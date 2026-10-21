"""
Baseline Suite — Phase 5.  Dataset-agnostic (driven by the dataset registry).

The research question this suite exists to answer is a PRIVACY question:
what does a fixed privacy budget cost, and how much of that cost is avoidable?
The arms are therefore chosen to decompose that cost, not merely to list prior
work:

  NON-PRIVATE REFERENCES  (establish the ceiling and the FL penalty)
    B0  Centralized        pooled data, no federation, no DP   → upper bound
    B1  Local Only         no federation at all                → lower bound
    B2  FedAvg             McMahan et al., 2017                → FL, no privacy
    B3  FedProx            Li et al., 2020                     → + heterogeneity
    B5  MOON               Li et al., 2021                     → + contrastive

  PRIVATE ARMS            (same eps, same data, same model — only the recipe moves)
    B4  DP-FedAvg          flat FL + DP-SGD on the WHOLE model, RANDOM init
                           (Geyer et al., 2017)
    B7  DP-FedAvg-Pre      flat FL + DP-SGD on the WHOLE model, PRETRAINED init
    B6  DP-FedAvg-Head     flat FL + DP-SGD on the FUSION HEAD only, PRETRAINED
                           init, encoders frozen

B6 is not from the literature; it exists to remove a confound. The proposed
system changes TWO things at once relative to B4 — it adds the edge tier AND it
restricts DP to the head over frozen encoders. Comparing only B4 against the
proposed model cannot say which change earned the result. With B6 in between:

    B4 -> B6    isolates the value of head-only DP  (recipe)
    B6 -> HFL   isolates the value of the edge tier (topology)

Every arm is trained and evaluated on the SAME partition files, so the dataset's
leakage controls (case-level for VitalDB, (subject,activity)-temporal for WEAR)
apply identically to baselines and to the proposed model.
"""

import os
import sys
import copy
import json
import argparse
import csv
from typing import Dict, List, Optional

# Allow running from any working directory. model/ is split into subfolders
# by concern (privacy/architecture/training/deploy/utils) — add them all so
# existing flat imports ("from device_utils import ...") keep resolving
# regardless of which subfolder a module lives in.
_MODEL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # model/
for _sub in ("privacy", "architecture", "training", "deploy", "utils"):
    sys.path.insert(0, os.path.join(_MODEL_ROOT, _sub))
sys.path.insert(0, os.path.join(os.path.dirname(_MODEL_ROOT), "data", "loaders"))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Subset, ConcatDataset
import numpy as np

from device_utils import get_device, optimize_gpu, get_dataloader_kwargs, set_seed
from datasets import get_spec, REGISTRY
# Reuse the trainer's metric code rather than reimplementing it: a baseline
# scored by a different function than the proposed model is not a comparison.
from hfl_trainer import _compute_metrics


# ─────────────────────────────────────────────────────────────────────
# Shared evaluation
# ─────────────────────────────────────────────────────────────────────

def evaluate(model: nn.Module, loader: DataLoader, device: torch.device,
             group_ids: Optional[np.ndarray] = None) -> Dict:
    """Accuracy + macro AUROC + AUPRC (+ case-level metrics when grouped)."""
    model.eval()
    logits, labels = [], []
    with torch.no_grad():
        for xa, xb, _tab, y in loader:
            logits.append(model(xa.to(device, non_blocking=True),
                                xb.to(device, non_blocking=True)).cpu())
            labels.append(y.cpu())
    probs = torch.softmax(torch.cat(logits), dim=-1).numpy()
    return _compute_metrics(torch.cat(labels).numpy(), probs, group_ids)


def _sel(metrics: Dict, key: str) -> float:
    """Model-selection scalar. NaN sorts below everything, never above."""
    v = metrics.get("auprc" if key == "auprc" else "macro_auc", float("nan"))
    return -np.inf if (v is None or np.isnan(v)) else float(v)


def weighted_fedavg(global_state: dict, client_states: List[dict],
                    client_sizes: List[int]) -> dict:
    """Federated Averaging: sample-count-weighted mean of client states."""
    total = sum(client_sizes)
    return {k: sum((n / total) * s[k].float()
                   for n, s in zip(client_sizes, client_states))
            for k in global_state}


def _trainable(model: nn.Module):
    """Optimiser must not receive frozen params — Opacus rejects them, and
    Adam would otherwise allocate state for tensors that never get a grad."""
    return [p for p in model.parameters() if p.requires_grad]


# ─────────────────────────────────────────────────────────────────────
# B0: Centralized
# ─────────────────────────────────────────────────────────────────────

