"""
HFL-MM-HC Training Engine — Phase 5
Two-tier FedAvg: clinical IoT devices -> Edge servers -> 1 Cloud server
With DP-SGD (Opacus), gradient compression (Top-k + 8-bit), and
FedConform-HC conformal calibration updates.
"""

import os
import sys
import copy
import json
import time
import argparse
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, Subset

_MODEL_ROOT = Path(__file__).parent.parent   # model/ — now split into subfolders
                                              # by concern (privacy/architecture/
                                              # training/deploy/utils); add them
                                              # all so existing flat imports
                                              # ("from dp_engine import ...")
                                              # keep resolving regardless of
                                              # which subfolder a module lives in.
for _sub in ("privacy", "architecture", "training", "deploy", "utils"):
    sys.path.insert(0, str(_MODEL_ROOT / _sub))
sys.path.insert(0, str(_MODEL_ROOT.parent / "data" / "loaders"))

# Module scope: the argparse --dataset choices resolve from the registry, so
# REGISTRY must be importable here and not only inside a function.
from datasets import REGISTRY                                   # noqa: E402

from device_utils import (get_device, optimize_gpu, get_dataloader_kwargs,
                          gpu_memory_info, set_seed)


def _model_kw(args) -> dict:
    """Modality-B kwargs for HFLMMHC, resolved from the dataset registry."""
    from datasets import get_spec
    sp = get_spec(getattr(args, "dataset", "vitaldb"))
    kw = {"n_channels_a": sp.n_channels_a}
    if sp.modality_b != "image":
        kw.update({"modality_b": "features", "feat_b_dim": sp.feat_b_dim})
    return kw


def load_partitioned_data(partition_dir: str, processed_dir: str,
                          device_id: int, batch_size: int = 32,
                          full_ds=None):
    """
    Load train/val/test loaders for a specific device.

    `full_ds` is REQUIRED: it is built once by the caller and shared across
    every device via Subset. Building one full dataset per device would
    multiply resident memory by n_devices. It has no default because the only
    default that ever existed built the removed `healthcare` dataset, and a
    silent fallback to the wrong dataset is worse than an explicit failure.
    """
    if full_ds is None:
        raise ValueError(
            "load_partitioned_data requires full_ds. Build it once with "
            "spec.build_full(<data_dir>) from the dataset registry and pass "
            "the same object for every device.")

    train_idx = np.load(os.path.join(partition_dir,
                                     f"device_{device_id:02d}_train.npy"))
    val_idx = np.load(os.path.join(partition_dir,
                                   f"device_{device_id:02d}_val.npy"))
    test_idx = np.load(os.path.join(partition_dir,
                                    f"device_{device_id:02d}_test.npy"))

    train_ds = Subset(full_ds, train_idx.tolist())
    val_ds = Subset(full_ds, val_idx.tolist())
    test_ds = Subset(full_ds, test_idx.tolist())

    _device  = get_device(verbose=False)
    _dl_kw   = get_dataloader_kwargs(_device)
    return {
        "train": DataLoader(train_ds, batch_size=batch_size,
                            shuffle=True, **_dl_kw),
        "val":   DataLoader(val_ds,   batch_size=batch_size * 2, **_dl_kw),
        "test":  DataLoader(test_ds,  batch_size=batch_size * 2, **_dl_kw),
        "n_train": len(train_idx),
    }


def build_pooled_loader(partition_dir: str, n_devices: int, full_ds,
                        split: str = "test", batch_size: int = 32):
    """
    Concatenate every device's local split into one loader (`split` selects
    train/val/test), returning the loader and its index order.

    A single device's split is too small
    and too class-skewed to report as the headline "final test" number —
    e.g. device 0 has only 7 class-0 samples in its test split, so a handful
    of misclassifications swing accuracy by several percentage points. Pooling
    across all devices gives a much larger, less noisy, less skewed estimate
    of true held-out performance without touching training at all.
    """
    from torch.utils.data import ConcatDataset

    test_subsets, order = [], []
    for dev_id in range(n_devices):
        test_idx = np.load(os.path.join(partition_dir,
                                        f"device_{dev_id:02d}_{split}.npy"))
        test_subsets.append(Subset(full_ds, test_idx.tolist()))
        order.append(test_idx)

    _device = get_device(verbose=False)
    _dl_kw = get_dataloader_kwargs(_device)
    # Also return the concatenated index order so callers can align an
    # external per-sample array (e.g. VitalDB case ids) to the loader.
    # ConcatDataset preserves order, and the loader is NOT shuffled.
    return (DataLoader(ConcatDataset(test_subsets), batch_size=batch_size * 2,
                       **_dl_kw),
            np.concatenate(order))


def _compute_metrics(labels: np.ndarray, probs: np.ndarray,
                     group_ids: np.ndarray = None, prefix: str = "") -> Dict:
    """
    Accuracy + macro AUROC + AUPRC, and — when `group_ids` is supplied — the
    same metrics aggregated to the GROUP level.

    Why AUPRC: on a 19.7 %-positive task like VitalDB, accuracy is nearly
    uninformative (80 % comes free from always predicting "no ICU") and AUROC
    is optimistic under class imbalance. Average precision is the metric that
    actually moves when the minority class is handled well.

    Why group aggregation: VitalDB scores 10-minute WINDOWS, but the clinical
    question is per OPERATION. Windows from one case are highly correlated, so
    window-level metrics overstate effective sample size. Averaging each case's
    window probabilities gives one prediction per case, which is both the
    clinically meaningful unit and the statistically honest one.
    """
    from sklearn.metrics import roc_auc_score, average_precision_score

    n_cls = probs.shape[1]
    preds = probs.argmax(1)
    out = {f"{prefix}accuracy": float((preds == labels).mean())}

    def _auc_ap(y, p):
        try:
            if n_cls == 2:
                # Binary: sklearn needs a 1-D score for the POSITIVE class.
                # Passing the full (N,2) matrix raises "y should be a 1d array".
                return (float(roc_auc_score(y, p[:, 1])),
                        float(average_precision_score(y, p[:, 1])))
            return (float(roc_auc_score(y, p, multi_class="ovr",
                                        average="macro",
                                        labels=list(range(n_cls)))),
                    float(average_precision_score(
                        np.eye(n_cls)[y], p, average="macro")))
        except Exception as e:
            print(f"[METRIC ERROR] {e} | classes present: {np.unique(y)}")
            return float("nan"), float("nan")

    out[f"{prefix}macro_auc"], out[f"{prefix}auprc"] = _auc_ap(labels, probs)

    if group_ids is not None and len(group_ids) == len(labels):
        gs = np.unique(group_ids)
        gp = np.stack([probs[group_ids == g].mean(0) for g in gs])
        gy = np.array([labels[group_ids == g][0] for g in gs])
        # A group must not carry conflicting labels, or the aggregation is
        # meaningless — every window of a case shares that case's outcome.
        assert all(len(np.unique(labels[group_ids == g])) == 1 for g in gs), \
            "group label conflict — a case spans more than one label"
        out[f"{prefix}n_groups"] = int(len(gs))
        out[f"{prefix}case_accuracy"] = float((gp.argmax(1) == gy).mean())
        out[f"{prefix}case_auc"], out[f"{prefix}case_auprc"] = _auc_ap(gy, gp)
    return out


_ACTIVE_DATASET = [None]


def _metric_group_rel(dataset=None):
    """Relative path of the array that groups predictions for CASE-LEVEL
    metrics. Resolved from the registry so nothing is hardcoded per corpus.

    This is NOT the DP unit and NOT the split key — both remain the individual
    (case_ids). It is only the unit over which per-group predictions are
    averaged, which requires a single-valued label per group.
    """
    try:
        from datasets import get_spec
        name = dataset if dataset is not None else _ACTIVE_DATASET[0]
        if name:
            return get_spec(name).metric_group_file
    except Exception:
        pass
    return "meta/case_ids.npy"


def evaluate_model(model: nn.Module, loader: DataLoader,
                   device: torch.device, group_ids: np.ndarray = None) -> Dict:
    from sklearn.metrics import roc_auc_score
    model.eval()
    all_logits, all_labels = [], []
    with torch.no_grad():
        for ecg, cxr, _tab, labels in loader:
            logits = model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True))
            all_logits.append(logits.cpu())
            all_labels.append(labels.cpu())
    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels).numpy()
    probs = torch.softmax(logits, dim=-1).numpy()
    return _compute_metrics(labels, probs, group_ids)


def _predict(model: nn.Module, loader: DataLoader, device: torch.device):
    model.eval()
    P, Y = [], []
    with torch.no_grad():
        for ecg, cxr, _tab, labels in loader:
            P.append(torch.softmax(model(ecg.to(device), cxr.to(device)), -1).cpu())
            Y.append(labels.cpu())
    return torch.cat(P).numpy(), torch.cat(Y).numpy()


