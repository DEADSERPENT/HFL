"""
make_public_split.py — carve a PUBLIC pretraining pool out of the client data.

THE PROBLEM THIS SOLVES
-----------------------
Head-only DP fine-tuning pretrains the encoders, freezes them, and DP-trains
only the fusion head. The epsilon then covers everything the head saw.

But if the encoders were pretrained on the POOLED CLIENT TRAINING DATA, they
have already seen that data with no privacy protection at all. The reported
epsilon describes the head; it says nothing about what the encoders memorised.
Such a number is an UPPER BOUND on achievable utility, not a guarantee — and
publishing it as a guarantee would be the most serious overstatement available
to this project.

THE FIX
-------
Reserve a set of PATIENTS that no client ever trains on, and pretrain the
encoders only on those. Then:

    encoders   <- public patients only      (no privacy claim needed: public)
    fusion head <- client patients, DP      (epsilon covers exactly this)

and the end-to-end guarantee is valid.

WHY THIS CARVES FROM TRAIN ONLY
-------------------------------
The public pool is taken exclusively from client TRAIN splits. Val and test are
left byte-identical, so every result already measured on the test set stays
directly comparable — the change costs some training data, not comparability.
Taking the pool from test would be far worse than the problem it solves.

WHY IT SPLITS BY CASE
---------------------
A patient contributes ~8 windows. Splitting by window would put the same
patient in both the public pool and a client's training set, which reintroduces
exactly the leak this script exists to remove — the encoders would still have
seen that patient's data. Whole cases move or they do not move.

NOTHING IS PUBLISHED OR EXPOSED
-------------------------------
"Public" here is a term of art from differential privacy: it means "not covered
by the epsilon guarantee", i.e. data the analysis treats as already known to an
adversary. It does NOT mean released, uploaded or shared. Every file this script
writes stays on the local disk, and the underlying dataset is already an open
published corpus (VitalDB, CC BY 3.0). The split exists purely so the privacy
accounting is honest about which records the encoders were allowed to see.

OUTPUT
------
  <partition_dir>/public_indices.npy      pretraining pool (window indices)
  <partition_dir>/device_NN_train.npy     rewritten, public cases removed
  <partition_dir>/public_split_meta.json  provenance and disjointness proof
  <partition_dir>/backup_pre_public/      originals, so this is reversible
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

import numpy as np

_SIM = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIM / "data" / "loaders"))
from datasets import get_spec, REGISTRY                       # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, choices=sorted(REGISTRY))
    ap.add_argument("--public_frac", type=float, default=0.20,
                    help="fraction of TRAIN cases reserved as public (default 0.20)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--restore", action="store_true",
                    help="undo: restore the original train splits and exit")
    a = ap.parse_args()

    spec = get_spec(a.dataset)
    pdir = _SIM / spec.partition_dir
    ddir = _SIM / spec.data_dir
    backup = pdir / "backup_pre_public"

    with open(pdir / "partition_meta.json") as f:
        meta = json.load(f)
    n_dev = meta["n_devices"]

    # ── restore ──────────────────────────────────────────────────────
    if a.restore:
        if not backup.is_dir():
            raise SystemExit("[restore] no backup found — nothing to undo.")
        n = 0
        for f in backup.glob("device_*_train.npy"):
            shutil.copy2(f, pdir / f.name); n += 1
        for f in ("public_indices.npy", "public_split_meta.json"):
            (pdir / f).unlink(missing_ok=True)
        # Metadata must revert too, or it keeps advertising the reduced counts.
        for d in range(n_dev):
            meta["devices"][str(d)]["n_train"] = int(
                len(np.load(pdir / f"device_{d:02d}_train.npy")))
        meta.pop("public_split", None)
        with open(pdir / "partition_meta.json", "w") as f:
            json.dump(meta, f, indent=2)
        print(f"[restore] restored {n} train splits + metadata; public pool removed.")
        return 0

    # ── group identity ───────────────────────────────────────────────
    gpath = ddir / "meta" / "case_ids.npy"
    if not gpath.exists():
        raise SystemExit(
            f"[FATAL] no per-sample group ids at {gpath}.\n"
            f"Without them the pool cannot be split by patient, and a "
            f"window-level split would leave the same patient on both sides — "
            f"which is the leak this script exists to remove.")
    case_ids = np.load(gpath)

    # ── back up originals once ───────────────────────────────────────
    backup.mkdir(exist_ok=True)
    for d in range(n_dev):
        src = pdir / f"device_{d:02d}_train.npy"
        dst = backup / src.name
        if not dst.exists():
            shutil.copy2(src, dst)

    # Always read from the BACKUP so re-running with a different fraction
    # re-derives from the full original data instead of shrinking what is
    # already shrunken.
    train_idx = {d: np.load(backup / f"device_{d:02d}_train.npy")
                 for d in range(n_dev)}

    all_train = np.concatenate([train_idx[d] for d in range(n_dev)])
    train_cases = np.unique(case_ids[all_train])

    rng = np.random.default_rng(a.seed)
    shuffled = train_cases.copy()
    rng.shuffle(shuffled)
    n_pub = int(round(len(shuffled) * a.public_frac))
    public_cases = set(shuffled[:n_pub].tolist())

    public_idx = np.sort(all_train[np.isin(case_ids[all_train],
                                           list(public_cases))])

    print("=" * 74)
    print(f"PUBLIC PRETRAINING SPLIT — {a.dataset}")
    print("=" * 74)
    print(f"  train cases total     : {len(train_cases):,}")
    print(f"  reserved as public    : {n_pub:,} ({100*a.public_frac:.0f} %)")
    print(f"  public windows        : {len(public_idx):,}")

    # ── rewrite client train splits ──────────────────────────────────
    removed_tot = 0
    print(f"\n  {'device':<8}{'before':>10}{'after':>10}{'removed':>10}")
    print("  " + "-" * 38)
    for d in range(n_dev):
        before = train_idx[d]
        keep = before[~np.isin(case_ids[before], list(public_cases))]
        np.save(pdir / f"device_{d:02d}_train.npy", keep)
        removed_tot += len(before) - len(keep)
        print(f"  {d:<8}{len(before):>10,}{len(keep):>10,}"
              f"{len(before)-len(keep):>10,}")
    np.save(pdir / "public_indices.npy", public_idx)

    # ── disjointness proof — the whole point, so it is verified ──────
    new_train = np.concatenate([np.load(pdir / f"device_{d:02d}_train.npy")
                                for d in range(n_dev)])
    overlap_idx = np.intersect1d(public_idx, new_train)
    pub_cases_arr = np.unique(case_ids[public_idx])
    cli_cases_arr = np.unique(case_ids[new_train])
    overlap_case = np.intersect1d(pub_cases_arr, cli_cases_arr)

    val_test = []
    for d in range(n_dev):
        for sp in ("val", "test"):
            f = pdir / f"device_{d:02d}_{sp}.npy"
            if f.exists():
                val_test.append(np.load(f))
    val_test = np.concatenate(val_test) if val_test else np.array([], int)
    overlap_eval_case = np.intersect1d(pub_cases_arr,
                                       np.unique(case_ids[val_test])) \
        if len(val_test) else np.array([])

    print("\n  DISJOINTNESS CHECKS")
    checks = [
        ("public ∩ client-train  (window)", len(overlap_idx)),
        ("public ∩ client-train  (CASE)",   len(overlap_case)),
        ("public ∩ val/test      (CASE)",   len(overlap_eval_case)),
    ]
    ok = True
    for label, n in checks:
        print(f"    {'PASS' if n == 0 else 'FAIL'}  {label:<34} {n}")
        ok &= (n == 0)
    if not ok:
        raise SystemExit("\n[FATAL] disjointness violated — refusing to write a "
                         "public pool that would not support a privacy claim.")

    # Rewrite partition_meta.json so it matches the files on disk. Anything
    # that reads n_train from the metadata (privacy calibration, preflight,
    # reporting) would otherwise silently use pre-split counts — which is
    # exactly how a run breached its own epsilon budget.
    for d in range(n_dev):
        meta["devices"][str(d)]["n_train"] = int(
            len(np.load(pdir / f"device_{d:02d}_train.npy")))
    meta["public_split"] = {
        "applied": True, "public_frac": a.public_frac, "seed": a.seed,
        "n_public_windows": int(len(public_idx)),
        "note": "client train splits reduced; val/test untouched",
    }
    with open(pdir / "partition_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("  partition_meta.json updated to match the files on disk")

    json.dump({
        "dataset": a.dataset, "seed": a.seed, "public_frac": a.public_frac,
        "n_public_cases": int(n_pub), "n_public_windows": int(len(public_idx)),
        "n_client_train_windows_after": int(len(new_train)),
        "n_client_train_windows_removed": int(removed_tot),
        "split_unit": "case (patient)",
        "val_test_modified": False,
        "disjoint_verified": {k: int(v) for k, v in checks},
        "note_on_terminology": ("'public' = outside the epsilon guarantee "
                                "for the DP analysis; nothing is released "
                                "or uploaded — all files are local"),
        "purpose": ("encoders pretrain ONLY on public_indices.npy so the "
                    "reported epsilon is a valid end-to-end guarantee rather "
                    "than an upper bound"),
    }, open(pdir / "public_split_meta.json", "w"), indent=2)

    print(f"\n  client train windows: {len(all_train):,} -> {len(new_train):,} "
          f"({100*removed_tot/len(all_train):.1f} % moved to public)")
    print(f"  val/test: UNCHANGED — every previously measured test result stays "
          f"comparable")
    print(f"\n  written: {pdir/'public_indices.npy'}")
    print(f"  backup : {backup}   (undo with --restore)")
    print("\n  NEXT:")
    print(f"    python model/training/pretrain_encoders.py --dataset {a.dataset} \\")
    print(f"        --public_data {pdir/'public_indices.npy'} \\")
    print(f"        --output checkpoints/pretrained_encoders_{a.dataset}_public.pt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
