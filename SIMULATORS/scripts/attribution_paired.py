"""attribution_paired.py — missingness share of the attribution, per recipe, with
seed-paired differences for the comparisons Results quotes.

attribution_stability.py reports the mean share per recipe; a difference
between two recipes is only interpretable paired by seed, because the share
moves with the seed (full_dp spans 24.9-31.9 %).

Reads  results/phase5/attribution/<ds>/attribution_ckpt_<arm>_<seed>_mean.json
Writes results/phase5/attribution/<ds>/attribution_paired.json
"""
import argparse
import glob
import json
import os
import re
import statistics as st
from scipy import stats

# (minuend, subtrahend, what the difference isolates)
PAIRS = (("full_dp", "full_nodp", "record-level DP, full model fine-tuned"),
         ("patient", "sample", "privacy unit, encoders frozen"),
         ("full_nodp", "head_nodp", "encoder fine-tuning, no DP"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", nargs="?", default="vitaldb")
    a = ap.parse_args()
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results",
                     "phase5", "attribution", a.dataset)
    share, n_inputs, n_masks = {}, None, None
    for f in sorted(glob.glob(os.path.join(d, "attribution_ckpt_*_mean.json"))):
        m = re.search(r"ckpt_(.+?)_(?:seed)?(\d+)_mean\.json$", f)
        share.setdefault(m.group(1), {})[int(m.group(2))] = \
            json.load(open(f))["missingness_share_pct"]
        if n_inputs is None:
            rows = open(f[:-5] + ".csv").read().splitlines()[1:]
            n_inputs = len(rows)
            n_masks = sum(r.split(",")[2] == "1" for r in rows)
    out = dict(dataset=a.dataset, n_inputs=n_inputs, n_mask_inputs=n_masks,
               mask_input_fraction_pct=100 * n_masks / n_inputs, arms={}, paired=[])
    for arm, s in share.items():
        v = list(s.values())
        out["arms"][arm] = dict(seeds=sorted(s), mean=st.mean(v),
                                sd=st.stdev(v) if len(v) > 1 else None,
                                min=min(v), max=max(v))
    for x, y, what in PAIRS:
        ks = sorted(set(share[x]) & set(share[y]))
        diff = [share[x][k] - share[y][k] for k in ks]
        out["paired"].append(dict(
            arm=x, minus=y, isolates=what, seeds=ks, mean=st.mean(diff),
            per_seed=diff, p=float(stats.ttest_1samp(diff, 0.0).pvalue)))
    path = os.path.join(d, "attribution_paired.json")
    json.dump(out, open(path, "w"), indent=2)
    print(f"{n_masks}/{n_inputs} inputs are missingness indicators")
    for arm, v in out["arms"].items():
        print(f"{arm:10s} {v['mean']:6.2f} % (n={len(v['seeds'])})")
    for p in out["paired"]:
        print(f"{p['arm']} - {p['minus']}: {p['mean']:+.2f} pts "
              f"[{min(p['per_seed']):+.2f}, {max(p['per_seed']):+.2f}] p={p['p']:.3f}")
    print("wrote", path)


if __name__ == "__main__":
    main()