def _threshold_metrics(model, args, n_devices, full_ds, device) -> Dict:
    """Accuracy at a threshold chosen on the VALIDATION cohort (Youden's J),
    reported on test. Under strong DP the positive-class probabilities shrink
    toward the prior, so the fixed 0.5 cut makes every prediction negative and
    test accuracy equals the majority rate on every seed. The val cohort is
    already used non-privately for checkpoint selection; picking the cut there
    adds no new disclosure. Binary tasks only."""
    try:
        vl, _ = build_pooled_loader(args.partition_dir, n_devices, full_ds,
                                    "val", args.batch_size)
        tl, _ = build_pooled_loader(args.partition_dir, n_devices, full_ds,
                                    "test", args.batch_size)
        pv, yv = _predict(model, vl, device)
        pt, yt = _predict(model, tl, device)
        if pv.shape[1] != 2:
            return {}
        from sklearn.metrics import roc_curve
        fpr, tpr, thr = roc_curve(yv, pv[:, 1])
        t = float(thr[int(np.argmax(tpr - fpr))])
        yh = (pt[:, 1] >= t).astype(int)
        sens = float((yh[yt == 1] == 1).mean()) if (yt == 1).any() else float("nan")
        spec = float((yh[yt == 0] == 0).mean()) if (yt == 0).any() else float("nan")
        return {"val_threshold": t, "accuracy_valthr": float((yh == yt).mean()),
                "balanced_accuracy_valthr": 0.5 * (sens + spec),
                "sensitivity_valthr": sens, "specificity_valthr": spec}
    except Exception as e:                       # never lose the run over this
        print(f"[test][WARN] threshold metrics skipped: {e}")
        return {}


def evaluate_personalized(backbone: nn.Module, adapter: nn.Module, loader: DataLoader,
                          device: torch.device) -> Dict:
    """Same as evaluate_model, but passes the shared backbone's logits through
    a per-edge pFAL adapter (see hfl_mm_model.PersonalizationAdapter) first."""
    from sklearn.metrics import roc_auc_score
    backbone.eval()
    adapter.eval()
    all_logits, all_labels = [], []
    with torch.no_grad():
        for ecg, cxr, _tab, labels in loader:
            shared_logits = backbone(ecg.to(device, non_blocking=True),
                                     cxr.to(device, non_blocking=True))
            logits = adapter(shared_logits)
            all_logits.append(logits.cpu())
            all_labels.append(labels.cpu())
    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels).numpy()
    probs = torch.softmax(logits, dim=-1).numpy()
    preds = logits.argmax(dim=-1).numpy()
    acc = float((preds == labels).mean())
    try:
        auc = float(roc_auc_score(labels, probs, multi_class="ovr", average="macro",
                                  labels=list(range(probs.shape[1]))))
    except Exception as e:
        print(f"[AUC ERROR] {e}")
        auc = 0.0
    return {"accuracy": acc, "macro_auc": auc}


def local_dp_train(model: nn.Module, loader: DataLoader,
                   device: torch.device, delta: float,
                   max_grad_norm: float, lr: float,
                   noise_multiplier: Optional[float],
                   n_epochs: int = 1,
                   privacy_engine=None,
                   dp_mode: str = "uniform",
                   group_of: Optional[Dict[str, int]] = None,
                   group_sigmas: Optional[List[float]] = None,
                   class_weight: Optional[torch.Tensor] = None,
                   no_dp: bool = False) -> Dict:
    """
    DP-SGD local training for one FL round.

    noise_multiplier must be pre-computed once via compute_fl_noise_multiplier()
    for the full training budget (global_rounds × edge_rounds × local_epochs).
    Using the same fixed σ each round is what makes the end-to-end privacy
    accounting valid. Under dp_mode="sadp", pass group_sigmas (from
    sadp_engine.compute_sadp_group_sigmas) instead — noise_multiplier is
    ignored in that branch.

    privacy_engine: pass the SAME tracking object across every call for a
    given device (an Opacus PrivacyEngine for "uniform", a SADPPrivacyTracker
    for "sadp" — see get_persistent_privacy_engines / SADPPrivacyTracker).
    Both accumulate step history additively across calls, so reusing one
    instance per device for its whole FL lifetime is what makes the reported
    ε the true *cumulative* ε for that device. Passing None (uniform mode
    only) creates a fresh engine whose ε only reflects this single call —
    do not use None inside the FL round loop.

    dp_mode="sadp": per-layer-depth-group clip+noise (PHANTOM-FL Innovation
    I2 — see model/sadp_engine.py) instead of one global clip+noise for the
    whole model. group_of (from sadp_engine.assign_depth_groups) and
    group_sigmas (from sadp_engine.compute_sadp_group_sigmas) are required.
    """
    # Only optimise params that require grad — identical to model.parameters()
    # in normal mode, but under --freeze_encoders it excludes the frozen
    # encoders so Opacus's DPOptimizer never sees params without a grad_sample.
    optimizer = torch.optim.Adam(
        [p for p in model.parameters() if p.requires_grad],
        lr=lr, weight_decay=1e-4)
    # Class weighting is applied INSIDE local training so every client
    # optimises the same objective. Weights are global (computed once on the
    # pooled train split), not per-client: a per-client weighting would make
    # low-prevalence clients optimise a different loss from high-prevalence
    # ones, and FedAvg would then be averaging models trained on different
    # objectives.
    loss_fn = nn.CrossEntropyLoss(
        weight=class_weight.to(device) if class_weight is not None else None)

    if no_dp:
        # Genuine no-privacy arm: no Opacus wrapper, no clipping, no noise.
        #
        # This exists because Phase 6 needs S3 (HED-FL: hierarchy WITHOUT DP)
        # and A2 (the proposed system with DP removed). Both were previously
        # approximated by running eps=1000, which is very low noise but is
        # still per-sample-clipped DP-SGD — so it answers "what does a loose
        # budget cost", not "what does privacy cost at all". Clipping alone
        # changes the optimisation, so the eps=1000 proxy silently understates
        # the true no-DP ceiling and therefore understates DP's cost.
        model.train()
        total_loss, total = 0.0, 0
        for _ in range(n_epochs):
            for xa, xb, _tab, y in loader:
                optimizer.zero_grad()
                loss = loss_fn(model(xa.to(device, non_blocking=True),
                                     xb.to(device, non_blocking=True)),
                               y.to(device, non_blocking=True))
                loss.backward()
                optimizer.step()
                total_loss += loss.item() * len(y)
                total += len(y)
        return {"loss": total_loss / max(total, 1),
                "epsilon_spent": float("inf"),   # key the FL loop reads
                "n_samples": total, "dp": False}

    try:
        if dp_mode == "sadp":
            from sadp_engine import make_sadp_model
            dp_model, dp_opt = make_sadp_model(
                model, optimizer, group_sigmas=group_sigmas,
                max_grad_norm=max_grad_norm, group_of=group_of,
            )
            dp_model.train()
            total_loss, total = 0.0, 0
            for _ in range(n_epochs):
                for ecg, cxr, _tab, labels in loader:
                    dp_opt.zero_grad()
                    logits = dp_model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True))
                    loss = loss_fn(logits, labels.to(device, non_blocking=True))
                    loss.backward()
                    dp_opt.step()
                    total_loss += loss.item() * len(labels)
                    total += len(labels)
            sample_rate = min(loader.batch_size / max(len(loader.dataset), 1), 1.0)
            steps_this_call = n_epochs * len(loader)
            privacy_engine.record(group_sigmas, sample_rate, steps_this_call)
            eps_spent = privacy_engine.get_epsilon(delta)
        else:
            from dp_engine import make_dp_model, get_epsilon_spent
            dp_model, dp_opt, dp_loader, pe = make_dp_model(
                model, optimizer, loader,
                noise_multiplier=noise_multiplier,
                max_grad_norm=max_grad_norm,
                privacy_engine=privacy_engine,
            )
            dp_model.train()
            total_loss, total = 0.0, 0
            for _ in range(n_epochs):
                for ecg, cxr, _tab, labels in dp_loader:
                    dp_opt.zero_grad()
                    logits = dp_model(ecg.to(device, non_blocking=True), cxr.to(device, non_blocking=True))
                    loss = loss_fn(logits, labels.to(device, non_blocking=True))
                    loss.backward()
                    dp_opt.step()
                    total_loss += loss.item() * len(labels)
                    total += len(labels)
            eps_spent = get_epsilon_spent(pe, delta)

        return {"loss": total_loss / max(total, 1),
                "epsilon_spent": eps_spent,
                "n_samples": total}
    except Exception as e:
        raise RuntimeError(f"[HFL-Trainer] DP-SGD training failed: {e}") from e


def edge_fedavg(global_state: dict, client_updates: List[Dict],
                client_sizes: List[int]) -> dict:
    """Weighted FedAvg at edge level."""
    total = sum(client_sizes)
    agg = {}
    for key in global_state:
        if not global_state[key].is_floating_point():
            agg[key] = global_state[key].clone()
            continue
        agg[key] = sum(
            (n / total) * upd[key].float()
            for n, upd in zip(client_sizes, client_updates)
        )
    return agg