def run_centralized(model_fn, loaders, n_classes, epochs=30, lr=1e-3,
                    device=None, output_path=None, class_weight=None,
                    select_on="auc", group_ids=None,
                    eval_every=0, val_cap=0, max_steps=0) -> dict:
    """
    B0: train on the pooled data of every device. Upper bound.

    Splits come from the POOLED PARTITION FILES, not from slicing the raw
    dataset by index range. The previous version used range(0, 0.7n) etc.,
    which ignored the partition files entirely — on VitalDB that scatters
    windows of one operation across train and test, and on WEAR it destroys
    the temporal boundary gap. Either way B0 reports an inflated ceiling that
    no federated arm can reach, for reasons that have nothing to do with
    federation. "Centralized" means pooled DATA, not abandoned SPLITS.
    """
    device = device or get_device(verbose=False)
    model = model_fn().to(device)
    opt = torch.optim.Adam(_trainable(model), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    loss_fn = nn.CrossEntropyLoss(
        weight=class_weight.to(device) if class_weight is not None else None)

    best, best_state = -np.inf, None

    # Intra-epoch validation. B0 pools EVERY device, so one epoch is one pass
    # over the whole corpus: a few hundred steps on vitaldb/wear, but ~41k on
    # eICU. There the model peaks early and then collapses to a constant
    # (val AUC exactly 0.5000), and a once-per-epoch checkpoint only ever sees
    # the collapsed model. All three knobs default to 0 = OFF, reproducing the
    # original per-epoch cadence exactly, so published baselines are unchanged.
    every    = max(0, int(eval_every or 0))
    v_cap    = max(0, int(val_cap or 0))
    max_step = max(0, int(max_steps or 0))

    # Frequent checks run on a capped val subset to stay affordable; the
    # epoch-boundary check always uses the FULL val split.
    va_quick = loaders["val"]
    if v_cap and len(va_quick.dataset) > v_cap:
        sub = np.sort(np.random.default_rng(0).choice(
            len(va_quick.dataset), v_cap, replace=False))
        va_quick = DataLoader(Subset(va_quick.dataset, sub.tolist()),
                              batch_size=va_quick.batch_size or 256,
                              shuffle=False, num_workers=0)

    def _check(tag, loader):
        nonlocal best, best_state
        m = evaluate(model, loader, device)
        if _sel(m, select_on) > best:
            best, best_state = _sel(m, select_on), copy.deepcopy(model.state_dict())
        print(f"[B0 Centralized] {tag} | "
              f"val AUC={m['macro_auc']:.4f} AUPRC={m['auprc']:.4f} "
              f"acc={m['accuracy']:.4f}", flush=True)
        model.train()

    step, stop = 0, False
    for ep in range(epochs):
        model.train()
        for xa, xb, _t, y in loaders["train"]:
            opt.zero_grad()
            loss_fn(model(xa.to(device, non_blocking=True),
                          xb.to(device, non_blocking=True)),
                    y.to(device, non_blocking=True)).backward()
            opt.step()
            step += 1
            if every and step % every == 0:
                _check(f"Epoch {ep+1}/{epochs} step {step}", va_quick)
            if max_step and step >= max_step:
                stop = True
                break
        sched.step()
        _check(f"Epoch {ep+1}/{epochs}", loaders["val"])
        if stop:
            print(f"[B0 Centralized] stop: max_steps={max_step} reached", flush=True)
            break

    if best_state is not None:
        model.load_state_dict(best_state)
    t = evaluate(model, loaders["test"], device, group_ids)
    r = {"baseline": "B0_Centralized", "epochs": epochs, **_pack(t)}
    print(f"[B0] {_fmt(r)}")
    if output_path:
        _save_csv(r, output_path)
    return r


# ─────────────────────────────────────────────────────────────────────
# B1: Local Only
# ─────────────────────────────────────────────────────────────────────

def run_local_only(model_fn, device_loaders, n_classes, epochs=20, lr=1e-3,
                   device=None, output_path=None, class_weight=None) -> dict:
    """B1: each device trains alone on its own shard. Lower bound.

    Scored per-device on that device's own test split — pooling would be
    meaningless here since there is no single model to pool onto."""
    device = device or get_device(verbose=False)
    aucs, aps, accs = [], [], []
    for i, dl in enumerate(device_loaders):
        model = model_fn().to(device)
        opt = torch.optim.Adam(_trainable(model), lr=lr)
        loss_fn = nn.CrossEntropyLoss(
            weight=class_weight.to(device) if class_weight is not None else None)
        for ep in range(epochs):
            model.train()
            for xa, xb, _t, y in dl["train"]:
                opt.zero_grad()
                loss_fn(model(xa.to(device, non_blocking=True),
                              xb.to(device, non_blocking=True)),
                        y.to(device, non_blocking=True)).backward()
                opt.step()
        m = evaluate(model, dl["test"], device)
        aucs.append(m["macro_auc"]); aps.append(m["auprc"]); accs.append(m["accuracy"])
        print(f"  [B1] device {i+1}/{len(device_loaders)} | "
              f"AUC={m['macro_auc']:.4f} AUPRC={m['auprc']:.4f}", flush=True)

    n_nan = int(np.sum(np.isnan(aucs)))
    if n_nan:
        print(f"[B1] {n_nan}/{len(aucs)} devices had a single-class test split "
              f"(AUC undefined) — excluded from the mean.")
    r = {"baseline": "B1_LocalOnly",
         "test_accuracy": float(np.nanmean(accs)),
         "test_macro_auc": float(np.nanmean(aucs)),
         "test_auprc": float(np.nanmean(aps)),
         "std_auc": float(np.nanstd(aucs)),
         "n_devices_undefined_auc": n_nan}
    print(f"[B1] {_fmt(r)} (±{r['std_auc']:.4f} across devices)")
    if output_path:
        _save_csv(r, output_path)
    return r


# ─────────────────────────────────────────────────────────────────────
# B2 / B3 / B5 — non-private federated arms
# ─────────────────────────────────────────────────────────────────────

def _fl_loop(name, model_fn, device_loaders, pooled, rounds, local_epochs, lr,
             device, class_weight, select_on, group_ids, local_step, on_round=None):
    """
    Shared FedAvg driver for the non-private arms.

    `local_step(local_model, global_state, dev_id, batch) -> loss` is the only
    thing that differs between FedAvg / FedProx / MOON, so the round structure,
    the aggregation, the per-round pooled-val model selection and the final
    scoring are guaranteed identical across the three. Selection on a pooled
    VAL split (never test) matches how the proposed model is chosen; taking the
    last round instead, as this file used to, penalises whichever arm happens
    to oscillate and is not a fair comparison.
    """
    global_model = model_fn().to(device)
    loss_fn = nn.CrossEntropyLoss(
        weight=class_weight.to(device) if class_weight is not None else None)
    best, best_state, history = -np.inf, None, []

    for r in range(rounds):
        global_state = copy.deepcopy(global_model.state_dict())
        states, sizes = [], []
        for dev_id, dl in enumerate(device_loaders):
            local = model_fn().to(device)
            local.load_state_dict(global_state)
            opt = torch.optim.Adam(_trainable(local), lr=lr)
            local.train()
            n = 0
            for _ in range(local_epochs):
                for batch in dl["train"]:
                    opt.zero_grad()
                    loss = local_step(local, global_model, global_state,
                                      dev_id, batch, loss_fn, device)
                    loss.backward()
                    opt.step()
                    n += len(batch[3])
            states.append(copy.deepcopy(local.state_dict())); sizes.append(n)
        global_model.load_state_dict(weighted_fedavg(global_state, states, sizes))
        if on_round:
            on_round(global_state)

        m = evaluate(global_model, pooled["val"], device)
        history.append(round(float(m["macro_auc"]), 4))
        if _sel(m, select_on) > best:
            best, best_state = _sel(m, select_on), copy.deepcopy(global_model.state_dict())
        print(f"  [{name}] round {r+1}/{rounds} | val AUC={m['macro_auc']:.4f} "
              f"AUPRC={m['auprc']:.4f}", flush=True)

    if best_state is not None:
        global_model.load_state_dict(best_state)
    return global_model, evaluate(global_model, pooled["test"], device, group_ids), history


def run_fedavg(model_fn, device_loaders, pooled, rounds=20, local_epochs=1,
               lr=1e-3, device=None, output_path=None, class_weight=None,
               select_on="auc", group_ids=None) -> dict:
    """B2: standard FedAvg — no DP, no hierarchy."""
    device = device or get_device(verbose=False)

    def step(local, _gm, _gs, _d, batch, loss_fn, dev):
        xa, xb, _t, y = batch
        return loss_fn(local(xa.to(dev, non_blocking=True),
                             xb.to(dev, non_blocking=True)), y.to(dev, non_blocking=True))

    _, t, hist = _fl_loop("B2 FedAvg", model_fn, device_loaders, pooled, rounds,
                          local_epochs, lr, device, class_weight, select_on,
                          group_ids, step)
    r = {"baseline": "B2_FedAvg", "rounds": rounds, **_pack(t), "val_auc_history": hist}
    print(f"[B2] {_fmt(r)}")
    if output_path:
        _save_csv(r, output_path)
    return r


def run_fedprox(model_fn, device_loaders, pooled, rounds=20, local_epochs=1,
                lr=1e-3, mu=0.01, device=None, output_path=None,
                class_weight=None, select_on="auc", group_ids=None) -> dict:
    """B3: FedProx — adds mu/2 * ||w - w_global||^2 to the local objective."""
    device = device or get_device(verbose=False)

    def step(local, _gm, gs, _d, batch, loss_fn, dev):
        xa, xb, _t, y = batch
        ce = loss_fn(local(xa.to(dev, non_blocking=True),
                           xb.to(dev, non_blocking=True)), y.to(dev, non_blocking=True))
        prox = sum(((p - gs[n].to(dev)) ** 2).sum()
                   for n, p in local.named_parameters()
                   if n in gs and p.requires_grad)
        return ce + (mu / 2.0) * prox

    _, t, hist = _fl_loop("B3 FedProx", model_fn, device_loaders, pooled, rounds,
                          local_epochs, lr, device, class_weight, select_on,
                          group_ids, step)
    r = {"baseline": "B3_FedProx", "rounds": rounds, "mu": mu, **_pack(t),
         "val_auc_history": hist}
    print(f"[B3] {_fmt(r)}")
    if output_path:
        _save_csv(r, output_path)
    return r


def run_moon(model_fn, device_loaders, pooled, rounds=20, local_epochs=1,
             lr=1e-3, mu=5.0, temperature=0.5, device=None, output_path=None,
             class_weight=None, select_on="auc", group_ids=None) -> dict:
    """B5: MOON — contrastive term pulls the local representation toward the
    global model and away from the client's previous one (Li et al., 2021)."""
    device = device or get_device(verbose=False)
    prev = [model_fn().to(device) for _ in device_loaders]

    def step(local, global_model, _gs, dev_id, batch, loss_fn, dev):
        xa, xb, _t, y = batch
        xa, xb, y = (xa.to(dev, non_blocking=True), xb.to(dev, non_blocking=True),
                     y.to(dev, non_blocking=True))
        ce = loss_fn(local(xa, xb), y)
        with torch.no_grad():
            ga, gb = global_model.encode(xa, xb)
            pa, pb = prev[dev_id].encode(xa, xb)
        ca, cb = local.encode(xa, xb)
        z, zg, zp = (torch.cat([ca, cb], -1), torch.cat([ga, gb], -1),
                     torch.cat([pa, pb], -1))
        s_g = F.cosine_similarity(z, zg, dim=-1) / temperature
        s_p = F.cosine_similarity(z, zp, dim=-1) / temperature
        # Numerically stable -log(e^a/(e^a+e^b)) = softplus(b-a).
        return ce + mu * F.softplus(s_p - s_g).mean()

    def after_round(global_state):
        for m in prev:
            m.load_state_dict(copy.deepcopy(global_state))

    _, t, hist = _fl_loop("B5 MOON", model_fn, device_loaders, pooled, rounds,
                          local_epochs, lr, device, class_weight, select_on,
                          group_ids, step, on_round=after_round)
    r = {"baseline": "B5_MOON", "rounds": rounds, "mu": mu,
         "temperature": temperature, **_pack(t), "val_auc_history": hist}
    print(f"[B5] {_fmt(r)}")
    if output_path:
        _save_csv(r, output_path)
    return r


# ─────────────────────────────────────────────────────────────────────
# B4 / B6 — private federated arms
# ─────────────────────────────────────────────────────────────────────

def run_dp_fedavg(model_fn, device_loaders, pooled, rounds=20, local_epochs=1,
                  lr=1e-3, epsilon=1.0, delta=1e-5, max_grad_norm=1.0,
                  device=None, output_path=None, class_weight=None,
                  select_on="auc", group_ids=None, head_only=False,
                  max_physical_batch_size: int = 0,
                  label="B4_DP_FedAvg") -> dict:
    """
    Flat FL + DP-SGD. `head_only` switches between the two private arms:

      head_only=False -> B4, DP-SGD over the whole model (Geyer et al., 2017)
      head_only=True  -> B6, encoders pretrained + frozen, DP-SGD on the head

    Both consume the SAME (epsilon, delta) and the same number of rounds, so
    any difference between them is attributable to the recipe and not to the
    budget. Note that sigma is IDENTICAL for the two arms — it depends on
    eps/steps/sampling-rate, never on parameter count. Freezing does not buy a
    smaller noise scale; it changes the optimisation geometry so that the same
    noise scale is survivable. That distinction is the whole claim, so the code
    must not be read as though freezing reduced the noise.

    One sigma is precomputed for the entire budget and ONE persistent
    PrivacyEngine per device is reused across rounds. Calling target_epsilon
    afresh each round would silently drop cross-round composition and report a
    budget far smaller than the one actually spent.
    """
    device = device or get_device(verbose=False)
    from dp_engine import (make_dp_model, get_epsilon_spent,
                           compute_fl_noise_multiplier_multidevice,
                           new_device_privacy_engines)

    global_model = model_fn().to(device)
    n_trainable = sum(p.numel() for p in _trainable(global_model))
    n_total = sum(p.numel() for p in global_model.parameters())
    min_n = min(len(dl["train"].dataset) for dl in device_loaders)
    bs = device_loaders[0]["train"].batch_size
    # Calibrate against EVERY client. Using the smallest client as a stand-in,
    # with floor(n/B) for the step count, under-provisioned noise and made every
    # sweep point breach its own budget: 0.5->0.511, 1->1.018, 2->2.044,
    # 4->4.082, 8->8.163. A privacy result that exceeds the epsilon it claims is
    # not a weaker result, it is an invalid one.
    _dev_n = [len(dl["train"].dataset) for dl in device_loaders]
    sigma = compute_fl_noise_multiplier_multidevice(
        target_epsilon=epsilon, target_delta=delta, n_fl_calls=rounds,
        device_n_train=_dev_n, batch_size=bs, local_epochs=local_epochs)
    print(f"  [{label}] sigma={sigma:.4f} | DP-trained params "
          f"{n_trainable:,}/{n_total:,} ({100*n_trainable/n_total:.1f}%)")

    engines = new_device_privacy_engines(len(device_loaders))
    loss_fn = nn.CrossEntropyLoss(
        weight=class_weight.to(device) if class_weight is not None else None)
    eps_spent, best, best_state, history = 0.0, -np.inf, None, []

    for r in range(rounds):
        global_state = copy.deepcopy(global_model.state_dict())
        states, sizes = [], []
        for dev_id, dl in enumerate(device_loaders):
            local = model_fn().to(device)
            local.load_state_dict(global_state)
            # requires_grad is not part of state_dict, so a load can leave the
            # freeze intact but a rebuild+load must be re-checked explicitly.
            if head_only:
                from hfl_mm_model import freeze_encoders
                freeze_encoders(local)
            opt = torch.optim.Adam(_trainable(local), lr=lr)
            dp_model, dp_opt, dp_loader, pe = make_dp_model(
                local, opt, dl["train"], noise_multiplier=sigma,
                max_grad_norm=max_grad_norm, privacy_engine=engines[dev_id])
            dp_model.train()
            n = 0

            # Opacus materialises a PER-SAMPLE gradient for every trainable
            # parameter, so peak memory is batch_size x n_params x 4 bytes. On
            # the full-model arm that is ~1 GB per tensor set at batch 64 and
            # the run dies with a CUDA OOM inside capture_backprops_hook.
            #
            # BatchMemoryManager splits the batch PHYSICALLY while keeping the
            # LOGICAL batch — and therefore the sampling rate and the privacy
            # accounting — unchanged. Simply lowering batch_size would also fix
            # the memory but would silently change the guarantee being measured.
            from contextlib import nullcontext
            try:
                from opacus.utils.batch_memory_manager import BatchMemoryManager
                if max_physical_batch_size and max_physical_batch_size > 0:
                    _ctx = BatchMemoryManager(
                        data_loader=dp_loader,
                        max_physical_batch_size=max_physical_batch_size,
                        optimizer=dp_opt)
                else:
                    _ctx = nullcontext(dp_loader)
            except Exception:
                _ctx = nullcontext(dp_loader)

            with _ctx as _loader:
                for _ in range(local_epochs):
                    for xa, xb, _t, y in _loader:
                        if len(y) == 0:
                            continue          # Poisson sampling can yield empty
                        dp_opt.zero_grad()
                        loss_fn(dp_model(xa.to(device, non_blocking=True),
                                         xb.to(device, non_blocking=True)),
                                y.to(device, non_blocking=True)).backward()
                        dp_opt.step()
                        n += len(y)
            eps_spent = max(eps_spent, get_epsilon_spent(pe, delta))
            states.append(copy.deepcopy(local.state_dict())); sizes.append(n)

        global_model.load_state_dict(weighted_fedavg(global_state, states, sizes))
        m = evaluate(global_model, pooled["val"], device)
        history.append(round(float(m["macro_auc"]), 4))
        if _sel(m, select_on) > best:
            best, best_state = _sel(m, select_on), copy.deepcopy(global_model.state_dict())
        print(f"  [{label}] round {r+1}/{rounds} | val AUC={m['macro_auc']:.4f} "
              f"AUPRC={m['auprc']:.4f} | eps={eps_spent:.4f}", flush=True)

        if eps_spent >= epsilon:
            print(f"  [{label}] privacy budget exhausted at round {r+1}. Stopping.")
            break

    if best_state is not None:
        global_model.load_state_dict(best_state)
    t = evaluate(global_model, pooled["test"], device, group_ids)
    r_out = {"baseline": label, "rounds": rounds, "epsilon_target": epsilon,
             "epsilon_spent": eps_spent, "delta": delta, "sigma": sigma,
             "head_only": head_only, "dp_trained_params": n_trainable,
             "total_params": n_total, **_pack(t), "val_auc_history": history}
    print(f"[{label}] {_fmt(r_out)} | eps_spent={eps_spent:.4f}")
    if output_path:
        _save_csv(r_out, output_path)
    return r_out


# ─────────────────────────────────────────────────────────────────────
# Reporting helpers
# ─────────────────────────────────────────────────────────────────────

def _pack(m: Dict) -> Dict:
    """Flatten an evaluate() dict into CSV columns with a test_ prefix."""
    out = {"test_accuracy": m.get("accuracy"),
           "test_macro_auc": m.get("macro_auc"),
           "test_auprc": m.get("auprc")}
    for k in ("case_accuracy", "case_auc", "case_auprc", "n_groups"):
        if k in m:
            out[f"test_{k}"] = m[k]
    return out


def _fmt(r: Dict) -> str:
    s = (f"AUC={r.get('test_macro_auc', float('nan')):.4f} "
         f"AUPRC={r.get('test_auprc', float('nan')):.4f} "
         f"acc={r.get('test_accuracy', float('nan')):.4f}")
    if "test_case_auc" in r:
        s += (f" | case AUC={r['test_case_auc']:.4f} "
              f"AUPRC={r['test_case_auprc']:.4f}")
    return s


def _save_csv(result: dict, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    ser = {k: json.dumps(v) if isinstance(v, (list, dict)) else v
           for k, v in result.items()}
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ser.keys()))
        w.writeheader()
        w.writerow(ser)
    print(f"Saved: {path}")


