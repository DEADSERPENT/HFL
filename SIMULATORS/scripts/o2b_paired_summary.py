"""o2b_paired_summary.py — privacy cost of eps=1 against the eps=inf reference,
paired by seed, for every metric of the multi-seed O2b sweep.

check_objectives scores O2b on accuracy, which is the pre-registered metric.
On a corpus whose accuracy is pinned at the majority-class rate (eICU,
mortality 4.2 %) the accuracy difference measures where the decision threshold
falls, not what privacy costs, so the ranking metrics are reported alongside.

Reads  results/phase5/o2b_multiseed/<ds>/epsilon_sweep.csv
Writes results/phase5/o2b_multiseed/<ds>/o2b_paired.json

Cost = reference - private, so a positive value is a loss under DP.
"""
import argparse
import csv
import json
import math
import os
from scipy import stats

METRICS = ("accuracy", "macro_auc", "auprc", "case_auc", "case_auprc",
           "accuracy_valthr", "balanced_accuracy_valthr")


def paired(diffs):
    n = len(diffs)
    m = sum(diffs) / n
    if n < 2:
        return dict(n=n, mean=m)
    sd = math.sqrt(sum((x - m) ** 2 for x in diffs) / (n - 1))
    half = stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n)
    p = float(stats.ttest_1samp(diffs, 0.0).pvalue) if sd > 0 else None
    return dict(n=n, mean=m, sd=sd, ci_low=m - half, ci_high=m + half, p=p,
                per_seed=diffs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--root", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results", "phase5",
        "o2b_multiseed"))
    a = ap.parse_args()
    d = os.path.join(a.root, a.dataset)
    rows = list(csv.DictReader(open(os.path.join(d, "epsilon_sweep.csv"))))
    by = {}
    for r in rows:
        by.setdefault(r["seed"], {})[r["epsilon"]] = r
    seeds = sorted(s for s, e in by.items() if {"1", "inf"} <= e.keys())
    out = dict(dataset=a.dataset, seeds=[int(s) for s in seeds],
               eps_spent=max(float(by[s]["1"]["epsilon_spent"]) for s in seeds)
               if seeds else None, metrics={})
    for m in METRICS:
        diffs = [float(by[s]["inf"][m]) - float(by[s]["1"][m]) for s in seeds
                 if by[s]["inf"].get(m) not in (None, "") and by[s]["1"].get(m) not in (None, "")]
        if diffs:
            out["metrics"][m] = dict(
                private=sum(float(by[s]["1"][m]) for s in seeds) / len(seeds),
                reference=sum(float(by[s]["inf"][m]) for s in seeds) / len(seeds),
                cost=paired(diffs))
    path = os.path.join(d, "o2b_paired.json")
    json.dump(out, open(path, "w"), indent=2)
    for m, v in out["metrics"].items():
        c = v["cost"]
        ci = f" [{c['ci_low']:+.4f}, {c['ci_high']:+.4f}] p={c['p']}" if "ci_low" in c else ""
        print(f"{m:11s} priv {v['private']:.4f} ref {v['reference']:.4f} "
              f"cost {c['mean']:+.4f}{ci}  (n={c['n']})")
    print("wrote", path)


if __name__ == "__main__":
    main()