def train_hfl_mm_hc(args) -> Dict:
    """
    Main HFL-MM-HC training loop: 2-tier FedAvg + DP-SGD + conformal.
    """
    # Records which corpus is active so metric grouping resolves from the
    # registry (see _metric_group_rel). Does not affect the DP unit.
    _ACTIVE_DATASET[0] = getattr(args, "dataset", None)
    from hfl_mm_model import build_hfl_mm_hc
    from compression import GradientCompressor
    from fedconform_hc import LocalConformCalibrator, FedConformAggregator
    from aswa import compute_aswa_weights, mean_edge_loss
    from fedkd_e import collect_teacher_soft_logits, edge_distill_refine

    # Reproducibility: fix the RNG stream (python/numpy/torch/CUDA). This does
    # not change the algorithm — it only makes a run repeatable. Defensive so
    # the trainer still runs if the engineering package is unavailable.
    _seed = int(getattr(args, "seed", 42))
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # SIMULATORS/ — engineering/ lives here
        from engineering.runctx import set_global_seed
        set_global_seed(_seed, deterministic=bool(getattr(args, "deterministic", False)))
    except Exception:
        set_seed(_seed)   # fallback to device_utils.set_seed

    device = get_device()
    optimize_gpu()

    # Load partition metadata
    meta_path = os.path.join(args.partition_dir, "partition_meta.json")
    with open(meta_path) as f:
        meta = json.load(f)

    n_devices = meta["n_devices"]
    n_edges = meta["n_edges"]
    edge_assignments = {int(k): v for k, v in meta["edge_assignments"].items()}

    # --n_edges overrides the partition's edge count by REASSIGNING devices,
    # leaving every device's data untouched. Until now this flag was parsed and
    # then never read: the topology always came from partition_meta.json, so
    # `--n_edges 1` silently trained the ordinary two-edge hierarchy. The
    # ablation arm that reports "flat tier" was therefore not flat, and would
    # have been published as a measurement of a topology that never ran.
    if args.n_edges is not None and args.n_edges != n_edges:
        if args.n_edges < 1 or args.n_edges > n_devices:
            raise SystemExit(f"--n_edges {args.n_edges} outside [1, {n_devices}]")
        new_assign = {e: [] for e in range(args.n_edges)}
        for dev in range(n_devices):            # round-robin, as the partitioner does
            new_assign[dev % args.n_edges].append(dev)
        print(f"[topology] --n_edges {args.n_edges} overrides partition's "
              f"{n_edges}: {dict(new_assign)}")
        n_edges = args.n_edges
        edge_assignments = new_assign

    # Build global model
    global_model = build_hfl_mm_hc(n_classes=args.n_classes, **_model_kw(args)).to(device)
    if args.freeze_encoders:
        from hfl_mm_model import freeze_encoders, load_pretrained_encoders
        if args.pretrained_encoders:
            load_pretrained_encoders(global_model, args.pretrained_encoders)
            print(f"[DP-FT] Loaded pretrained encoders ← {args.pretrained_encoders}")
        else:
            print("[DP-FT][WARN] --freeze_encoders WITHOUT --pretrained_encoders: "
                  "freezing RANDOM-init encoders — features will be uninformative. "
                  "Only meaningful with pretrained encoder weights.")
        freeze_encoders(global_model)
        _ntr = sum(p.numel() for p in global_model.parameters() if p.requires_grad)
        _ntot = sum(p.numel() for p in global_model.parameters())
        print(f"[DP-FT] Encoders frozen — DP-training {_ntr:,}/{_ntot:,} params "
              f"({100*_ntr/_ntot:.1f}%): fusion head only")
    gpu_memory_info()
    compressor = GradientCompressor(sparsity=args.sparsity, quant_bits=args.quant_bits)
    conform_agg = FedConformAggregator()

    # Build the full multimodal dataset ONCE (~2 GB RSS) and share it across
    # all devices via Subset. Building one dataset per device would multiply
    # RAM by n_devices (~12 GB for 6 devices) and OOM/freeze a 16 GB machine.
    print("Loading full dataset (shared across devices)...")
    from datasets import get_spec
    _spec = get_spec(getattr(args, "dataset", "vitaldb"))
    print(_spec.describe())
    full_ds = _spec.build_full(args.data_dir)

    # Lazy-load device loaders: build on first access, reuse thereafter.
    # All loaders index into the single shared `full_ds` above.
    # ── PATIENT-level DP support ─────────────────────────────────────────
    # Groups are built ONCE per device: grouping is a pure function of the
    # partition indices and the case ids, so recomputing it every round would
    # be wasted work in the hot loop.
    _patient_groups: Dict[int, list] = {}
    _case_ids = None
    if args.dp_unit == "patient" and not args.no_dp and (
            args.agg_mode == "aswa" or args.edge_distill_epochs > 0):
        # Both re-weight or refine on unprotected quantities (local losses,
        # edge validation data) that the patient-level guarantee does not cover.
        raise SystemExit("[FATAL] --agg_mode aswa / --edge_distill_epochs are not "
                         "covered by the patient-level guarantee")
    if (args.sigma_mode != "worst" or args.accountant != "rdp") and \
            args.dp_unit != "patient" and not args.no_dp:
        raise SystemExit("[FATAL] --sigma_mode / --accountant apply to the "
                         "patient-level path only (--dp_unit patient)")
    if args.dp_unit == "patient" and args.dp_mode == "sadp" and not args.no_dp:
        # The patient branch of the round loop never consults dp_mode, so this
        # combination would train uniform patient-level DP and report it as SADP.
        raise SystemExit(
            "[FATAL] --dp_mode sadp is implemented for --dp_unit sample only; "
            "under --dp_unit patient it would silently run uniform DP.")
    if args.dp_unit == "patient":
        _cid_path = os.path.join(args.data_dir, "meta", "case_ids.npy")
        if not os.path.exists(_cid_path):
            raise SystemExit(
                f"[FATAL] --dp_unit patient needs per-sample case ids and none "
                f"were found at:\n  {_cid_path}\n"
                f"Without them there is no way to know which windows belong to "
                f"the same person, so a patient-level guarantee cannot be "
                f"constructed. Dataset '{args.dataset}' may not support it.")
        _case_ids = np.load(_cid_path)
        from patient_dp import (group_indices_by_patient,
                                patient_level_dp_train,
                                PatientPrivacyAccountant,
                                patient_level_noise_multiplier_multidevice,
                                patient_level_noise_multipliers_per_client)
        for _d in range(args.n_devices):
            _tr = np.load(os.path.join(args.partition_dir,
                                       f"device_{_d:02d}_train.npy"))
            _patient_groups[_d] = group_indices_by_patient(_tr, _case_ids)
        _npat = [len(g) for g in _patient_groups.values()]
        print(f"[patient-DP] {sum(_npat)} patients across {args.n_devices} "
              f"devices (min {min(_npat)}, max {max(_npat)} per device)")

    _loader_cache: Dict[int, dict] = {}

    def get_device_loaders(dev_id: int) -> dict:
        if dev_id not in _loader_cache:
            _loader_cache[dev_id] = load_partitioned_data(
                args.partition_dir, args.data_dir, dev_id, args.batch_size,
                full_ds=full_ds)
        return _loader_cache[dev_id]

    # Pooled validation across every client — this drives per-round reporting
    # and best-checkpoint selection, so it must represent the whole population
    # rather than one client. Built once and reused, like full_ds.
    _pooled_val_loader, _val_order = build_pooled_loader(
        args.partition_dir, n_devices, full_ds, "val", args.batch_size)
    # METRIC grouping only — the DP unit and the split key stay case_ids.
    _grp_path = os.path.join(args.data_dir, _metric_group_rel())
    _val_groups = (np.load(_grp_path)[_val_order]
                   if os.path.exists(_grp_path) else None)
    # Inverse-frequency class weights from the pooled TRAIN split only.
    _class_weight = None
    if args.class_weight == "balanced":
        _tr_idx = np.concatenate([
            np.load(os.path.join(args.partition_dir, f"device_{d:02d}_train.npy"))
            for d in range(n_devices)])
        _tr_y = np.array([int(full_ds[int(i)][3]) for i in _tr_idx])
        _cnt = np.bincount(_tr_y, minlength=args.n_classes).astype(np.float64)
        # n / (K * count_k) — the sklearn 'balanced' convention; mean weight 1
        _w = len(_tr_y) / (args.n_classes * np.maximum(_cnt, 1))
        _class_weight = torch.tensor(_w, dtype=torch.float32)
        print(f"[loss] balanced class weights from {len(_tr_y):,} train samples: "
              f"{np.round(_w, 3).tolist()}  (counts {_cnt.astype(int).tolist()})")

    print(f"[eval] pooled val: {len(_val_order):,} samples across "
          f"{n_devices} clients"
          + (f", {len(np.unique(_val_groups)):,} cases" if _val_groups is not None else ""))

    # FedKD-E (IP-4): one fixed calibration set per edge (that edge's first
    # device's val split) used both to capture each client's soft-label
    # "opinion" and to fine-tune the averaged edge model against it. Fixed
    # per edge (not per round) so teacher/student batches always line up.
    edge_distill_loaders = None
    if args.edge_distill_epochs > 0:
        edge_distill_loaders = {
            e: get_device_loaders(edge_assignments[e][0])["val"]
            for e in range(n_edges)
        }

    # Pre-compute σ for the full FL budget once.
    # Each device trains for (global_rounds × edge_rounds) local calls.
    # Using a fixed σ across all calls is what makes end-to-end DP valid.
    # n_train is read from partition metadata (no data pre-load needed here).
    n_fl_calls_total = args.rounds * args.tau_e   # per-device total local calls
    sadp_group_of = None
    sadp_group_sigmas = None
    if args.dp_mode == "sadp":
        from sadp_engine import assign_depth_groups, compute_sadp_group_sigmas, SADPPrivacyTracker, N_GROUPS
        # Group assignment only depends on architecture (module names), not
        # on any trained weights, so a throwaway instance is enough.
        sadp_group_of = assign_depth_groups(build_hfl_mm_hc(n_classes=args.n_classes, **_model_kw(args)))
        if args.noise_multiplier is not None:
            sadp_group_sigmas = [args.noise_multiplier] * N_GROUPS
            sadp_group_deltas = [args.delta / N_GROUPS] * N_GROUPS
            print(f"[SADP-Engine] Using manually specified σ={args.noise_multiplier:.4f} "
                  f"for every depth group")
        else:
            _n_train_min = min(
                meta["devices"][str(d)]["n_train"] for d in range(n_devices)
            )
            sadp_group_sigmas, sadp_group_deltas = compute_sadp_group_sigmas(
                target_epsilon=args.epsilon,
                target_delta=args.delta,
                n_fl_calls=n_fl_calls_total,
                n_samples=_n_train_min,
                batch_size=args.batch_size,
                local_epochs=1,
            )
        noise_multiplier = None  # unused in sadp mode; group_sigmas carries the per-group σ instead
        # One tracker per device, reused for every local-training call that
        # device makes across the ENTIRE run — same reasoning as the Opacus
        # PrivacyEngine reuse below, just for SADP's own RDP composition.
        device_privacy_engines = {d: SADPPrivacyTracker(sadp_group_deltas) for d in range(n_devices)}
    elif args.noise_multiplier is not None:
        noise_multiplier = args.noise_multiplier
        print(f"[DP-Engine] Using manually specified σ={noise_multiplier:.4f}")
    else:
        from dp_engine import compute_fl_noise_multiplier
        # Read the ACTUAL partition files, not partition_meta.json.
        #
        # Metadata drifts. make_public_split.py rewrites the train splits to
        # carve out a disjoint pretraining pool but does not rewrite the meta
        # file, so the calibration budgeted noise for 1,422 samples when 1,147
        # existed — sample rate 0.0450 assumed against 0.0558 actual. The
        # result was sigma too small and a reported eps of 1.0593 against a
        # 1.0 budget: the run BREACHED its own privacy guarantee, silently,
        # while every log line looked healthy.
        #
        # Sample rate is what the accountant is most sensitive to, so it must
        # come from the data that is actually loaded.
        _n_train_min = min(
            len(np.load(os.path.join(args.partition_dir,
                                     f"device_{d:02d}_train.npy")))
            for d in range(n_devices))
        _meta_min = min(meta["devices"][str(d)]["n_train"] for d in range(n_devices))
        if _meta_min != _n_train_min:
            print(f"[DP][WARN] partition_meta.json says min n_train={_meta_min:,} "
                  f"but the files hold {_n_train_min:,}. Calibrating sigma on the "
                  f"FILES. Stale metadata would under-provision noise and breach "
                  f"the budget.")
        # Calibrate against EVERY client, not a single stand-in.
        #
        # The reported epsilon is the MAX across clients. Small clients have a
        # high sampling rate over few steps; large clients the reverse. Neither
        # dominates universally, so calibrating from one device can
        # under-provision the others. Combined with floor(n/B) instead of
        # ceil(n/B) for the step count, this produced eps=1.0107 against a 1.0
        # budget — a silent breach of the guarantee the thesis claims.
        from dp_engine import compute_fl_noise_multiplier_multidevice
        _dev_n = [len(np.load(os.path.join(args.partition_dir,
                                           f"device_{d:02d}_train.npy")))
                  for d in range(n_devices)]
        noise_multiplier = compute_fl_noise_multiplier_multidevice(
            target_epsilon=args.epsilon,
            target_delta=args.delta,
            n_fl_calls=n_fl_calls_total,
            device_n_train=_dev_n,
            batch_size=args.batch_size,
            local_epochs=1,
        )

        # ── PATIENT-level recalibration ──────────────────────────────────
        # Sigma above was calibrated with the WINDOW sampling rate. Under
        # --dp_unit patient the clip is applied to each patient's SUMMED
        # gradient, so the sampling rate must be patients-per-batch over
        # TOTAL PATIENTS. Leaving the window rate in place while clipping per
        # patient would report a budget that describes neither unit — the
        # single most consequential thing to get wrong here.
        if args.dp_unit == "patient" and not args.no_dp:
            # Worst-client calibration, as on the record-level path: a
            # one-client calibration can leave another client over budget.
            if args.sigma_mode == "per_client":
                # Each client meets the budget with its own sigma_k (parallel
                # composition: a patient is touched by one client only).
                _sig = patient_level_noise_multipliers_per_client(
                    target_epsilon=args.epsilon, target_delta=args.delta,
                    device_n_patients=[len(g) for g in _patient_groups.values()],
                    patients_per_batch=args.patients_per_batch,
                    n_fl_calls=n_fl_calls_total, local_epochs=1,
                    accountant=args.accountant)
                _dev_sigma = dict(zip(_patient_groups.keys(), _sig))
                noise_multiplier = max(_sig)        # logged; the worst client
            else:
                noise_multiplier = patient_level_noise_multiplier_multidevice(
                    target_epsilon=args.epsilon, target_delta=args.delta,
                    device_n_patients=[len(g) for g in _patient_groups.values()],
                    patients_per_batch=args.patients_per_batch,
                    n_fl_calls=n_fl_calls_total, local_epochs=1,
                    accountant=args.accountant)
                _dev_sigma = {d: noise_multiplier for d in _patient_groups}
            _patient_accountants = {
                d: PatientPrivacyAccountant(
                    sample_rate=min(args.patients_per_batch / max(len(g), 1), 1.0),
                    noise_multiplier=_dev_sigma[d], accountant=args.accountant)
                for d, g in _patient_groups.items()}
            print(f"[patient-DP] privacy unit = PATIENT. Reported epsilon "
                  f"protects a whole person, not one 10-minute window.")

    # One PrivacyEngine per device, reused for every local-training call that
    # device makes across the ENTIRE run. Opacus's accountant lives on the
    # engine and composes ε additively across make_private() calls — reusing
    # one engine per device (not a fresh one per call) is what makes
    # cumulative_eps below the true composed privacy loss, per device, rather
    # than a proxy that only reflects the most recent local training call.
    if args.dp_mode != "sadp":
        from dp_engine import new_device_privacy_engines
        device_privacy_engines = new_device_privacy_engines(n_devices)

    # Results log
    results_log = []
    best_auc, best_state, best_round = 0.0, None, None
    _conformal_calls = [0]     # list so the inner scope can increment
    q_global = 0.9  # initial conformal quantile
    cumulative_eps = 0.0  # true per-device cumulative ε, max across devices

    _baseline = getattr(args, "baseline", "none")
    if _baseline != "none":
        import lit_baselines as _lit
        _lit_rng = np.random.default_rng(args.seed)
        print(f"[baseline] {_baseline}: " + (
            f"no DP, dense float32 upload, {args.hedfl_fraction:.0%} of each group "
            f"per low-level round" if _baseline == "hedfl" else
            f"flat FL, exponential-mechanism perturbation at nominal eps="
            f"{args.epsilon} (N={args.fl2dp_candidates}), gradient shuffling "
            f"w={tuple(args.fl2dp_weights)}, dense float32 upload"))

    print(f"\nStarting HFL-MM-HC training: {args.rounds} global rounds, "
          f"{args.tau_e} edge rounds, {n_devices} devices, {n_edges} edges")
    if args.dp_mode == "sadp":
        print(f"DP: ε_total={args.epsilon}, δ={args.delta}, "
              f"σ_groups={[round(s, 4) for s in sadp_group_sigmas]}, "
              f"C={args.max_grad_norm}, n_fl_calls={n_fl_calls_total}")
    else:
        print(f"DP: ε_total={args.epsilon}, δ={args.delta}, σ={noise_multiplier:.4f}, "
              f"C={args.max_grad_norm}, n_fl_calls={n_fl_calls_total}")

    for global_round in range(1, args.rounds + 1):
        round_start = time.time()
        global_state = {k: v.clone() for k, v in global_model.state_dict().items()}

        edge_states = {e: copy.deepcopy(global_state) for e in range(n_edges)}
        round_eps_spent = []
        round_clip_sat = []
        round_uplink_bytes = 0   # total compressed bytes uploaded this global round

        for edge_round in range(1, args.tau_e + 1):
            edge_client_states = {e: [] for e in range(n_edges)}
            edge_client_sizes = {e: [] for e in range(n_edges)}
            edge_q_tildes = {e: [] for e in range(n_edges)}
            edge_client_losses = {e: [] for e in range(n_edges)}   # ASWA (IP-3)
            edge_teacher_logits = {e: [] for e in range(n_edges)}  # FedKD-E (IP-4)

            _active = (_lit.hedfl_select(edge_assignments, args.hedfl_fraction, _lit_rng)
                       if _baseline == "hedfl" else None)

            # Step 1: Local DP training on all devices
            for dev_id in range(n_devices):
                if _active is not None and dev_id not in _active:
                    continue
                edge_id = next(e for e, devs in edge_assignments.items()
                               if dev_id in devs)
                local_model = build_hfl_mm_hc(n_classes=args.n_classes, **_model_kw(args)).to(device)
                local_model.load_state_dict(edge_states[edge_id])
                if args.freeze_encoders:
                    # requires_grad is not in state_dict — re-freeze after every
                    # rebuild/load so only the head is DP-trained this round.
                    freeze_encoders(local_model)

                if args.dp_unit == "patient" and not args.no_dp:
                    train_result = patient_level_dp_train(
                        local_model, full_ds, _patient_groups[dev_id], device,
                        noise_multiplier=_dev_sigma[dev_id],
                        max_grad_norm=args.max_grad_norm, lr=args.lr,
                        n_epochs=1,
                        patients_per_batch=args.patients_per_batch,
                        accountant=_patient_accountants[dev_id],
                        class_weight=_class_weight,
                        clip_norm=args.clip_norm)
                elif _baseline == "fl2dp":
                    train_result = _lit.fl2dp_local_train(
                        local_model, get_device_loaders(dev_id)["train"], device,
                        lr=args.lr, epsilon=args.epsilon,
                        n_candidates=args.fl2dp_candidates,
                        class_weight=_class_weight)
                else:
                    train_result = local_dp_train(
                        local_model, get_device_loaders(dev_id)["train"],
                        device, args.delta,
                        args.max_grad_norm, args.lr,
                        noise_multiplier=noise_multiplier,
                        n_epochs=1,
                        privacy_engine=device_privacy_engines[dev_id],
                        dp_mode=args.dp_mode,
                        group_of=sadp_group_of,
                        group_sigmas=sadp_group_sigmas,
                        class_weight=_class_weight,
                        no_dp=args.no_dp,
                    )
                # epsilon_spent is now this device's TRUE cumulative ε across
                # every local-training call it has made so far this run (the
                # persistent per-device PrivacyEngine composes it), not just
                # this one call.
                round_eps_spent.append(train_result["epsilon_spent"])
                if "clip_saturation" in train_result:
                    # N-D diagnostic: fraction of per-patient gradients the
                    # clip actually bound. Measured inside the real training
                    # loop rather than by a probe at initialisation, because
                    # gradient norms shrink as the head fits and saturation
                    # therefore moves over rounds.
                    round_clip_sat.append(train_result["clip_saturation"])
                edge_client_losses[edge_id].append(train_result["loss"])

                # Compress delta
                delta_params = {
                    n: local_model.state_dict()[n] - edge_states[edge_id][n]
                    for n in global_state
                    if global_state[n].is_floating_point()
                }
                if _baseline != "none":
                    # Both prior-art systems upload the model uncompressed.
                    round_uplink_bytes += _lit.dense_uplink_bytes(local_model)
                    edge_client_states[edge_id].append(
                        {k: v.detach().clone() for k, v in local_model.state_dict().items()})
                    edge_client_sizes[edge_id].append(train_result["n_samples"])
                    del local_model
                    torch.cuda.empty_cache()
                    continue
                compressed = compressor.compress(delta_params)
                # Measure actual uplink bytes: int32 indices + payload + 8B
                # header per layer. The payload width is read with .nbytes
                # rather than len(): those agree only while the payload is
                # uint8, so an arm that disables quantization (quant_bits=32,
                # float32 payload) would otherwise report a quarter of the
                # traffic it really sends — understating the cost of exactly
                # the component the ablation is trying to price. Unaffected at
                # the default 8 bits, where nbytes == len.
                _uplink_bytes = sum(
                    len(v["indices"]) * 4 + v["values_uint8"].nbytes + 8
                    for v in compressed.values()
                )
                round_uplink_bytes += _uplink_bytes
                decompressed = compressor.decompress(compressed, device)

                # Reconstruct full state with compressed delta
                updated_state = copy.deepcopy(edge_states[edge_id])
                for n in decompressed:
                    updated_state[n] = updated_state[n] + decompressed[n]

                edge_client_states[edge_id].append(updated_state)
                # Under patient-level DP the averaging weight must be public.
                # n_samples counts the windows of the patients Poisson-drawn this
                # call, so it depends on who was sampled and how many records
                # they hold; the edge would receive it unprotected. The client's
                # static training size is the public weight the paper states.
                edge_client_sizes[edge_id].append(
                    get_device_loaders(dev_id)["n_train"]
                    if args.dp_unit == "patient" and not args.no_dp
                    else train_result["n_samples"])

                # Conformal calibration. Runs on the FINAL round only by
                # default: it is a post-hoc procedure that does not feed
                # training, and calibrating every edge round would spend
                # rounds*tau_e * epsilon_conf of privacy budget — with
                # rounds=20, tau_e=5 that is 100x, dwarfing the training
                # budget the headline epsilon refers to. --conformal_every_round
                # restores the old behaviour and prices it honestly below.
                # FINAL EDGE ROUND of the final global round — not merely the
                # final global round. `global_round == args.rounds` stays true
                # across all tau_e edge rounds inside it, so this fired tau_e
                # times per device: 9 devices x 5 edge rounds = 45 calls, i.e.
                # 5 calibrations each. At eps_conf=0.5 that charged 2.50 of
                # privacy instead of 0.50, and pushed the composed total to
                # 3.49 against a stated budget of 1.0. The training epsilon was
                # correct throughout; only the conformal term was overspent.
                # NB: the edge loop is range(1, tau_e+1), so the final edge
                # round is tau_e, not tau_e-1. Off by one here would calibrate
                # one edge round early — still once, but on a model that has
                # not had its last edge aggregation.
                _is_last = (global_round == args.rounds and
                            edge_round == args.tau_e)
                if args.conformal_every_round or _is_last:
                    cal_loader = get_device_loaders(dev_id)["val"]
                    cal = LocalConformCalibrator(alpha=args.alpha_conf,
                                                 epsilon_conf=args.epsilon_conf)
                    # Patient-level release whenever the run is: one score per
                    # calibration patient (see LocalConformCalibrator).
                    _cal_groups = None
                    if _case_ids is not None:
                        _cal_groups = _case_ids[np.load(os.path.join(
                            args.partition_dir, f"device_{dev_id:02d}_val.npy"))]
                    q_tilde = cal.calibrate(local_model, cal_loader, device,
                                            groups=_cal_groups,
                                            seed=args.seed * 1000 + dev_id)
                    edge_q_tildes[edge_id].append(q_tilde)
                    _conformal_calls[0] += 1

                # FedKD-E (IP-4): capture this just-updated client's soft-label
                # opinion on the edge's fixed calibration set before it's
                # discarded, so it can be distilled into the averaged model.
                if args.edge_distill_epochs > 0:
                    teacher_logits = collect_teacher_soft_logits(
                        local_model, edge_distill_loaders[edge_id], device,
                        temperature=args.edge_distill_temp, max_batches=1)
                    if teacher_logits is not None:
                        edge_teacher_logits[edge_id].append(teacher_logits)

                # Free GPU memory — critical: without this, 18 models accumulate per global round
                del local_model
                torch.cuda.empty_cache()

            if _baseline == "fl2dp":
                # Trusted shuffler: identity i is aggregated with the update it
                # is reassigned, under its own FedAvg weight (FL2DP Eq. 2).
                _tk = [n for n, p in global_model.named_parameters() if p.requires_grad]
                for edge_id in range(n_edges):
                    _st = edge_client_states[edge_id]
                    if len(_st) < 2:
                        continue
                    _upd = [torch.cat([(s[k] - edge_states[edge_id][k]).flatten()
                                       for k in _tk]) for s in _st]
                    _perm = _lit.fl2dp_shuffle(_upd, args.epsilon,
                                               args.fl2dp_weights, _lit_rng)
                    edge_client_states[edge_id] = [_st[j] for j in _perm]

            # Step 2: Edge aggregation
            for edge_id in range(n_edges):
                if edge_client_states[edge_id]:
                    edge_states[edge_id] = edge_fedavg(
                        edge_states[edge_id],
                        edge_client_states[edge_id],
                        edge_client_sizes[edge_id],
                    )
                    if args.edge_distill_epochs > 0 and edge_teacher_logits[edge_id]:
                        edge_states[edge_id] = edge_distill_refine(
                            edge_states[edge_id],
                            lambda: build_hfl_mm_hc(n_classes=args.n_classes, **_model_kw(args)),
                            edge_teacher_logits[edge_id],
                            edge_distill_loaders[edge_id], device,
                            epochs=args.edge_distill_epochs,
                            temperature=args.edge_distill_temp,
                            lr=args.edge_distill_lr, max_batches=1,
                        )

        # Step 3: Cloud aggregation
        edge_sizes = [sum(get_device_loaders(d)["n_train"]
                          for d in edge_assignments[e])
                      for e in range(n_edges)]
        total_samples = sum(edge_sizes)
        if args.agg_mode == "aswa":
            # ASWA (IP-3): re-weight each edge by data volume AND how well its
            # clients converged this round (last edge_round's mean local
            # loss), instead of purely by sample count.
            edge_losses = [mean_edge_loss(edge_client_losses, e) for e in range(n_edges)]
            cloud_weights = compute_aswa_weights(edge_sizes, edge_losses,
                                                 temperature=args.aswa_temperature)
        else:
            cloud_weights = [n / total_samples for n in edge_sizes]
        new_global_state = {}
        for key in global_state:
            if not global_state[key].is_floating_point():
                new_global_state[key] = global_state[key].clone()
                continue
            new_global_state[key] = sum(
                w * edge_states[e][key].float()
                for e, w in zip(range(n_edges), cloud_weights)
            )
        global_model.load_state_dict(new_global_state)
        compressor.reset_error_feedback()

        # Step 4: Global conformal quantile update
        # Only aggregate from edges that actually calibrated this round.
        # Calibration runs on the final round by default, so on earlier rounds
        # every list is empty and np.median/np.mean of [] returns nan with a
        # RuntimeWarning. Carry the previous q_global forward instead.
        _live = [e for e in range(n_edges) if edge_q_tildes[e]]
        q_edges = [conform_agg.edge_aggregate(edge_q_tildes[e])
                   for e in _live]
        if q_edges:
            q_global = conform_agg.cloud_aggregate(q_edges)

        # Step 5: Evaluate
        # Pooled across ALL clients. Using device 0's split alone made model
        # selection depend on one client's distribution — for VitalDB that is a
        # single surgical specialty (Biliary/Pancreas, 14.3 % ICU vs 19.7 %
        # overall), for WEAR a single subject. The best-checkpoint decision has
        # to see the population the model is claimed to serve.
        val_metrics = evaluate_model(global_model, _pooled_val_loader, device,
                                     group_ids=_val_groups)
        # Each device's PrivacyEngine persists across the whole run (see
        # device_privacy_engines above), so round_eps_spent already holds each
        # device's TRUE cumulative ε via Opacus's RDP/PRV composition — not a
        # single-call estimate. The FL-wide privacy guarantee is bounded by the
        # worst-case (highest-ε) device, so we report the max across devices.
        # This value is monotonically non-decreasing round over round because
        # the accountants' history only grows.
        cumulative_eps = max(round_eps_spent) if round_eps_spent else cumulative_eps
        round_time = time.time() - round_start

        log_entry = {
            "global_round": global_round,
            "val_accuracy": round(val_metrics["accuracy"], 4),
            "val_macro_auc": round(val_metrics["macro_auc"], 4),
            "val_auprc": round(val_metrics["auprc"], 4),
            "val_case_auc": (round(val_metrics["case_auc"], 4)
                             if "case_auc" in val_metrics else ""),
            "val_case_auprc": (round(val_metrics["case_auprc"], 4)
                               if "case_auprc" in val_metrics else ""),
            "epsilon_spent": round(cumulative_eps, 4),
            "q_global": round(q_global, 4),
            "round_time_s": round(round_time, 2),
            "uplink_bytes": round_uplink_bytes,   # feeds ns3_phase5_integration.py
            # N-D mechanism diagnostic. Empty under --dp_unit sample, where no
            # per-patient clip exists. Written every round because saturation
            # is expected to fall as the head fits.
            "clip_saturation": (round(sum(round_clip_sat) / len(round_clip_sat), 4)
                                if round_clip_sat else ""),
            "clip_norm": getattr(args, "clip_norm", ""),
        }
        results_log.append(log_entry)

        _case_str = (f"case_AUC={val_metrics['case_auc']:.4f} | "
                     if "case_auc" in val_metrics else "")
        print(f"Round {global_round:3d}/{args.rounds} | "
              f"AUC={val_metrics['macro_auc']:.4f} | "
              f"AUPRC={val_metrics['auprc']:.4f} | "
              f"{_case_str}"
              f"Acc={val_metrics['accuracy']:.4f} | "
              f"ε={cumulative_eps:.4f} | "
              f"q={q_global:.4f} | "
              f"{round_time:.1f}s")

        _sel = val_metrics["auprc" if args.select_on == "auprc" else "macro_auc"]
        if not np.isnan(_sel) and _sel > best_auc:
            best_auc = _sel
            best_state = copy.deepcopy(global_model.state_dict())
            best_round = global_round

        # Only meaningful when a budget is actually being spent. Under --no_dp
        # the accountant reports cumulative_eps = inf, and `inf >= epsilon` is
        # true on the first round, so the non-private arm stopped after 1 of 10
        # rounds. It then scored BELOW the private arm, which reads as
        # "differential privacy improves accuracy" — an artefact of early
        # stopping presented as a finding.
        if not args.no_dp and cumulative_eps >= args.epsilon:
            print(f"Privacy budget exhausted at round {global_round}. Stopping.")
            break

    # Final test evaluation — pooled across all devices' test splits (see
    # build_pooled_test_loader) rather than device 0's ~87-sample split alone,
    # which is too small/skewed to be a reliable headline number.
    global_model.load_state_dict(best_state)
    pooled_test_loader, _test_order = build_pooled_loader(
        args.partition_dir, n_devices, full_ds, "test", args.batch_size)

    # Group-level aggregation, when the dataset defines a grouping. VitalDB
    # scores 10-minute WINDOWS but the clinical unit is the OPERATION: windows
    # from one case are highly correlated, so window-level metrics overstate
    # the effective sample size. `case_ids.npy` maps each window to its case.
    _groups = None
    _gpath = os.path.join(args.data_dir, _metric_group_rel())
    if os.path.exists(_gpath):
        _groups = np.load(_gpath)[_test_order]

    test_metrics = evaluate_model(global_model, pooled_test_loader, device,
                                  group_ids=_groups)
    print(f"\nFinal Test  AUROC={test_metrics['macro_auc']:.4f} "
          f"AUPRC={test_metrics['auprc']:.4f} "
          f"Acc={test_metrics['accuracy']:.4f} | Best val {args.select_on.upper()}={best_auc:.4f}")
    # Persist the held-out TEST metrics next to the results CSV. The CSV holds
    # per-round VAL metrics only, so every downstream consumer previously had
    # to scrape them from stdout - and silently fell back to VAL when the print
    # format drifted, tabulating a val number against the baselines' test ones.
    try:
        import json as _json
        _tp = os.path.splitext(args.output)[0] + "_test.json"
        with open(_tp, "w") as _f:
            _json.dump({"dataset": args.dataset,
                        "split": "test",
                        "pooled_over_devices": True,
                        "accuracy": float(test_metrics["accuracy"]),
                        "macro_auc": float(test_metrics["macro_auc"]),
                        "auprc": float(test_metrics["auprc"]),
                        **_threshold_metrics(global_model, args, n_devices,
                                             full_ds, device),
                        "selected_on": args.select_on,
                        "best_val_auc": float(best_auc)}, _f, indent=2)
        print(f"[test] metrics written -> {_tp}")
    except Exception as _e:
        print(f"[test][WARN] could not write test metrics: {_e}")

    # Honest privacy accounting: the conformal calibration touches each
    # device's private validation data, so its budget composes with training.
    _cal_per_device = _conformal_calls[0] / max(n_devices, 1)
    _eps_conf_total = _cal_per_device * args.epsilon_conf
    print(f"\n[privacy] training eps={cumulative_eps:.4f} (delta={args.delta})")
    print(f"[privacy] conformal: {_cal_per_device:.0f} calibration(s)/device "
          f"x eps_conf={args.epsilon_conf} = {_eps_conf_total:.4f}")
    _eps_total = cumulative_eps + _eps_conf_total
    print(f"[privacy] TOTAL reportable eps = {_eps_total:.4f} "
          f"(basic composition)")
    # Persist the TOTAL next to the results. Downstream checkers previously read
    # epsilon_spent — the TRAINING term only — and reported 0.963 when the
    # composed budget was 3.49. A privacy objective must be scored on what the
    # whole system spends, not on its largest single component.
    try:
        import json as _json
        _ep = os.path.join(os.path.dirname(args.output) or ".",
                           f"privacy_total_{args.dataset}.json")
        with open(_ep, "w") as _f:
            _json.dump({"dataset": args.dataset,
                        "epsilon_training": float(cumulative_eps),
                        "epsilon_conformal": float(_eps_conf_total),
                        "calibrations_per_device": float(_cal_per_device),
                        "epsilon_conf_per_call": float(args.epsilon_conf),
                        "epsilon_TOTAL": float(_eps_total),
                        "delta": float(args.delta),
                        "composition": "basic"}, _f, indent=2)
        print(f"[privacy] total written -> {_ep}")
    except Exception as _e:
        print(f"[privacy][WARN] could not write total: {_e}")
    if _eps_conf_total > cumulative_eps:
        print("[privacy][WARN] the conformal budget now EXCEEDS the training "
              "budget — reduce --epsilon_conf or drop --conformal_every_round.")

    if "case_auc" in test_metrics:
        print(f"  case-level ({test_metrics['n_groups']} cases): "
              f"AUROC={test_metrics['case_auc']:.4f} "
              f"AUPRC={test_metrics['case_auprc']:.4f} "
              f"Acc={test_metrics['case_accuracy']:.4f}")

    # pFAL (IP-5): fit a small per-edge adapter on each edge's own local data
    # (frozen shared backbone) and evaluate it on that edge's own test data.
    # A frozen copy of the backbone is used so fitting adapters never mutates
    # the shared global_model / best_state already finalised above.
    personalized_metrics = None
    if args.personalize:
        from hfl_mm_model import PersonalizationAdapter, fit_personalization_adapter
        from torch.utils.data import ConcatDataset

        frozen_backbone = build_hfl_mm_hc(n_classes=args.n_classes, **_model_kw(args)).to(device)
        frozen_backbone.load_state_dict(best_state)
        _dl_kw = get_dataloader_kwargs(device)

        edge_results, edge_ns = [], []
        for e in range(n_edges):
            edge_devices = edge_assignments[e]
            val_loader = DataLoader(
                ConcatDataset([get_device_loaders(d)["val"].dataset for d in edge_devices]),
                batch_size=args.batch_size * 2, **_dl_kw)
            test_ds = ConcatDataset([get_device_loaders(d)["test"].dataset for d in edge_devices])
            test_loader = DataLoader(test_ds, batch_size=args.batch_size * 2, **_dl_kw)

            adapter = PersonalizationAdapter(n_classes=args.n_classes)
            adapter = fit_personalization_adapter(
                frozen_backbone, adapter, val_loader, device,
                epochs=args.personalize_epochs, lr=args.personalize_lr)
            metrics = evaluate_personalized(frozen_backbone, adapter, test_loader, device)
            edge_results.append(metrics)
            edge_ns.append(len(test_ds))
            print(f"  [pFAL] edge {e}: Acc={metrics['accuracy']:.4f} "
                  f"AUC={metrics['macro_auc']:.4f} (n={len(test_ds)})")

        total_n = sum(edge_ns) or 1
        personalized_metrics = {
            "accuracy": sum(m["accuracy"] * n for m, n in zip(edge_results, edge_ns)) / total_n,
            "macro_auc": sum(m["macro_auc"] * n for m, n in zip(edge_results, edge_ns)) / total_n,
            "per_edge": edge_results,
        }
        print(f"  [pFAL] pooled personalized: Acc={personalized_metrics['accuracy']:.4f} "
              f"AUC={personalized_metrics['macro_auc']:.4f}  (shared-backbone-only was "
              f"Acc={test_metrics['accuracy']:.4f} AUC={test_metrics['macro_auc']:.4f})")

    # Save checkpoint
    if args.save_checkpoint:
        os.makedirs(os.path.dirname(args.save_checkpoint) or ".", exist_ok=True)
        torch.save({"model_state": best_state,
                    "args": vars(args),
                    "q_global": q_global,
                    "test_metrics": test_metrics,
                    "personalized_metrics": personalized_metrics},
                   args.save_checkpoint)
        print(f"Checkpoint saved: {args.save_checkpoint}")

    # Save CSV results
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results_log[0].keys())
            writer.writeheader()
            writer.writerows(results_log)
        print(f"Results saved: {args.output}")

        # The per-round CSV carries VALIDATION metrics only. The test metrics
        # above are computed once, on the checkpoint selected by validation —
        # which is generally not the last round — so they cannot be recovered
        # from that CSV by reading its final row. Until now the only way to
        # reach them was to scrape stdout or load the whole checkpoint, and
        # every downstream consumer that tried to read `test_*` from the CSV
        # silently got nothing. Writing them beside the CSV makes them an
        # artefact rather than a side effect.
        def _plain(v):
            if isinstance(v, (np.floating, np.integer)):
                return v.item()
            return v

        sidecar = os.path.splitext(args.output)[0] + "_final.json"
        payload = {
            "dataset": args.dataset,
            "seed": args.seed,
            "rounds": args.rounds,
            "select_on": args.select_on,
            "best_val": float(best_auc),
            "selected_round": int(best_round) if best_round is not None else None,
            "epsilon_spent": _plain(results_log[-1].get("epsilon_spent"))
                             if results_log else None,
            "uplink_bytes_total": sum(int(r.get("uplink_bytes") or 0)
                                      for r in results_log),
            "test": {k: _plain(v) for k, v in test_metrics.items()},
        }
        if personalized_metrics:
            payload["personalized"] = {k: _plain(v)
                                       for k, v in personalized_metrics.items()
                                       if k != "per_edge"}
        with open(sidecar, "w") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"Final test metrics saved: {sidecar}")

    return {"test_metrics": test_metrics, "best_auc": best_auc, "log": results_log,
            "personalized_metrics": personalized_metrics}


