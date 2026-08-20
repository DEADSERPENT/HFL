#!/usr/bin/env python
"""
mia_difficulty_floor.py — the confound floor every MIA number must be read against.

WHY THIS EXISTS
---------------
A patient-level membership attack is scored on members drawn from the released
TRAIN patients and non-members drawn from the released TEST patients. That is
the natural construction, and it carries a trap: if the two pools differ in
intrinsic difficulty, an attack is rewarded for detecting difficulty rather
than membership, and its AUC overstates leakage.

The floor measures exactly that. For every evaluated patient it takes `mo`, the
mean statistic over the shadows in which that patient was NOT a member, and
ranks patients by it. This uses NO target model. Shadow membership is drawn
uniformly over the whole patient universe, so a difficulty-balanced split must
score 0.5. Whatever it scores above 0.5 is a property of how the split was
drawn, and no attack should be credited for it.

Measured on the eps=16 record arm the floor is 0.5731, while the loss-threshold
attack on the same arm is 0.5465 — the attack is BELOW the floor, so it carries
no membership signal at all. Reporting 0.5465 against 0.5 would have implied
the opposite.

The floor is now emitted by `lira_attack.py` for every new run. This script
recovers it for arms that were scored before that change, without retraining
anything: shadow scores and the membership matrix are already on disk.

Usage
-----
    python scripts/mia_difficulty_floor.py --dataset vitaldb
    python scripts/mia_difficulty_floor.py --dataset vitaldb \
        --roots results/phase5/lira/vitaldb results/phase5/lira_eps/vitaldb/eps16.0
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_SIM = _HERE.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_SIM / "data" / "loaders"))

from lira_attack import (REGISTRY, auc_scores, get_spec, load_partition,  # noqa: E402
                         mean_ci, patient_table)


def eval_patients(dataset: str, max_patients: int):
    """Rebuild the evaluated member/non-member lists.

    Reproduced from lira_attack.main by importing the same helpers and using
    the same generator seed, so the two cannot drift apart. If the released
    partition is ever repartitioned this returns different patients — which is
    correct, because the recorded AUCs would refer to different patients too.
    """
    spec = get_spec(dataset)
    case_ids = np.load(_SIM / spec.data_dir / "meta" / "case_ids.npy")
    pdir = _SIM / spec.partition_dir
    meta = json.load(open(pdir / "partition_meta.json"))
    part = load_partition(pdir, meta["n_devices"])
    windows, _dev_of, split_of = patient_table(part, case_ids)

    mem_pool = sorted(c for c, sp in split_of.items() if sp == "train")
    non_pool = sorted(c for c, sp in split_of.items() if sp == "test")
    rng = np.random.default_rng(0)
    n = min(max_patients, len(mem_pool), len(non_pool))
    mem = [int(c) for c in rng.choice(mem_pool, n, replace=False)]
    non = [int(c) for c in rng.choice(non_pool, n, replace=False)]
    return mem + non, np.r_[np.ones(len(mem)), np.zeros(len(non))]


def floor_for_arm(arm_root: Path, eval_pat, y_true):
    """AUC of the difficulty floor for one arm, or None if not scorable."""
    mfile = arm_root / "membership.npz"
    if not mfile.exists():
        return None, "no membership.npz"

    shadows = sorted(d for d in arm_root.iterdir()
                     if d.is_dir() and (d / "scores.npz").exists())
    if len(shadows) < 4:
        return None, f"only {len(shadows)} scored shadows"

    phi = np.array([np.load(d / "scores.npz")["phi"] for d in shadows])

    z = np.load(mfile)
    pos = {int(c): i for i, c in enumerate(z["patients"])}
    missing = [c for c in eval_pat if c not in pos]
    if missing:
        return None, f"{len(missing)} evaluated patients absent from mask"
    in_mask = z["mask"][:len(shadows), [pos[c] for c in eval_pat]]

    if phi.shape[1] != len(eval_pat):
        return None, (f"shadow scores cover {phi.shape[1]} patients but "
                      f"{len(eval_pat)} were evaluated")

    # mo — mean over the shadows in which the patient was NOT a member.
    mo = np.full(phi.shape[1], np.nan)
    for p in range(phi.shape[1]):
        vo = phi[~in_mask[:, p], p]
        vo = vo[~np.isnan(vo)]
        if len(vo):
            mo[p] = vo.mean()
    if not np.isfinite(mo).all():
        mo = np.where(np.isfinite(mo), mo, np.nanmean(mo))

    return auc_scores(y_true, mo), f"{len(shadows)} shadows"


def recorded_attacks(arm_root: Path):
    """Best recorded attack AUC for this arm, read from the run's own CSV."""
    csvs = list(arm_root.parent.parent.glob("lira_*.csv")) + \
           list(arm_root.parent.parent.glob("*/lira_*.csv"))
    arm = arm_root.name
    per: dict[str, list[float]] = {}
    for f in csvs:
        for row in csv.DictReader(open(f)):
            if row.get("arm") != arm:
                continue
            try:
                per.setdefault(row["attack"], []).append(float(row["attack_auc"]))
            except (KeyError, ValueError):
                continue
    per.pop("difficulty", None)
    if not per:
        return None, None
    name, vals = max(per.items(), key=lambda kv: np.mean(kv[1]))
    return name, float(np.mean(vals))


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="vitaldb", choices=sorted(REGISTRY))
    ap.add_argument("--roots", nargs="+", default=None,
                    help="LiRA output dirs (each containing shadows/<arm>/). "
                         "Default: every lira* tree for the dataset.")
    ap.add_argument("--max_patients", type=int, default=600,
                    help="must match the value the attacks were scored with")
    ap.add_argument("--out", default=None,
                    help="optional CSV to write")
    a = ap.parse_args()

    if a.roots:
        roots = [Path(r) if Path(r).is_absolute() else _SIM / r for r in a.roots]
    else:
        base = _SIM / "results" / "phase5"
        roots = sorted({p.parent for p in base.glob(f"lira*/**/shadows")
                        if (p).is_dir()})

    eval_pat, y_true = eval_patients(a.dataset, a.max_patients)
    print("=" * 78)
    print(f"  DIFFICULTY FLOOR — {a.dataset}")
    print("=" * 78)
    print(f"  evaluated: {int(y_true.sum())} members + "
          f"{int(len(y_true) - y_true.sum())} non-members")
    print("  floor uses NO target model — shadow difficulty only.")
    print("  A difficulty-balanced split scores 0.5. An attack only shows")
    print("  memorisation if it exceeds the floor, not merely 0.5.\n")
    print(f"  {'arm':<28}{'floor':>9}{'best attack':>22}{'margin':>10}")
    print("  " + "-" * 69)

    rows = []
    for root in roots:
        sroot = root / "shadows"
        if not sroot.is_dir():
            continue
        for arm_root in sorted(d for d in sroot.iterdir() if d.is_dir()):
            label = f"{root.name}/{arm_root.name}"
            floor, note = floor_for_arm(arm_root, eval_pat, y_true)
            if floor is None:
                print(f"  {label:<28}{'—':>9}   ({note})")
                continue
            name, best = recorded_attacks(arm_root)
            if best is None:
                print(f"  {label:<28}{floor:>9.4f}{'(no CSV)':>22}{'':>10}")
                rows.append({"arm": label, "floor": floor,
                             "best_attack": "", "best_auc": "", "margin": ""})
                continue
            margin = best - floor
            flag = "  NO SIGNAL" if margin <= 0 else ""
            print(f"  {label:<28}{floor:>9.4f}"
                  f"{f'{best:.4f} ({name})':>22}{margin:>+10.4f}{flag}")
            rows.append({"arm": label, "floor": round(floor, 4),
                         "best_attack": name, "best_auc": round(best, 4),
                         "margin": round(margin, 4)})

    if a.out and rows:
        out = Path(a.out) if Path(a.out).is_absolute() else _SIM / a.out
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\n  written: {out.relative_to(_SIM)}")


if __name__ == "__main__":
    main()