# ─────────────────────────────────────────────────────────────────────
# Data assembly
# ─────────────────────────────────────────────────────────────────────

def build_loaders(spec, batch_size: int, device):
    """Per-device train/val/test loaders + pooled val/test, all from the
    dataset's own partition files."""
    full_ds = spec.build_full(spec.data_dir)
    with open(os.path.join(spec.partition_dir, "partition_meta.json")) as f:
        meta = json.load(f)
    n_dev = meta["n_devices"]
    dl_kw = get_dataloader_kwargs(device)

    device_loaders, pools = [], {"train": [], "val": [], "test": []}
    for d in range(n_dev):
        per = {}
        for split in ("train", "val", "test"):
            idx = np.load(os.path.join(spec.partition_dir,
                                       f"device_{d:02d}_{split}.npy"))
            sub = Subset(full_ds, idx.tolist())
            pools[split].append((sub, idx))
            per[split] = DataLoader(
                sub, batch_size=batch_size if split == "train" else batch_size * 2,
                shuffle=(split == "train"), **dl_kw)
        device_loaders.append(per)

    pooled, order = {}, {}
    for split in ("train", "val", "test"):
        subs = [s for s, _ in pools[split]]
        pooled[split] = DataLoader(
            ConcatDataset(subs),
            batch_size=batch_size if split == "train" else batch_size * 2,
            shuffle=(split == "train"), **dl_kw)
        order[split] = np.concatenate([i for _, i in pools[split]])

    # Case ids let VitalDB be scored per OPERATION, not per 10-minute window.
    gpath = os.path.join(spec.data_dir, "meta", "case_ids.npy")
    group_test = np.load(gpath)[order["test"]] if os.path.exists(gpath) else None
    return full_ds, n_dev, device_loaders, pooled, order, group_test


