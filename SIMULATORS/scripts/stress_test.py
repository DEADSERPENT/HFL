"""
stress_test — long-running leak / slowdown detector for the HFL hot path.

Replays the trainer's per-device inner step (build model → load global state →
train a few batches → discard) for many iterations while sampling process RSS
and GPU VRAM. Fits a linear trend over iterations: a near-zero slope means no
leak; a positive slope flags a leak or unbounded cache growth. Also tracks
per-iteration wall time to catch gradual slowdown.

This does NOT change training behavior — it exercises the same code paths the
real run uses, purely to observe stability under repetition.

Usage:
    python scripts/stress_test.py --iters 60 --batches 3
"""

import os
import sys
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data", "loaders"))

# Module scope: --dataset choices resolve from the registry, so REGISTRY
# must be importable here, not only inside a function.
from datasets import REGISTRY                                   # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import torch
import torch.nn as nn

from engineering.sysmon import sample_resources


def _linfit_slope(xs, ys):
    """Least-squares slope of ys vs xs (per-iteration drift)."""
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    mask = np.isfinite(ys)
    if mask.sum() < 2:
        return float("nan")
    xs, ys = xs[mask], ys[mask]
    return float(np.polyfit(xs, ys, 1)[0])


def main():
    ap = argparse.ArgumentParser(description="HFL hot-path stress test")
    ap.add_argument("--dataset", default="vitaldb",
                    choices=sorted(REGISTRY))
    ap.add_argument("--data_dir", default=None, help="override registry path")
    ap.add_argument("--part_dir", default=None, help="override registry path")
    ap.add_argument("--iters", type=int, default=60,
                    help="Number of build→train→discard cycles")
    ap.add_argument("--batches", type=int, default=3,
                    help="Train batches per cycle")
    ap.add_argument("--batch_size", type=int, default=32)
    ap.add_argument("--n_classes", type=int, default=None, help="override registry")
    ap.add_argument("--output", default="results/monitoring/stress_test.csv")
    args = ap.parse_args()

    from hfl_trainer import load_partitioned_data
    from hfl_mm_model import build_hfl_mm_hc
    from device_utils import get_device, optimize_gpu
    from datasets import get_spec

    # Every shape/path/count comes from the registry so this harness profiles
    # the model that actually trains, not a differently-shaped stand-in.
    spec = get_spec(args.dataset)
    args.data_dir = args.data_dir or spec.data_dir
    args.part_dir = args.part_dir or spec.partition_dir
    args.n_classes = args.n_classes or spec.n_classes
    _kw = {"n_channels_a": spec.n_channels_a}
    if spec.modality_b != "image":
        _kw.update(modality_b="features", feat_b_dim=spec.feat_b_dim)
    print(f"[{'stress'}] dataset={spec.name} classes={spec.n_classes} "
          f"ch_a={spec.n_channels_a} mod_b={spec.modality_b}")

    device = get_device()
    optimize_gpu()

    # Shared dataset (verifies the C1 fix holds under the stress harness too).
    full_ds = spec.build_full(args.data_dir)
    loaders = load_partitioned_data(args.part_dir, args.data_dir, 0,
                                    args.batch_size, full_ds=full_ds)
    train_loader = loaders["train"]
    loss_fn = nn.CrossEntropyLoss()

    # A single "global state" to load each cycle (mimics the FL round).
    ref_model = build_hfl_mm_hc(n_classes=args.n_classes, **_kw).to(device)
    global_state = {k: v.clone() for k, v in ref_model.state_dict().items()}
    del ref_model

    print(f"Stress test: {args.iters} cycles × {args.batches} batches "
          f"on {device.type}")
    print(f"{'iter':>5} {'rss_gb':>8} {'vram_res_gb':>12} {'iter_s':>8}")

    rows, rss_series, vram_series, time_series = [], [], [], []
    for it in range(args.iters):
        t0 = time.time()

        # --- replay trainer inner step ---
        local = build_hfl_mm_hc(n_classes=args.n_classes, **_kw).to(device)
        local.load_state_dict(global_state)
        opt = torch.optim.Adam(local.parameters(), lr=1e-3)
        local.train()
        seen = 0
        for bi, (ecg, cxr, _tab, labels) in enumerate(train_loader):
            if bi >= args.batches:
                break
            opt.zero_grad()
            out = local(ecg.to(device, non_blocking=True),
                        cxr.to(device, non_blocking=True))
            loss = loss_fn(out, labels.to(device, non_blocking=True))
            loss.backward()
            opt.step()
            seen += len(labels)
        del local, opt
        if device.type == "cuda":
            torch.cuda.empty_cache()
        # --- end step ---

        dt = time.time() - t0
        s = sample_resources(".")
        rss_series.append(s["rss_gb"])
        vram_series.append(s["vram_reserved_gb"])
        time_series.append(dt)
        rows.append({"iter": it, "rss_gb": s["rss_gb"],
                     "vram_reserved_gb": s["vram_reserved_gb"],
                     "iter_s": round(dt, 4), "samples": seen})
        if it % max(1, args.iters // 12) == 0 or it == args.iters - 1:
            print(f"{it:5d} {s['rss_gb']:8.3f} {s['vram_reserved_gb']:12.3f} "
                  f"{dt:8.3f}")

    # --- trend analysis ---
    iters = list(range(args.iters))
    rss_slope = _linfit_slope(iters, rss_series)      # GB / iter
    vram_slope = _linfit_slope(iters, vram_series)    # GB / iter
    # slowdown: compare last-third mean vs first-third mean iter time
    third = max(1, args.iters // 3)
    t_first = float(np.mean(time_series[:third]))
    t_last = float(np.mean(time_series[-third:]))
    slowdown_pct = (t_last - t_first) / max(t_first, 1e-9) * 100

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    import csv
    with open(args.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)

    # Leak thresholds: >5 MB/iter RSS growth or >2 MB/iter VRAM growth is
    # suspicious over a long run; >20% iter-time growth flags slowdown.
    rss_leak = rss_slope > 0.005
    vram_leak = vram_slope > 0.002
    slow = slowdown_pct > 20.0

    print("\n" + "=" * 58)
    print("STRESS TEST TREND ANALYSIS")
    print("=" * 58)
    print(f"  RSS slope        : {rss_slope*1000:+.3f} MB/iter   "
          f"[{'LEAK?' if rss_leak else 'OK'}]")
    print(f"  VRAM slope       : {vram_slope*1000:+.3f} MB/iter   "
          f"[{'LEAK?' if vram_leak else 'OK'}]")
    print(f"  Peak RSS         : {max(rss_series):.3f} GB")
    print(f"  Peak VRAM (resv) : {max(vram_series):.3f} GB")
    print(f"  Iter time first→last third: {t_first:.3f}s → {t_last:.3f}s "
          f"({slowdown_pct:+.1f}%)  [{'SLOWDOWN?' if slow else 'OK'}]")
    print(f"  Samples per cycle: {rows[0]['samples']}")
    print("=" * 58)
    verdict = "PASS" if not (rss_leak or vram_leak or slow) else "REVIEW"
    print(f"  VERDICT: {verdict}   (CSV → {args.output})")
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
