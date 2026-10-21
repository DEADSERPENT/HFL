#!/usr/bin/env python3
"""
One driver for the eICU k-scaling programme (pre-registration P1).

Runs, in order, skipping any stage whose artefact already exists:

  1. make_public_split  — carve a pretraining pool disjoint from every FL
                          client's train data, and rewrite the partitions.
  2. pretrain_encoders  — RIGOROUS mode on that disjoint pool. The encoders are
                          FROZEN by stage 3, so this state propagates into every
                          downstream number; --eval_every guards against
                          selecting a collapsed model on a long epoch.
  3. k_scaling          — the frozen operating point from
                          document/01_planning/PREREGISTRATION_EICU.md §3.

Nothing here is hardcoded: paths and sizes resolve from the dataset registry
and from partition_meta.json, so the same driver works for any registered
dataset via --dataset.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

_SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_SIM / "data" / "loaders"))
from datasets import get_spec, REGISTRY          # noqa: E402


def sh(cmd, tag):
    print(f"\n{'=' * 74}\n  ▶ {tag}\n{'=' * 74}\n  $ " +
          " ".join(str(c) for c in cmd[1:]), flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=_SIM)
    if r.returncode != 0:
        sys.exit(f"[driver] FAILED at {tag} (exit {r.returncode})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="eicu", choices=sorted(REGISTRY))
    # Pre-registered operating point (§3). Defaults ARE the frozen values.
    ap.add_argument("--k", type=int, nargs="+", default=[1, 2, 4, 8, 16, 32])
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--epsilon", type=float, default=0.80)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--tau_e", type=int, default=5)
    ap.add_argument("--public_frac", type=float, default=0.20)
    ap.add_argument("--pretrain_epochs", type=int, default=30)
    ap.add_argument("--eval_every", type=int, default=250,
                    help="intra-epoch validation cadence for pretraining")
    ap.add_argument("--force", action="store_true",
                    help="redo stages even if their artefact exists")
    a = ap.parse_args()

    spec = get_spec(a.dataset)
    pdir = _SIM / spec.partition_dir
    pub = pdir / "public_indices.npy"
    enc = _SIM / "checkpoints" / f"pretrained_encoders_{a.dataset}.pt"
    py = sys.executable

    n_dev = json.loads((pdir / "partition_meta.json").read_text())["n_devices"]
    print(f"[driver] {a.dataset}: {n_dev} clients, partitions at {pdir}")

    # 1 ── disjoint public pool
    if a.force or not pub.exists():
        sh([py, _SIM / "scripts" / "make_public_split.py",
            "--dataset", a.dataset,
            "--public_frac", a.public_frac,
            "--seed", a.seeds[0]], "make_public_split")
    else:
        print(f"[driver] ⊙ public split cached: {pub}")

    # 2 ── encoders, RIGOROUS mode on the disjoint pool
    if a.force or not enc.exists():
        sh([py, _SIM / "model" / "training" / "pretrain_encoders.py",
            "--dataset", a.dataset,
            "--public_data", pub,
            "--epochs", a.pretrain_epochs,
            "--batch_size", a.batch_size,
            "--eval_every", a.eval_every,
            "--output", enc], "pretrain_encoders (RIGOROUS)")
    else:
        print(f"[driver] ⊙ encoders cached: {enc}")

    # 3 ── k-scaling at the frozen operating point
    sh([py, _SIM / "scripts" / "k_scaling.py",
        "--dataset", a.dataset,
        "--k", *a.k,
        "--seeds", *a.seeds,
        "--epsilon", a.epsilon,
        "--batch_size", a.batch_size,
        "--rounds", a.rounds,
        "--tau_e", a.tau_e], "k_scaling")

    print("\n[driver] all stages complete.")


if __name__ == "__main__":
    main()
