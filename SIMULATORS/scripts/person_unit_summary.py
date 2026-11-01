"""person_unit_summary.py — paired cost of the privacy unit (record -> patient).

Reads  results/phase5/patient_dp/<ds>/{sample,patient}_seed<s>_test.json
Writes results/phase5/patient_dp/<ds>/unit_paired.json

Difference is patient minus record (sample) arm, paired by seed, 95 % Student-t.

    python SIMULATORS/scripts/person_unit_summary.py vitaldb_person
"""
import argparse
import glob
import json
import os
import re

import numpy as np
from scipy import stats

SIM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
METRICS = ("macro_auc", "auprc", "balanced_accuracy_valthr")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    a = ap.parse_args()
    d = os.path.join(SIM, "results", "phase5", "patient_dp", a.dataset)
    seeds = sorted(int(re.search(r"seed(\d+)_test", p).group(1))
                   for p in glob.glob(os.path.join(d, "patient_seed*_test.json"))
                   if os.path.exists(p.replace("patient_seed", "sample_seed")))
    if not seeds:
        raise SystemExit(f"[FATAL] no paired seeds in {d}")
    out = {"dataset": a.dataset, "seeds": seeds, "difference": "patient - record"}
    for m in METRICS:
        rec = np.array([json.load(open(f"{d}/sample_seed{s}_test.json"))[m] for s in seeds])
        pat = np.array([json.load(open(f"{d}/patient_seed{s}_test.json"))[m] for s in seeds])
        diff = pat - rec
        n = len(diff)
        h = stats.t.ppf(0.975, n - 1) * diff.std(ddof=1) / np.sqrt(n) if n > 1 else float("nan")
        out[m] = {"record": float(rec.mean()), "patient": float(pat.mean()),
                  "mean": float(diff.mean()), "ci_low": float(diff.mean() - h),
                  "ci_high": float(diff.mean() + h),
                  "p": float(stats.ttest_1samp(diff, 0).pvalue) if n > 1 else float("nan"),
                  "per_seed": diff.tolist()}
        print(f"  {m:26s} record {rec.mean():.4f}  patient {pat.mean():.4f}  "
              f"diff {diff.mean():+.4f} [{diff.mean() - h:+.4f}, {diff.mean() + h:+.4f}]  "
              f"p={out[m]['p']:.3f}")
    json.dump(out, open(os.path.join(d, "unit_paired.json"), "w"), indent=2)
    print(f"wrote {d}/unit_paired.json")


if __name__ == "__main__":
    main()
