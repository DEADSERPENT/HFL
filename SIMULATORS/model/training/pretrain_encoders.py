"""
pretrain_encoders.py — non-private central pretraining of the HFL-MM-HC
feature encoders, for the DP fine-tuning pipeline.

Writes a checkpoint {"encoders": {"encoder_a": ..., "encoder_b": ...}} that
hfl_trainer.py loads via --pretrained_encoders, then FREEZES both encoders and
DP-trains ONLY the fusion head (--freeze_encoders). A near-linear probe over
frozen, pretrained features is DP-robust even at the large σ a strict ε forces
(σ≈11.3 at ε=1), which end-to-end-from-scratch DP-SGD is not — see
hfl_mm_model.freeze_encoders and project memory "phase5_dp_collapse".

PRIVACY — read before using the checkpoint under a privacy claim:
  --public_data <indices.npy> : RIGOROUS. Pretrain ONLY on a disjoint public
      index set that no FL client ever uses. Analogous to encoder_b's ImageNet
      pretraining; the real-world source for encoder_a is a public 12-lead ECG
      corpus (e.g. PTB-XL). The subsequent ε=1 DP-SGD on the head is then a
      valid guarantee.
  (default, no --public_data) : PROXY / ORACLE. Pretrains on the pooled FL
      TRAIN data. This is NOT privacy-valid — the encoders would have seen the
      private data non-privately. Use ONLY to measure the *upper bound* of what
      head-only DP can achieve (proof of concept). A loud warning is printed.
"""

import os
import sys
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset

_MODEL_ROOT = Path(__file__).parent.parent
for _sub in ("privacy", "architecture", "training", "deploy", "utils"):
    sys.path.insert(0, str(_MODEL_ROOT / _sub))
sys.path.insert(0, str(_MODEL_ROOT.parent / "data" / "loaders"))

from device_utils import get_device, get_dataloader_kwargs, set_seed  # noqa: E402
from hfl_mm_model import build_hfl_mm_hc  # noqa: E402
from datasets import get_spec, REGISTRY# noqa: E402


def pooled_train_indices(partition_dir: str, n_devices: int) -> np.ndarray:
    """Union of every FL client's TRAIN indices (the proxy/oracle pool)."""
    idx = []
    for d in range(n_devices):
        idx.append(np.load(os.path.join(partition_dir, f"device_{d:02d}_train.npy")))
    return np.unique(np.concatenate(idx))


