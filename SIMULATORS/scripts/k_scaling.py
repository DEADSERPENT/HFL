"""
k_scaling.py — how does the cost of a patient-level guarantee scale with the
number of records each patient contributes?

THE QUESTION
------------
Patient-level DP clips a patient's SUMMED gradient to C, so one patient can
move the aggregate by at most C no matter how many windows they contributed.
Record-level DP clips each window to C, so a patient with k windows can move it
by up to kC. The gap between the two guarantees must therefore grow with k.

Phase 5 measured that gap at ONE value of k (the cohort mean, 7.79 windows per
patient) and reported a single number. A single number cannot distinguish "this
is what a patient-level guarantee costs" from "this is what it costs on this
particular cohort". Measuring the cost as a CURVE in k turns an observation
into a scaling law, and it is the difference between a result that transfers to
other datasets and one that does not.

THE BUILT-IN VALIDITY CHECK
---------------------------
At k=1 a patient IS a record. The per-patient sum is a single per-sample
gradient, so the two arms are the same algorithm and MUST produce the same
result up to seed noise. If they do not collapse at k=1, something in the
experiment is wrong and every other point on the curve is suspect. This is
the k-scaling analogue of the positive control in the membership-inference
work: a condition the experiment has to satisfy before its findings are
admissible.

Making that check meaningful requires one deviation from the Phase 5 recipe.
There, `--batch_size 64` sampled 64 WINDOWS for the record-level arm while
`--patients_per_batch 32` sampled 32 PATIENTS for the patient-level arm. Those
are different sampling rates, so the two arms would differ at k=1 for a purely
mechanical reason and the collapse check would fail without telling us
anything. Here both arms sample the SAME NUMBER OF UNITS per step
(`--batch_size` = `--patients_per_batch`), which makes them identical at k=1
by construction.

WHAT IS AND IS NOT CONTROLLED
-----------------------------
Subsampling to k windows per patient also shrinks the training set, so
absolute utility falls as k falls. That is expected and is NOT the quantity of
interest. The quantity of interest is the DIFFERENCE between the two arms at
each k, and at a given k both arms see exactly the same data, the same
partition and the same seed. The difference is therefore clean even though the
levels are not comparable across k.

Only the TRAIN split is subsampled. Validation and test are left whole, so
every point on the curve is evaluated on the same held-out data and the
utilities are measured against a fixed target.

OUTPUT
------
results/phase5/k_scaling/<dataset>/k_scaling_<dataset>.csv, one row per
(k, arm, seed), plus a printed curve of the paired gap with confidence
intervals and the k=1 collapse verdict.
"""

import os
import sys
import csv
import json
import argparse
import subprocess
from pathlib import Path

import numpy as np

_SIM = Path(__file__).resolve().parent.parent
for _s in ("data/loaders", "scripts"):
    sys.path.insert(0, str(_SIM / _s))

from datasets import get_spec, REGISTRY                          # noqa: E402
from run_statistics import mean_ci, paired_test                  # noqa: E402


# ── partitions: cap every patient at k training windows ─────────────────────

def build_k_partition(spec, meta, case_ids, k, seed, out: Path):
    """Write a partition in which each patient contributes at most k windows.

    Selection is random per patient rather than "the first k", because windows
    are time-ordered within a case: taking the first k would systematically
    sample the start of every operation and confound k with intraoperative
    phase.
    """
    pdir = _SIM / spec.partition_dir
    n_dev = meta["n_devices"]
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed * 1000 + k)

    kept_meta = json.loads(json.dumps(meta))
    total_kept = 0
    for d in range(n_dev):
        tr = np.load(pdir / f"device_{d:02d}_train.npy")
        cids = case_ids[tr]
        keep = []
        for c in np.unique(cids):
            idx = tr[cids == c]
            keep.append(idx if len(idx) <= k
                        else rng.choice(idx, k, replace=False))
        kept = np.sort(np.concatenate(keep)) if keep else np.array([], int)
        np.save(out / f"device_{d:02d}_train.npy", kept)
        total_kept += len(kept)
        kept_meta["devices"][str(d)]["n_train"] = int(len(kept))

        # val/test are copied untouched: the evaluation target must not move
        # with k, or utility differences across k become uninterpretable.
        for sp in ("val", "test"):
            src = pdir / f"device_{d:02d}_{sp}.npy"
            if src.exists():
                np.save(out / f"device_{d:02d}_{sp}.npy", np.load(src))

    kept_meta["k_scaling"] = {"k": k, "seed": seed,
                              "n_train_windows": int(total_kept),
                              "note": "train subsampled to <=k windows per "
                                      "patient; val/test untouched"}
    kept_meta.pop("public_split", None)
    with open(out / "partition_meta.json", "w") as f:
        json.dump(kept_meta, f, indent=2)
    return total_kept