def compute_class_weight(full_ds, train_idx, n_classes) -> torch.Tensor:
    """n / (K * count_k) — the same rule the trainer uses, so a baseline is
    never handed a different class prior than the proposed model."""
    y = np.array([int(full_ds[int(i)][3]) for i in train_idx])
    cnt = np.bincount(y, minlength=n_classes).astype(np.float64)
    return torch.tensor(len(y) / (n_classes * np.maximum(cnt, 1)),
                        dtype=torch.float32)


# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _sim_dir = os.path.dirname(_MODEL_ROOT)                    # SIMULATORS/

    p = argparse.ArgumentParser(description="FL baselines B0–B6",
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", required=True,
                   choices=sorted(REGISTRY))
    p.add_argument("--data_dir", default=None, help="override registry path")
    p.add_argument("--partition_dir", default=None, help="override registry path")
    p.add_argument("--output_dir", default=None,
                   help="default: results/phase5/baselines/<dataset>")
    p.add_argument("--b0_epochs", type=int, default=5)
    p.add_argument("--b1_epochs", type=int, default=10)
    p.add_argument("--rounds", type=int, default=10)
    p.add_argument("--local_epochs", type=int, default=1)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--epsilon", type=float, default=1.0)
    p.add_argument("--delta", type=float, default=1e-5)
    p.add_argument("--max_grad_norm", type=float, default=1.0)
    p.add_argument("--max_physical_batch_size", type=int, default=0,
                   help="Physical micro-batch for the DP arms; 0 = no splitting. "
                        "The LOGICAL batch (and thus the privacy accounting) is "
                        "unchanged either way — this only bounds per-sample-gradient "
                        "memory. Set it ONLY when a run actually OOMs: splitting 64 "
                        "into micro-batches of 8 measured 425 s/round against "
                        "77 s/round unsplit.")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--class_weight", choices=["none", "balanced", "auto"],
                   default="auto",
                   help="auto = balanced for binary tasks, none otherwise")
    p.add_argument("--eval_every", type=int, default=0,
                   help="B0: validate every N optimiser steps (0 = only at "
                        "epoch end, the original behaviour). Needed where one "
                        "pooled epoch is long enough to hide the model's peak.")
    p.add_argument("--val_cap", type=int, default=0,
                   help="B0: cap the val split used by intra-epoch checks "
                        "(0 = full). Epoch-boundary checks always use full val.")
    p.add_argument("--max_steps", type=int, default=0,
                   help="B0: stop after N optimiser steps (0 = unlimited).")
    p.add_argument("--select_on", choices=["auc", "auprc"], default="auto",
                   nargs="?", const="auto",
                   help="auto = auprc for binary tasks, auc otherwise")
    p.add_argument("--pretrained_encoders", default=None,
                   help="checkpoint for B6's frozen encoders (required for B6)")
    p.add_argument("--only", nargs="*", default=[],
                   help="run only these, e.g. --only b4 b6")
    p.add_argument("--skip", nargs="*", default=[])
    args = p.parse_args()

    spec = get_spec(args.dataset)
    # DatasetSpec is frozen; overrides must produce a new spec or build_loaders
    # would keep reading the registry paths and silently ignore the flags.
    if args.data_dir or args.partition_dir:
        import dataclasses
        spec = dataclasses.replace(
            spec,
            data_dir=args.data_dir or spec.data_dir,
            partition_dir=args.partition_dir or spec.partition_dir)
    out_dir = args.output_dir or os.path.join(_sim_dir, "results", "phase5",
                                              "baselines", args.dataset)
    os.makedirs(out_dir, exist_ok=True)

    if args.select_on == "auto":
        args.select_on = "auprc" if spec.n_classes == 2 else "auc"
    use_cw = (args.class_weight == "balanced" or
              (args.class_weight == "auto" and spec.n_classes == 2))

    set_seed(args.seed)
    _device = get_device()
    optimize_gpu()
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)

    print("=" * 70)
    print(f"BASELINE SUITE — {args.dataset.upper()}")
    print("=" * 70)
    print(spec)
    print(f"  pairing      : {spec.pairing}")
    print(f"  select_on    : {args.select_on}   class_weight: {use_cw}")
    print(f"  output       : {out_dir}")

    full_ds, n_dev, device_loaders, pooled, order, group_test = build_loaders(
        spec, args.batch_size, _device)
    print(f"  samples      : train={len(order['train']):,} "
          f"val={len(order['val']):,} test={len(order['test']):,} "
          f"across {n_dev} devices")
    if group_test is not None:
        print(f"  case-level   : {len(np.unique(group_test))} cases in test")

    cw = compute_class_weight(full_ds, order["train"], spec.n_classes) if use_cw else None
    if cw is not None:
        print(f"  class weights: {[round(float(x), 3) for x in cw]}")

    from hfl_mm_model import build_hfl_mm_hc, freeze_encoders, load_pretrained_encoders

    _kw = {"n_channels_a": spec.n_channels_a}
    if spec.modality_b != "image":
        _kw.update(modality_b="features", feat_b_dim=spec.feat_b_dim)

    def model_fn():
        return build_hfl_mm_hc(n_classes=spec.n_classes, **_kw)

    def pretrained_full_model_fn():
        """B7: same starting weights as B6, but NOTHING is frozen — DP-SGD is
        applied to the whole network. This is the arm that separates 'the
        encoders were already good' from 'training only the head is what
        survives the noise'."""
        m = build_hfl_mm_hc(n_classes=spec.n_classes, **_kw)
        if args.pretrained_encoders:
            load_pretrained_encoders(m, args.pretrained_encoders)
        return m                      # deliberately NOT frozen

    def head_only_model_fn():
        m = build_hfl_mm_hc(n_classes=spec.n_classes, **_kw)
        if args.pretrained_encoders:
            load_pretrained_encoders(m, args.pretrained_encoders)
        return freeze_encoders(m)

    _only = [s.lower() for s in args.only]
    _skip = [s.lower() for s in args.skip]

    def want(b):
        return (not _only or b in _only) and b not in _skip

    results = []
    common = dict(device=_device, class_weight=cw, select_on=args.select_on,
                  group_ids=group_test)

    if want("b0"):
        print("\n" + "=" * 70 + f"\nB0 CENTRALIZED | epochs={args.b0_epochs}\n" + "=" * 70)
        results.append(run_centralized(
            model_fn, pooled, spec.n_classes, epochs=args.b0_epochs, lr=args.lr,
            output_path=os.path.join(out_dir, "baseline_b0.csv"),
            eval_every=args.eval_every, val_cap=args.val_cap,
            max_steps=args.max_steps, **common))

    if want("b1"):
        print("\n" + "=" * 70 + f"\nB1 LOCAL ONLY | epochs={args.b1_epochs}\n" + "=" * 70)
        results.append(run_local_only(
            model_fn, device_loaders, spec.n_classes, epochs=args.b1_epochs,
            lr=args.lr, device=_device, class_weight=cw,
            output_path=os.path.join(out_dir, "baseline_b1.csv")))

    if want("b2"):
        print("\n" + "=" * 70 + f"\nB2 FEDAVG | rounds={args.rounds}\n" + "=" * 70)
        results.append(run_fedavg(
            model_fn, device_loaders, pooled, rounds=args.rounds,
            local_epochs=args.local_epochs, lr=args.lr,
            output_path=os.path.join(out_dir, "baseline_b2.csv"), **common))

    if want("b3"):
        print("\n" + "=" * 70 + f"\nB3 FEDPROX | rounds={args.rounds}\n" + "=" * 70)
        results.append(run_fedprox(
            model_fn, device_loaders, pooled, rounds=args.rounds,
            local_epochs=args.local_epochs, lr=args.lr,
            output_path=os.path.join(out_dir, "baseline_b3.csv"), **common))

    if want("b4"):
        print("\n" + "=" * 70 +
              f"\nB4 DP-FEDAVG (full model) | rounds={args.rounds} eps={args.epsilon}\n"
              + "=" * 70)
        results.append(run_dp_fedavg(
            model_fn, device_loaders, pooled, rounds=args.rounds,
            local_epochs=args.local_epochs, lr=args.lr, epsilon=args.epsilon,
            delta=args.delta, max_grad_norm=args.max_grad_norm, head_only=False,
            label="B4_DP_FedAvg",
            max_physical_batch_size=args.max_physical_batch_size,
            output_path=os.path.join(out_dir, "baseline_b4.csv"), **common))

    if want("b7"):
        if not args.pretrained_encoders:
            print("\n[B7 SKIPPED] --pretrained_encoders is required: the arm is "
                  "'PRETRAINED encoders + full-model DP'. Without the checkpoint "
                  "it would be identical to B4 and would isolate nothing.")
        else:
            print("\n" + "=" * 70 +
                  f"\nB7 DP-FEDAVG (pretrained init, FULL model) | rounds={args.rounds} "
                  f"eps={args.epsilon}\n" + "=" * 70)
            results.append(run_dp_fedavg(
                pretrained_full_model_fn, device_loaders, pooled, rounds=args.rounds,
                local_epochs=args.local_epochs, lr=args.lr, epsilon=args.epsilon,
                delta=args.delta, max_grad_norm=args.max_grad_norm, head_only=False,
                label="B7_DP_FedAvg_Pretrained",
                max_physical_batch_size=args.max_physical_batch_size,
                output_path=os.path.join(out_dir, "baseline_b7.csv"), **common))

    if want("b5"):
        print("\n" + "=" * 70 + f"\nB5 MOON | rounds={args.rounds}\n" + "=" * 70)
        results.append(run_moon(
            model_fn, device_loaders, pooled, rounds=args.rounds,
            local_epochs=args.local_epochs, lr=args.lr,
            output_path=os.path.join(out_dir, "baseline_b5.csv"), **common))

    if want("b6"):
        if not args.pretrained_encoders:
            # Without pretrained encoders B6 DP-trains a head over RANDOM
            # features — that measures nothing, and would understate the very
            # recipe the thesis proposes. Refuse rather than emit a number.
            print("\n[B6 SKIPPED] --pretrained_encoders is required: the arm is "
                  "'frozen PRETRAINED encoders + DP head', and freezing random "
                  "encoders would report a meaningless floor.")
        else:
            print("\n" + "=" * 70 +
                  f"\nB6 DP-FEDAVG (head only) | rounds={args.rounds} eps={args.epsilon}\n"
                  + "=" * 70)
            results.append(run_dp_fedavg(
                head_only_model_fn, device_loaders, pooled, rounds=args.rounds,
                local_epochs=args.local_epochs, lr=args.lr, epsilon=args.epsilon,
                delta=args.delta, max_grad_norm=args.max_grad_norm, head_only=True,
                label="B6_DP_FedAvg_HeadOnly",
            max_physical_batch_size=args.max_physical_batch_size,
                output_path=os.path.join(out_dir, "baseline_b6.csv"), **common))

    # ── summary ──────────────────────────────────────────────────────
    fields = ["baseline", "test_accuracy", "test_macro_auc", "test_auprc",
              "test_case_auc", "test_case_auprc", "epsilon_target", "epsilon_spent"]
    spath = os.path.join(out_dir, "baselines_summary.csv")
    with open(spath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow({k: r.get(k, "") for k in fields})

    print("\n" + "=" * 70)
    print(f"BASELINE SUMMARY — {args.dataset}")
    print("=" * 70)
    hdr = f"{'Baseline':<26}{'Acc':>8}{'AUROC':>9}{'AUPRC':>9}"
    if group_test is not None:
        hdr += f"{'caseAUC':>10}{'caseAP':>9}"
    hdr += f"{'eps':>8}"
    print(hdr)
    print("-" * len(hdr))
    for r in results:
        def g(k):
            v = r.get(k)
            return f"{v:.4f}" if isinstance(v, float) and not np.isnan(v) else "   —"
        line = (f"{r.get('baseline', '?'):<26}{g('test_accuracy'):>8}"
                f"{g('test_macro_auc'):>9}{g('test_auprc'):>9}")
        if group_test is not None:
            line += f"{g('test_case_auc'):>10}{g('test_case_auprc'):>9}"
        e = r.get("epsilon_spent")
        line += f"{f'{e:.3f}' if isinstance(e, float) else '   —':>8}"
        print(line)
    print("=" * 70)
    print(f"\nSummary CSV: {spath}")
    def _find(pfx):
        return next((r for r in results if r.get("baseline", "").startswith(pfx)), None)

    b4, b6, b7, b2 = _find("B4"), _find("B6"), _find("B7"), _find("B2")
    if b4 and b6:
        print(f"\nDECOMPOSITION at eps={args.epsilon} (AUROC):")
        print(f"  B4 full-model DP, random init      {b4['test_macro_auc']:.4f}")
        if b7:
            print(f"  B7 full-model DP, pretrained init  {b7['test_macro_auc']:.4f}"
                  f"   ({b7['test_macro_auc']-b4['test_macro_auc']:+.4f} = value of PRETRAINING)")
        print(f"  B6 head-only DP, pretrained init   {b6['test_macro_auc']:.4f}"
              + (f"   ({b6['test_macro_auc']-b7['test_macro_auc']:+.4f} = value of HEAD-ONLY)"
                 if b7 else "   (B7 absent: recipe NOT separable from pretraining)"))
        if not b7:
            print("\n  WARNING: without B7 the B4->B6 gap conflates two changes "
                  "and must NOT be reported as the value of head-only DP.")
        if b2 and b6 and b6["test_macro_auc"] > b2["test_macro_auc"]:
            print(f"\n  NOTE: B6 ({b6['test_macro_auc']:.4f}) exceeds the NON-PRIVATE "
                  f"B2 ({b2['test_macro_auc']:.4f}). A private arm beating its own "
                  f"non-private counterpart indicates the pretrained encoders carry "
                  f"an advantage B2 never received — and, in PROXY mode, that they "
                  f"saw the training data non-privately. Interpret accordingly.")
