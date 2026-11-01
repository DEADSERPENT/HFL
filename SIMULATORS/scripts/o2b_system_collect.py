"""o2b_system_collect.py — gather the system-recipe O2b runs into the
epsilon_sweep.csv schema that o2b_paired_summary.py and check_objectives read.

The O2b sweep (o2b_multiseed/) trains flat FedAvg on the head for 30 rounds;
this measures the cost on the PROPOSED SYSTEM itself (the headline recipe,
10 global x tau_e edge rounds), private arm vs the same run with --no_dp.

Reads  results/phase5/o2b_system/<ds>/{dp,nodp}_s<seed>/run_test.json
       results/phase5/o2b_system/<ds>/dp_s<seed>/privacy_total_<ds>.json
Writes results/phase5/o2b_system/<ds>/epsilon_sweep.csv
"""
import argparse
import csv
import glob
import json
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                    "results", "phase5", "o2b_system")
COLS = ("accuracy", "macro_auc", "auprc", "accuracy_valthr",
        "balanced_accuracy_valthr", "sensitivity_valthr", "specificity_valthr")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--tag", default="", help="results subdir suffix, e.g. _disjoint")
    a = ap.parse_args()
    d = os.path.join(ROOT, a.dataset + a.tag)
    rows = []
    for run in sorted(glob.glob(os.path.join(d, "*_s*", "run_test.json"))):
        arm, seed = re.match(r"(dp|nodp)_s(\d+)", os.path.basename(os.path.dirname(run))).groups()
        t = json.load(open(run))
        r = dict(dataset=a.dataset, epsilon="1" if arm == "dp" else "inf", seed=seed,
                 **{c: t.get(c, "") for c in COLS}, epsilon_spent="")
        if arm == "dp":
            pt = os.path.join(os.path.dirname(run), f"privacy_total_{a.dataset}.json")
            r["epsilon_spent"] = json.load(open(pt))["epsilon_TOTAL"]
        rows.append(r)
    path = os.path.join(d, "epsilon_sweep.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path} ({len(rows)} runs)")


if __name__ == "__main__":
    main()