def final_test_metrics(log_path: Path):
    """Parse the trainer's unbiased test line.

    The per-round CSV holds val_* columns only, and the trainer selects its
    best round on val AUC, so reading those would report the quantity that was
    optimised. The `Final Test` line is the held-out one.
    """
    if not log_path.exists():
        return {}
    for line in reversed(log_path.read_text().splitlines()):
        if "Final Test" in line:
            out = {}
            for tok, key in (("AUROC=", "auroc"), ("AUPRC=", "auprc"),
                             ("Acc=", "acc")):
                if tok in line:
                    try:
                        out[key] = float(line.split(tok)[1].split()[0])
                    except (ValueError, IndexError):
                        pass
            return out
    return {}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="vitaldb", choices=sorted(REGISTRY))
    ap.add_argument("--k", type=int, nargs="+", default=[1, 2, 4, 8])
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--arms", nargs="+", default=["sample", "patient"])
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--tau_e", type=int, default=5)
    ap.add_argument("--epsilon", type=float, default=1.0)
    ap.add_argument("--epsilon_conf", type=float, default=0.20,
                    help="Budget per conformal calibration call, composed into "
                         "the reported total. hfl_trainer defaults this to 0.5, "
                         "which with --epsilon 1.0 composes to 1.49 and FAILS "
                         "the eps<=1 objective; runs before 2026-09-21 inherited "
                         "that default because this script never passed the flag. "
                         "The default here is the pre-registered operating point.")
    ap.add_argument("--batch_size", type=int, default=32,
                    help="units per step. Deliberately used for BOTH "
                         "--batch_size and --patients_per_batch so the two "
                         "arms sample the same number of units and collapse "
                         "at k=1 by construction.")
    ap.add_argument("--out_dir", default=None)
    ap.add_argument("--dry_run", action="store_true")
    ap.add_argument("--collect_only", action="store_true",
                    help="skip training, just re-read what is on disk")
    a = ap.parse_args()

    sys.stdout.reconfigure(line_buffering=True)
    spec = get_spec(a.dataset)
    out_root = Path(a.out_dir) if a.out_dir else (
        _SIM / "results" / "phase5" / "k_scaling" / a.dataset)
    if not out_root.is_absolute():
        out_root = _SIM / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    cid = _SIM / spec.data_dir / "meta" / "case_ids.npy"
    if not cid.exists():
        raise SystemExit(f"[FATAL] no case ids at {cid}: k is defined per "
                         f"patient, so patient identity is required.")
    case_ids = np.load(cid)
    meta = json.loads(((_SIM / spec.partition_dir) / "partition_meta.json").read_text())
    enc = _SIM / "checkpoints" / f"pretrained_encoders_{a.dataset}.pt"

    print("=" * 74)
    print(f"k-SCALING — {a.dataset}   k={a.k}  seeds={a.seeds}  arms={a.arms}")
    print("=" * 74)
    print(f"  units per step: {a.batch_size} (both arms)   "
          f"eps_train={a.epsilon}  eps_conf={a.epsilon_conf}  "
          f"total<={a.epsilon + a.epsilon_conf:.2f}")
    print(f"  output: {out_root}\n")

    rows = []
    for k in a.k:
        for seed in a.seeds:
            pdir = out_root / f"k{k}_seed{seed}"
            if not (pdir / "partition_meta.json").exists() and not a.collect_only:
                n = build_k_partition(spec, meta, case_ids, k, seed, pdir)
                print(f"  [part] k={k} seed={seed}: {n:,} train windows")

            for arm in a.arms:
                ck = pdir / f"ckpt_{arm}.pt"
                hist = pdir / f"hist_{arm}.csv"
                log = pdir / f"{arm}.log"

                if not ck.exists() and not a.collect_only:
                    cmd = [sys.executable,
                           str(_SIM / "model" / "training" / "hfl_trainer.py"),
                           "--dataset", a.dataset,
                           "--rounds", str(a.rounds), "--tau_e", str(a.tau_e),
                           "--epsilon", str(a.epsilon),
                           "--epsilon_conf", str(a.epsilon_conf),
                           "--batch_size", str(a.batch_size),
                           "--patients_per_batch", str(a.batch_size),
                           "--dp_unit", arm,
                           "--freeze_encoders",
                           "--pretrained_encoders", str(enc.relative_to(_SIM)),
                           "--partition_dir", str(pdir.relative_to(_SIM)),
                           "--seed", str(seed),
                           "--save_checkpoint", str(ck.relative_to(_SIM)),
                           "--output", str(hist.relative_to(_SIM)),
                           "--no_monitor"]
                    print(f"  [run ] k={k} seed={seed} arm={arm}")
                    if a.dry_run:
                        print("        $ " + " ".join(cmd[1:]))
                        continue
                    with open(log, "w") as lf:
                        r = subprocess.run(cmd, cwd=_SIM, stdout=lf,
                                           stderr=subprocess.STDOUT)
                    if r.returncode != 0 or not ck.exists():
                        print(f"        FAILED (exit {r.returncode}) — see {log}")
                        continue

                m = final_test_metrics(log)
                if m:
                    rows.append({"dataset": a.dataset, "k": k, "seed": seed,
                                 "arm": arm, **m})
                    print(f"        k={k} seed={seed} {arm:<8} "
                          f"AUROC={m.get('auroc', float('nan')):.4f}")

    if a.dry_run:
        return 0
    if not rows:
        print("\nnothing collected.")
        return 0

    out_csv = out_root / f"k_scaling_{a.dataset}.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    # ── the curve ───────────────────────────────────────────────────
    by = {}
    for r in rows:
        by.setdefault((r["k"], r["arm"]), {})[r["seed"]] = r.get("auroc")

    print("\n" + "=" * 74)
    print("  COST OF A PATIENT-LEVEL GUARANTEE, AS A CURVE IN k")
    print("=" * 74)
    print(f"  {'k':>3}{'record AUROC':>15}{'patient AUROC':>16}"
          f"{'gap':>10}   {'95% CI of gap':>22}")
    print("  " + "-" * 68)
    gaps, observed = {}, {}
    for k in a.k:
        s = by.get((k, "sample"), {})
        p = by.get((k, "patient"), {})
        common = sorted(set(s) & set(p))
        if not common:
            continue
        sv = [s[c] for c in common]; pv = [p[c] for c in common]
        t = paired_test(pv, sv)          # sample - patient
        ms, _, _ = mean_ci(sv); mp, _, _ = mean_ci(pv)
        gaps[k] = t
        # paired_test returns None with fewer than two seeds. Record the
        # observed difference separately so "no interval" is never reported as
        # "not run" — at k=1 that distinction is the validity anchor itself.
        observed[k] = (float(np.mean(sv)) - float(np.mean(pv)), len(common))
        ci = f"[{t['ci_low']:+.4f}, {t['ci_high']:+.4f}]" if t else "—"
        g = f"{t['mean_diff']:+.4f}" if t else "—"
        print(f"  {k:>3}{ms:>15.4f}{mp:>16.4f}{g:>10}   {ci:>22}")

    # ── validity check ──────────────────────────────────────────────
    print("\n" + "=" * 74)
    print("  VALIDITY CHECK — the two arms must COLLAPSE at k=1")
    print("=" * 74)
    t1 = gaps.get(1)
    if t1 is None and 1 not in observed:
        print("    k=1 not run — the curve has no validity anchor.")
    elif t1 is None:
        d, n = observed[1]
        verdict = "consistent with" if abs(d) < 0.02 else "OUTSIDE"
        print(f"    gap at k=1 = {d:+.4f} over {n} seed(s) — {verdict} the "
              f"|gap| < 0.02 anchor.")
        print("          A paired interval needs at least two seeds; this is "
              "the observed\n          difference, not a resolved test. Run "
              "more seeds before quoting it.")
    elif not t1["significant"]:
        print(f"    PASS  gap at k=1 = {t1['mean_diff']:+.4f} "
              f"[{t1['ci_low']:+.4f}, {t1['ci_high']:+.4f}] — includes zero.")
        print("          At k=1 a patient IS a record, so the arms are the "
              "same algorithm.")
    else:
        print(f"    FAIL  gap at k=1 = {t1['mean_diff']:+.4f} "
              f"[{t1['ci_low']:+.4f}, {t1['ci_high']:+.4f}] — EXCLUDES zero.")
        print("          The arms should be identical here. Something differs "
              "between them\n          that is not the privacy unit; the rest "
              "of the curve is not trustworthy.")

    print(f"""
  HOW TO READ THIS
    Levels fall as k falls because subsampling shrinks the training set. That
    is expected and is not the result. The RESULT is the gap column: at each k
    both arms saw identical data, so the gap isolates the privacy unit.

    A gap that grows with k is the scaling law. A flat gap means the cost of a
    patient-level guarantee does not depend on how many records a patient
    contributes, which would itself be worth reporting.

  Written: {out_csv}""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