@torch.no_grad()
def _evaluate(model, loader, device) -> tuple:
    """Return (acc, auroc, auprc). Binary tasks need the positive-class score
    column, not the (N,2) matrix — passing the matrix makes sklearn raise, and
    the old except-branch turned that into a plausible-looking nan/0.0."""
    from sklearn.metrics import roc_auc_score, average_precision_score
    model.eval()
    correct, total = 0, 0
    all_p, all_y = [], []
    for xa, xb, _tab, y in loader:
        prob = torch.softmax(model(xa.to(device), xb.to(device)), dim=-1)
        correct += (prob.argmax(-1).cpu() == y).sum().item()
        total += len(y)
        all_p.append(prob.cpu().numpy())
        all_y.append(y.numpy())
    acc = correct / max(total, 1)
    p, yv = np.concatenate(all_p), np.concatenate(all_y)
    n = p.shape[1]
    try:
        if n == 2:
            auc = roc_auc_score(yv, p[:, 1])
            ap = average_precision_score(yv, p[:, 1])
        else:
            auc = roc_auc_score(yv, p, multi_class="ovr", average="macro",
                                labels=list(range(n)))
            ap = average_precision_score(np.eye(n)[yv], p, average="macro")
    except Exception as e:
        print(f"[pretrain][METRIC ERROR] {e} | classes present: {np.unique(yv)}")
        auc = ap = float("nan")
    return acc, float(auc), float(ap)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="vitaldb",
                    choices=sorted(REGISTRY),
                    help="Resolves data_dir / partition_dir / n_devices / n_classes / "
                         "encoder shapes from the dataset registry.")
    ap.add_argument("--data_dir", default=None, help="override registry path")
    ap.add_argument("--partition_dir", default=None, help="override registry path")
    ap.add_argument("--public_data", type=str, default=None,
                    help="Path to an .npy of PUBLIC sample indices (disjoint from all FL "
                         "clients). If omitted, pretrains on pooled FL train data (PROXY, "
                         "not privacy-valid).")
    ap.add_argument("--n_devices", type=int, default=None, help="override registry")
    ap.add_argument("--n_classes", type=int, default=None, help="override registry")
    ap.add_argument("--class_weight", choices=["none", "balanced", "auto"], default="auto",
                    help="auto = balanced for binary tasks, none otherwise")
    ap.add_argument("--select_on", choices=["auc", "auprc", "auto"], default="auto",
                    help="checkpoint-selection metric; auto = auprc for binary")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--eval_every", type=int, default=0,
                    help="validate every N optimiser steps (0 = only at epoch "
                         "end, the original behaviour). These encoders are "
                         "frozen downstream, so on a large corpus this is what "
                         "stops a collapsed state being selected.")
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--val_frac", type=float, default=0.15,
                    help="Fraction of the pretraining pool held out to monitor transfer.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--deterministic", action="store_true",
                    help="Force deterministic cuDNN/algorithms (slower). Without this, "
                         "--seed fixes the RNG stream but GPU kernel nondeterminism still "
                         "makes runs differ slightly — reruns of the same seed have drifted "
                         "by ~2e-4 val AUC. Use for reproducible checkpoints.")
    ap.add_argument("--output", default=None,
                    help="default: checkpoints/pretrained_encoders_<dataset>.pt")
    args = ap.parse_args()

    spec = get_spec(args.dataset)
    args.data_dir = args.data_dir or spec.data_dir
    args.partition_dir = args.partition_dir or spec.partition_dir
    args.n_devices = args.n_devices or spec.n_devices
    args.n_classes = args.n_classes or spec.n_classes
    args.output = args.output or f"checkpoints/pretrained_encoders_{args.dataset}.pt"
    if args.select_on == "auto":
        args.select_on = "auprc" if spec.n_classes == 2 else "auc"

    # Reproducibility: fix the RNG stream (python/numpy/torch/CUDA). Mirrors
    # hfl_trainer.py — defensive so pretraining still runs if the engineering
    # package is unavailable.
    try:
        sys.path.insert(0, str(_MODEL_ROOT.parent))  # SIMULATORS/ — engineering/ lives here
        from engineering.runctx import set_global_seed
        set_global_seed(args.seed, deterministic=args.deterministic)
    except Exception:
        set_seed(args.seed)   # fallback to device_utils.set_seed
        if args.deterministic:
            import torch.backends.cudnn as cudnn
            cudnn.deterministic, cudnn.benchmark = True, False
    device = get_device()
    full_ds = spec.build_full(args.data_dir)
    print(spec)

    # ---- select pretraining indices -------------------------------------
    if args.public_data:
        pool = np.load(args.public_data)
        used = pooled_train_indices(args.partition_dir, args.n_devices)
        overlap = np.intersect1d(pool, used)
        if len(overlap) > 0:
            raise SystemExit(
                f"[pretrain][FATAL] --public_data overlaps FL client train data in "
                f"{len(overlap)} indices — that breaks the ε guarantee. The public set "
                f"must be DISJOINT from every client's data.")
        print(f"[pretrain] RIGOROUS mode: {len(pool)} public indices, disjoint from FL clients.")
    else:
        pool = pooled_train_indices(args.partition_dir, args.n_devices)
        print("=" * 74)
        print("[pretrain][WARNING] PROXY/ORACLE mode — pretraining on the pooled FL")
        print("  TRAIN data. This is NOT a valid ε guarantee (encoders see private data")
        print("  non-privately). Use the resulting checkpoint ONLY to measure the upper")
        print("  bound of head-only DP. For a real guarantee pass --public_data.")
        print("=" * 74)

    # Hold out the monitoring split BY CASE, not by window.
    #
    # A patient contributes ~8 windows. Shuffling indices puts the same person
    # on both sides, so the reported val score measures memorisation of that
    # patient rather than transfer — it came out at 0.9999 AUC / 0.9995 AUPRC,
    # which is not a generalisation number and must not be quoted as one.
    # It does not affect the downstream privacy guarantee (the pool is still
    # disjoint from every client), only whether this metric means anything.
    rng = np.random.default_rng(args.seed)
    pool = pool.copy()
    _cid_path = os.path.join(args.data_dir, "meta", "case_ids.npy")
    if os.path.exists(_cid_path):
        _cids = np.load(_cid_path)[pool]
        _uniq = np.unique(_cids)
        rng.shuffle(_uniq)
        _n_val_cases = max(1, int(len(_uniq) * args.val_frac))
        _val_cases = set(_uniq[:_n_val_cases].tolist())
        _mask = np.isin(_cids, list(_val_cases))
        val_idx, train_idx = pool[_mask], pool[~_mask]
        print(f"[pretrain] val split BY CASE: {_n_val_cases}/{len(_uniq)} cases "
              f"held out -> {len(val_idx)} val / {len(train_idx)} train windows")
    else:
        rng.shuffle(pool)
        n_val = int(len(pool) * args.val_frac)
        val_idx, train_idx = pool[:n_val], pool[n_val:]
        print("[pretrain][WARN] no case_ids.npy — falling back to a WINDOW-level "
              "val split. The reported val score will be optimistic because the "
              "same subject can appear on both sides.")
    print(f"[pretrain] pretrain samples: {len(train_idx)} train / {len(val_idx)} val")

    dl_kw = get_dataloader_kwargs(device)
    train_loader = DataLoader(Subset(full_ds, train_idx.tolist()),
                              batch_size=args.batch_size, shuffle=True, **dl_kw)
    val_loader = DataLoader(Subset(full_ds, val_idx.tolist()),
                            batch_size=args.batch_size * 2, **dl_kw)

    # ---- train whole model non-privately; keep the encoders -------------
    _kw = {"n_channels_a": spec.n_channels_a}
    if spec.modality_b != "image":
        _kw.update(modality_b="features", feat_b_dim=spec.feat_b_dim)
    model = build_hfl_mm_hc(n_classes=args.n_classes, **_kw).to(device)
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad],
                           lr=args.lr, weight_decay=1e-4)

    # Same class-weight rule as the trainer and the baselines. Without it the
    # encoders are pretrained toward the majority class on a 19.7 %-positive
    # task, and every downstream head inherits that bias.
    cw = None
    if args.class_weight == "balanced" or (args.class_weight == "auto"
                                           and spec.n_classes == 2):
        ytr = np.array([int(full_ds[int(i)][3]) for i in train_idx])
        cnt = np.bincount(ytr, minlength=args.n_classes).astype(np.float64)
        cw = torch.tensor(len(ytr) / (args.n_classes * np.maximum(cnt, 1)),
                          dtype=torch.float32, device=device)
        print(f"[pretrain] class weights: {[round(float(x), 3) for x in cw]}")
    loss_fn = nn.CrossEntropyLoss(weight=cw)

    best_sel, best_auc, best_ap, best_state = -1.0, float("nan"), float("nan"), None

    # Intra-epoch validation. These encoders are later FROZEN by k_scaling, so
    # whatever state is selected here propagates into every downstream number.
    # On a large corpus one epoch is many thousands of steps and the model can
    # peak and then collapse to a constant well inside epoch 1, which a
    # once-per-epoch checkpoint never sees. 0 = OFF reproduces the original
    # per-epoch cadence exactly, so existing encoders are unaffected.
    every = max(0, int(getattr(args, "eval_every", 0) or 0))

    def _check(tag):
        nonlocal best_sel, best_auc, best_ap, best_state
        acc, auc, apr = _evaluate(model, val_loader, device)
        sel = apr if args.select_on == "auprc" else auc
        print(f"[pretrain] {tag} | val_acc={acc:.4f} | val_auc={auc:.4f} "
              f"| val_auprc={apr:.4f}", flush=True)
        if not np.isnan(sel) and sel > best_sel:
            best_sel, best_auc, best_ap = sel, auc, apr
            best_state = {
                "encoder_a": {k: v.detach().cpu().clone()
                              for k, v in model.encoder_a.state_dict().items()},
                "encoder_b": {k: v.detach().cpu().clone()
                              for k, v in model.encoder_b.state_dict().items()},
            }
        model.train()

    step = 0
    for ep in range(1, args.epochs + 1):
        model.train()
        run_loss, seen = 0.0, 0
        for xa, xb, _tab, y in train_loader:
            opt.zero_grad()
            logits = model(xa.to(device), xb.to(device))
            loss = loss_fn(logits, y.to(device))
            loss.backward()
            opt.step()
            run_loss += loss.item() * len(y)
            seen += len(y)
            step += 1
            if every and step % every == 0:
                _check(f"epoch {ep:3d}/{args.epochs} step {step:<7d} "
                       f"loss={run_loss/max(seen,1):.4f}")
        _check(f"epoch {ep:3d}/{args.epochs}            "
               f"loss={run_loss/max(seen,1):.4f}")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    torch.save({"encoders": best_state,
                "meta": {"dataset": args.dataset,
                         # Stamped so a checkpoint cannot be silently loaded into a
                         # model built for a different dataset. Shapes usually differ
                         # (12ch/5-class/image vs 18ch/2-class/features) and would
                         # raise, but datasets can share n_channels_a and
                         # would NOT — encoder_a would load and quietly be wrong.
                         "n_channels_a": spec.n_channels_a,
                         "modality_b": spec.modality_b,
                         "feat_b_dim": spec.feat_b_dim,
                         "n_classes": args.n_classes,
                         "select_on": args.select_on,
                         "best_val_auc": best_auc, "best_val_auprc": best_ap,
                         "mode": "public" if args.public_data else "proxy",
                         "n_pretrain": int(len(train_idx)), "epochs": args.epochs}},
               args.output)
    print(f"[pretrain] best val AUC={best_auc:.4f} AUPRC={best_ap:.4f} "
          f"(selected on {args.select_on}) → saved encoders to {args.output}")


if __name__ == "__main__":
    main()
