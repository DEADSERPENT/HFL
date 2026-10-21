#!/usr/bin/env python3
"""
N1 — does the clip actually bind, and does normalisation stop it binding?

Measures the pre-registered mechanism check for claim N-D directly, through the
same `patient_level_dp_train` code path the experiment uses, rather than
inferring it from utility. Saturation is a property of the clipping arithmetic
on real per-patient gradients, so a handful of steps measures it exactly; a full
training run is not needed and would not measure it any better.

Reports, per clip_norm mode, the fraction of per-patient gradients whose norm
exceeded C and was therefore truncated.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np, torch

_SIM = Path(__file__).resolve().parents[1]
for sub in ("data/loaders", "model/architecture", "model/privacy", "model/utils"):
    sys.path.insert(0, str(_SIM / sub))
from datasets import get_spec, REGISTRY                      # noqa: E402
from hfl_mm_model import build_hfl_mm_hc                      # noqa: E402
from patient_dp import (group_indices_by_patient,             # noqa: E402
                        patient_level_dp_train)
from device_utils import get_device, set_seed                 # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="vitaldb", choices=sorted(REGISTRY))
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device_id", type=int, nargs="+", default=[0],
                    help="client(s) to probe. On eICU pick clients with real "
                         "spread — device 0 holds 15 patients at sd 2.3 and "
                         "would understate the effect.")
    ap.add_argument("--partition_dir", default=None,
                    help="default is the k-scaling partition for --k. Pass the "
                         "registry partition to probe the NATURAL window "
                         "distribution, which is where k-heterogeneity lives.")
    ap.add_argument("--max_grad_norm", type=float, default=1.0)
    ap.add_argument("--patients_per_batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    a = ap.parse_args()

    spec = get_spec(a.dataset)
    dev = get_device()
    set_seed(a.seed)
    full_ds = spec.build_full(spec.data_dir)
    cids = np.load(_SIM / spec.data_dir / "meta" / "case_ids.npy")

    pdir = (Path(a.partition_dir) if a.partition_dir else
            _SIM / "results/phase5/k_scaling" / a.dataset / f"k{a.k}_seed{a.seed}")
    if not pdir.is_absolute():
        pdir = _SIM / pdir
    groups = []
    for d in a.device_id:
        tr = np.load(pdir / f"device_{d:02d}_train.npy")
        groups.extend(group_indices_by_patient(tr, cids))
    sizes = np.array([len(g) for g in groups])
    print(f"  partitions: {pdir}")
    print(f"  clients {a.device_id}: {len(groups)} patients, windows/patient "
          f"min {sizes.min()} median {int(np.median(sizes))} mean {sizes.mean():.1f} "
          f"max {sizes.max()} sd {sizes.std():.2f}")
    if sizes.std() < 1.5:
        print("  WARNING: window counts are near-constant here, so there is no "
              "k-dependence for N-D to correct. N1 cannot hold on this split.")

    enc = _SIM / "checkpoints" / f"pretrained_encoders_{a.dataset}.pt"
    print(f"  encoders: {enc.name}   C = {a.max_grad_norm}\n")

    print("  mode      clip_saturation   reading")
    print("  " + "-" * 54)
    out = {}
    for mode in ("none", "k", "sqrt_k"):
        set_seed(a.seed)
        model = build_hfl_mm_hc(n_classes=spec.n_classes,
                                modality_b=spec.modality_b,
                                feat_b_dim=spec.feat_b_dim,
                                n_channels_a=spec.n_channels_a).to(dev)
        if enc.exists():
            ck = torch.load(enc, map_location=dev, weights_only=False)
            st = ck.get("encoders", ck)
            model.encoder_a.load_state_dict(st["encoder_a"])
            model.encoder_b.load_state_dict(st["encoder_b"])
        for p_ in model.encoder_a.parameters(): p_.requires_grad = False
        for p_ in model.encoder_b.parameters(): p_.requires_grad = False

        r = patient_level_dp_train(
            model, full_ds, groups, dev,
            noise_multiplier=1.0,            # irrelevant to saturation
            max_grad_norm=a.max_grad_norm,
            lr=a.lr, n_epochs=1,
            patients_per_batch=a.patients_per_batch,
            clip_norm=mode)
        s = r["clip_saturation"]
        out[mode] = s
        note = ("clip binds on most patients" if s > 0.5 else
                "clip rarely binds" if s < 0.10 else "clip binds sometimes")
        print(f"  {mode:8s}  {s:14.4f}   {note}")

    print()
    n1 = out["none"] > 0.50 and out["k"] < 0.10
    print(f"  N1 (saturation >0.50 under none AND <0.10 under k): "
          f"{'HELD' if n1 else 'NOT HELD'}")
    p = _SIM / "results/phase5/nd_clipnorm" / a.dataset / f"clip_saturation_{'natural' if a.partition_dir else 'k'+str(a.k)}_seed{a.seed}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"dataset": a.dataset, "k": a.k, "seed": a.seed,
                             "max_grad_norm": a.max_grad_norm,
                             "n_patients": len(groups), "partition_dir": str(pdir),
                             "windows_per_patient_sd": float(sizes.std()),
                             "saturation": out, "N1_held": bool(n1)}, indent=2))
    print(f"  written: {p}")


if __name__ == "__main__":
    main()
