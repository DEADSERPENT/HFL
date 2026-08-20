"""
profile_model — per-stage timing + throughput for the HFL training step.

Measures wall time of data loading, forward, backward, and optimizer step
using proper CUDA synchronization (so GPU-async work is attributed correctly),
then reports samples/sec and a per-stage breakdown. Observability only —
does not alter the model or training math.

Usage:
    python scripts/profile_model.py --batches 20 --batch_size 32
"""

import os
import sys
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data", "loaders"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import torch
import torch.nn as nn


def _sync(device):
    if device.type == "cuda":
        torch.cuda.synchronize()


def main():
    ap = argparse.ArgumentParser(description="Profile HFL training step")
    ap.add_argument("--dataset", default="vitaldb",
                    choices=["wear", "vitaldb"])
    ap.add_argument("--data_dir", default=None, help="override registry path")
    ap.add_argument("--part_dir", default=None, help="override registry path")
    ap.add_argument("--batches", type=int, default=20)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--batch_size", type=int, default=32)
    ap.add_argument("--n_classes", type=int, default=None, help="override registry")
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
    print(f"[{'profile'}] dataset={spec.name} classes={spec.n_classes} "
          f"ch_a={spec.n_channels_a} mod_b={spec.modality_b}")

    device = get_device()
    optimize_gpu()

    full = spec.build_full(args.data_dir)
    loaders = load_partitioned_data(args.part_dir, args.data_dir, 0,
                                    args.batch_size, full_ds=full)
    train = loaders["train"]

    model = build_hfl_mm_hc(n_classes=args.n_classes, **_kw).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    model.train()

    stages = {"data": [], "forward": [], "backward": [], "optimizer": []}
    n_seen = 0
    it = iter(train)
    total_batches = args.warmup + args.batches

    for i in range(total_batches):
        t0 = time.perf_counter()
        try:
            ecg, cxr, _tab, labels = next(it)
        except StopIteration:
            it = iter(train)
            ecg, cxr, _tab, labels = next(it)
        ecg = ecg.to(device, non_blocking=True)
        cxr = cxr.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        _sync(device); t1 = time.perf_counter()

        out = model(ecg, cxr)
        loss = loss_fn(out, labels)
        _sync(device); t2 = time.perf_counter()

        opt.zero_grad()
        loss.backward()
        _sync(device); t3 = time.perf_counter()

        opt.step()
        _sync(device); t4 = time.perf_counter()

        if i >= args.warmup:
            stages["data"].append(t1 - t0)
            stages["forward"].append(t2 - t1)
            stages["backward"].append(t3 - t2)
            stages["optimizer"].append(t4 - t3)
            n_seen += len(labels)

    def ms(x): return np.mean(x) * 1000
    per_batch_s = sum(np.mean(v) for v in stages.values())
    throughput = args.batch_size / per_batch_s if per_batch_s > 0 else 0.0

    print("\n" + "=" * 56)
    print(f"MODEL PROFILE  (device={device.type}, batch={args.batch_size}, "
          f"{args.batches} batches)")
    print("=" * 56)
    print(f"{'stage':<12} {'mean_ms':>10} {'% of step':>10}")
    print("-" * 56)
    total_ms = per_batch_s * 1000
    for name in ("data", "forward", "backward", "optimizer"):
        m = ms(stages[name])
        print(f"{name:<12} {m:>10.2f} {m/total_ms*100:>9.1f}%")
    print("-" * 56)
    print(f"{'step total':<12} {total_ms:>10.2f} {'100.0%':>10}")
    print(f"\n  Throughput : {throughput:,.0f} samples/sec")
    print(f"  Params     : {sum(p.numel() for p in model.parameters()):,}")
    if device.type == "cuda":
        print(f"  Peak VRAM  : {torch.cuda.max_memory_reserved()/1e9:.2f} GB")
    print("=" * 56)


if __name__ == "__main__":
    main()