if __name__ == "__main__":
    import json as _json, os as _os
    # Load shared config defaults (overridable by CLI args)
    _cfg_path = _os.path.join(_os.path.dirname(__file__), "..", "config", "hfl_config.json")
    _cfg = {}
    if _os.path.exists(_cfg_path):
        with open(_cfg_path) as _f:
            _raw = _json.load(_f)
        _cfg = {
            "rounds":    _raw.get("federated_learning", {}).get("total_fl_rounds", 20),
            "tau_e":     _raw.get("federated_learning", {}).get("tau_e", 5),
            "epsilon":   _raw.get("privacy", {}).get("epsilon", 1.0),
            "delta":     _raw.get("privacy", {}).get("delta", 1e-5),
            "lr":        _raw.get("federated_learning", {}).get("learning_rate", 1e-3),
            "batch_size":_raw.get("federated_learning", {}).get("batch_size", 32),
        }
        print(f"[Config] Loaded defaults from {_cfg_path}")

    parser = argparse.ArgumentParser(description="HFL-MM-HC Trainer")
    parser.add_argument("--dataset", default="vitaldb",
                        choices=sorted(REGISTRY),
                        help="Registry key; sets data/partition dirs, client and "
                             "class counts and the modality-B encoder unless "
                             "explicitly overridden.")
    parser.add_argument("--data_dir",       default=None)
    parser.add_argument("--partition_dir",  default=None)
    parser.add_argument("--rounds",         type=int,   default=_cfg.get("rounds",     20))
    parser.add_argument("--tau_e",          type=int,   default=_cfg.get("tau_e",      5))
    parser.add_argument("--n_devices",      type=int,   default=None)
    parser.add_argument("--n_edges",        type=int,   default=None,
                        help="override the partition's edge count by "
                             "reassigning devices round-robin; default None "
                             "means use the topology the partition defines")
    parser.add_argument("--class_weight", choices=["none", "balanced"],
                        default="none",
                        help="'balanced' weights the loss by inverse class "
                             "frequency, computed on the pooled TRAIN split. "
                             "Needed when the positive class is rare (VitalDB "
                             "is 19.7%%) or the model collapses to the majority.")
    parser.add_argument("--select_on", choices=["auc", "auprc"], default="auc",
                        help="Metric used to pick the best checkpoint. Prefer "
                             "'auprc' on imbalanced binary tasks: AUROC is "
                             "optimistic when negatives dominate.")
    parser.add_argument("--n_classes",      type=int,   default=None)
    parser.add_argument("--epsilon",        type=float, default=_cfg.get("epsilon",    1.0))
    parser.add_argument("--delta",          type=float, default=_cfg.get("delta",      1e-5))
    parser.add_argument("--max_grad_norm",  type=float, default=1.0)
    parser.add_argument("--noise_multiplier", type=float, default=None,
                        help="Fixed DP noise multiplier σ (or σ_base under --dp_mode sadp). "
                             "If set, overrides automatic calibration from --epsilon. Use "
                             "when you want direct control over σ (e.g. --noise_multiplier "
                             "1.1 for fast convergence).")
    parser.add_argument("--freeze_encoders", action="store_true",
                        help="DP fine-tuning mode: freeze both feature encoders "
                             "(encoder_a ECG-Mamba, encoder_b CXR-MobileNet) and DP-train "
                             "ONLY the fusion head (~28%% of params). A near-linear probe over "
                             "frozen pretrained features is DP-robust even at the large σ a "
                             "strict ε forces. Pair with --pretrained_encoders; freezing "
                             "random-init encoders yields garbage features.")
    parser.add_argument("--pretrained_encoders", type=str, default=None,
                        help="Path to an encoder checkpoint (from pretrain_encoders.py) whose "
                             "encoder_a/encoder_b weights are loaded before freezing. For a "
                             "valid ε guarantee this MUST be pretrained on NON-private data.")
    parser.add_argument("--clip_norm", choices=["none", "k", "sqrt_k"],
                        default="none",
                        help="claim N-D. Rescale a patient's SUMMED gradient by "
                             "k or sqrt(k) BEFORE clipping, where k is the "
                             "windows that patient contributed. Does NOT change "
                             "the guarantee: the clip still bounds each "
                             "patient's contribution to C, so sigma, epsilon "
                             "and delta are identical and the arms compare at a "
                             "matched budget. It changes the optimisation "
                             "geometry only. Applies under --dp_unit patient.")
    parser.add_argument("--dp_unit", choices=["sample", "patient"], default="sample",
                        help="What one unit of privacy protects. 'sample' is standard "
                             "DP-SGD and protects ONE 10-minute WINDOW. 'patient' clips "
                             "each patient's SUMMED gradient so the guarantee covers the "
                             "whole person. On VitalDB a patient contributes ~8 windows, "
                             "so these are materially different claims: a window-level "
                             "epsilon converted to patient level by group privacy "
                             "(k~8) degrades to epsilon~8 with an unusable delta. "
                             "Requires meta/case_ids.npy.")
    parser.add_argument("--patients_per_batch", type=int, default=16,
                        help="Poisson-sampled patients per step under --dp_unit patient.")
    parser.add_argument("--sigma_mode", choices=["worst", "per_client"], default="worst",
                        help="patient DP: one sigma calibrated on the worst client "
                             "(default), or each client's own sigma_k (still eps per "
                             "patient: a patient is on one client only)")
    parser.add_argument("--accountant", choices=["rdp", "prv"], default="rdp",
                        help="patient DP accountant for calibration and reporting")
    parser.add_argument("--no_dp", action="store_true",
                        help="Disable differential privacy entirely: no clipping, no "
                             "noise, no accountant (epsilon reported as inf). Required "
                             "for Phase 6 arm S3 (HED-FL = hierarchy without DP) and "
                             "ablation A2 (proposed minus DP). NOT the same as a large "
                             "--epsilon: that still clips per-sample gradients, so it "
                             "measures a loose budget rather than no privacy at all.")
    parser.add_argument("--dp_mode",        choices=["uniform", "sadp"], default="uniform",
                        help="uniform: one clip norm + noise multiplier for the whole model "
                             "(dp_engine.py). sadp: PHANTOM-FL Innovation I2 — per-layer-depth "
                             "clip+noise groups, full noise on the classification head, "
                             "reduced noise on the two feature-extractor encoders "
                             "(sadp_engine.py). See sadp_engine.py module docstring.")
    parser.add_argument("--agg_mode",       choices=["fedavg", "aswa"], default="fedavg",
                        help="fedavg: plain sample-weighted cloud aggregation. "
                             "aswa: PHANTOM-FL Innovation I3 — re-weight each edge by "
                             "data volume AND how well its clients converged this round "
                             "(see model/utils/aswa.py).")
    parser.add_argument("--aswa_temperature", type=float, default=1.0,
                        help="ASWA quality-tilt strength; 0 = identical to plain fedavg.")
    parser.add_argument("--edge_distill_epochs", type=int, default=0,
                        help="FedKD-E (IP-4): epochs of soft-label distillation refinement "
                             "on the averaged edge model per edge round. 0 = disabled "
                             "(plain edge_fedavg only). See model/utils/fedkd_e.py.")
    parser.add_argument("--edge_distill_temp", type=float, default=3.0,
                        help="FedKD-E softmax temperature for teacher/student distillation.")
    parser.add_argument("--edge_distill_lr", type=float, default=1e-4,
                        help="FedKD-E learning rate for the distillation refinement pass.")
    parser.add_argument("--personalize",    action="store_true",
                        help="pFAL (IP-5): fit a small per-edge adapter on each edge's own "
                             "local data (frozen shared backbone) after training, evaluated "
                             "on that edge's own test data. See hfl_mm_model.PersonalizationAdapter.")
    parser.add_argument("--personalize_epochs", type=int, default=3)
    parser.add_argument("--personalize_lr", type=float, default=1e-3)
    parser.add_argument("--alpha_conf",     type=float, default=0.1)
    parser.add_argument("--epsilon_conf",   type=float, default=0.5,
                        help="Privacy budget PER conformal calibration call. "
                             "Spent on each device's val data via the "
                             "exponential mechanism, and composed into the "
                             "reported total budget (see --conformal_every_round).")
    parser.add_argument("--conformal_every_round", action="store_true",
                        help="Calibrate every edge round instead of only the "
                             "final one. Multiplies the conformal budget by "
                             "rounds*tau_e — priced explicitly at the end.")
    parser.add_argument("--lr",             type=float, default=_cfg.get("lr",         1e-3))
    parser.add_argument("--batch_size",     type=int,   default=_cfg.get("batch_size", 32))
    parser.add_argument("--sparsity",       type=float, default=0.2)
    parser.add_argument("--quant_bits",     type=int,   default=8)
    parser.add_argument("--save_checkpoint", default=None,
                        help="default: checkpoints/best_<dataset>.pt — a fixed name would let a\n"
                             "run on one dataset overwrite another's checkpoint.")
    parser.add_argument("--output",          default="results/phase5/hfl_mm_hc_results.csv")
    # Engineering / observability flags (do not affect the FL algorithm)
    parser.add_argument("--seed",          type=int, default=42,
                        help="RNG seed for reproducibility")
    parser.add_argument("--deterministic", action="store_true",
                        help="Force deterministic cuDNN/algorithms (slower)")
    parser.add_argument("--no_preflight",  action="store_true",
                        help="Skip pre-run environment/data safety checks")
    parser.add_argument("--no_monitor",    action="store_true",
                        help="Disable the background resource watchdog")
    # Prior-art systems, run through this same loop so that only the mechanism
    # differs (see lit_baselines.py). Defaults are the published settings.
    parser.add_argument("--baseline", choices=["none", "hedfl", "fl2dp"], default="none",
                        help="hedfl: hierarchical FedAvg, no DP, dense upload, partial "
                             "participation (De Rango et al. 2023). fl2dp: flat FL with "
                             "exponential-mechanism gradient perturbation and gradient "
                             "shuffling (Gu et al. 2024), at nominal --epsilon.")
    parser.add_argument("--hedfl_fraction", type=float, default=0.6,
                        help="HED-FL: devices drawn per group per low-level round "
                             "(3 of 5 in its Table 1)")
    parser.add_argument("--fl2dp_candidates", type=int, default=15,
                        help="FL2DP: candidates N per coordinate (largest, most "
                             "accurate value in its Table II)")
    parser.add_argument("--fl2dp_weights", type=float, nargs=2, default=[0.1, 0.9],
                        help="FL2DP: (w1, w2) of Eq. 15 (its most private setting)")
    args = parser.parse_args()
    if args.baseline != "none":
        # Neither system has a patient-level mechanism; the DP-SGD path,
        # patient accounting and budget stop do not apply to them.
        if args.dp_unit == "patient":
            raise SystemExit("[FATAL] --baseline runs without --dp_unit patient")
        args.no_dp = True
        if args.baseline == "fl2dp":
            args.n_edges = 1     # flat FL: one aggregator, every round global

    # Fill anything the user did not set from the dataset registry, so
    # `--dataset wear` alone is a complete specification.
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "data" / "loaders"))
    from datasets import get_spec
    _sp = get_spec(args.dataset)
    for _a, _v in (("data_dir", _sp.data_dir), ("partition_dir", _sp.partition_dir),
                   ("n_devices", _sp.n_devices), ("n_classes", _sp.n_classes),
                   # Dataset-scoped so a wear run cannot overwrite the vitaldb
                   # checkpoint (both would previously land on best_model_hc.pt).
                   ("save_checkpoint", f"checkpoints/best_{args.dataset}.pt")):
        if getattr(args, _a, None) is None:
            setattr(args, _a, _v)

    # ── Engineering wrapper: preflight → metadata → monitored training ──────
    # All defensively imported so a missing engineering package never blocks
    # a training run.
    _monitor_cm = None
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # SIMULATORS/
        from engineering.preflight import run_preflight, format_report
        from engineering.runctx import capture_metadata
        from engineering.sysmon import ResourceMonitor

        if not args.no_preflight:
            _ok, _report = run_preflight(
                args.data_dir, args.partition_dir,
                os.path.dirname(args.save_checkpoint) or "checkpoints",
                os.path.dirname(args.output) or "results",
                n_devices=args.n_devices,
                required_files=get_spec(args.dataset).required_files)
            print(format_report(_report))
            if not _ok:
                print("[Preflight] FAIL — aborting. Re-run with --no_preflight "
                      "to override.")
                sys.exit(2)

        # Unique per-run suffix (timestamp + PID) so two runs writing to the
        # same results/monitoring directory — e.g. one launched while another
        # is still training — never clobber each other's metadata/monitor
        # files. A fixed shared filename here previously let a second run
        # silently overwrite an in-progress run's metadata.
        _run_tag = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_pid{os.getpid()}"

        _meta_path = os.path.join(os.path.dirname(args.output) or ".",
                                  f"run_metadata_{_run_tag}.json")
        capture_metadata(vars(args), seed=args.seed, out_path=_meta_path)
        print(f"[Metadata] Run metadata → {_meta_path}")

        if not args.no_monitor:
            _mon_csv = os.path.join("results", "monitoring",
                                    f"hfl_train_{_run_tag}.csv")
            _monitor_cm = ResourceMonitor(csv_path=_mon_csv, interval_s=10.0)
    except Exception as _e:
        print(f"[Engineering] utilities unavailable ({_e}); running plain.")

    if _monitor_cm is not None:
        with _monitor_cm as _mon:
            train_hfl_mm_hc(args)
        _s = _mon.summary()
        print(f"[Monitor] peak RSS={_s['rss_gb']:.2f} GB | "
              f"peak VRAM={_s['vram_reserved_gb']:.2f} GB | "
              f"min free RAM={_s['min_ram_avail_gb']:.2f} GB")
    else:
        train_hfl_mm_hc(args)
