"""
attribution_stability.py — is the attribution ranking a finding, or one seed?

WHY
---
A single attribution run produces a confident-looking ranking, and a single
attribution run is worth very little. Attribution is known to move with the
seed, with the baseline, and with the training recipe. "ART_MBP_observed is
the second most important input" is publishable only if it survives all three;
otherwise it is a property of one checkpoint.

This reads the CSVs written by attribution.py and answers three questions the
paper has to answer anyway:

  1. SEED STABILITY   — same recipe, different seeds. Spearman rank
                        correlation between every pair, and how often each
                        input lands in the top 5. A ranking that is not stable
                        across seeds cannot be quoted as a ranking.

  2. BASELINE SENSITIVITY — mean baseline vs zero baseline. IG measures
                        deviation FROM a baseline, so a conclusion that flips
                        between two defensible baselines is a conclusion about
                        the baseline, not the model.

  3. RECIPE EFFECT    — does DP change what the model attends to? Comparing
                        head-only DP against no-DP checkpoints asks whether
                        privacy shifts the model's evidence, which is not a
                        robustness check but a question nobody in this setting
                        has measured.

Nothing is recomputed here. This consumes attribution.py's output, so the two
cannot disagree about what was measured.
"""

import re
import sys
import csv
import json
import argparse
from pathlib import Path
from collections import defaultdict

import numpy as np

_SIM = Path(__file__).resolve().parent.parent


def spearman(a, b):
    """Rank correlation without a scipy dependency at import time."""
    try:
        from scipy import stats
        return float(stats.spearmanr(a, b).statistic)
    except Exception:
        ra = np.argsort(np.argsort(a)).astype(float)
        rb = np.argsort(np.argsort(b)).astype(float)
        ra -= ra.mean(); rb -= rb.mean()
        d = float(np.sqrt((ra ** 2).sum() * (rb ** 2).sum()))
        return float((ra * rb).sum() / d) if d else float("nan")


def load(path: Path):
    rows = list(csv.DictReader(open(path)))
    return {r["name"]: float(r["share_pct"]) for r in rows}, rows


def group_of(stem: str):
    """Recipe group and seed from a checkpoint stem, e.g.
    attribution_ckpt_patient_43_mean -> ('patient', 43, 'mean')."""
    m = re.match(r"attribution_ckpt_(.+?)_(?:seed)?(\d+)_(mean|zero)$", stem)
    if not m:
        return None
    return m.group(1), int(m.group(2)), m.group(3)


def matrix(files):
    """Aligned share-% matrix over the union of input names."""
    per, names = [], None
    for f in files:
        d, _ = load(f)
        per.append(d)
        names = set(d) if names is None else (names & set(d))
    names = sorted(names)
    return np.array([[d[n] for n in names] for d in per]), names


def report_pairwise(label, files, tag):
    if len(files) < 2:
        print(f"  {label}: only {len(files)} run — cannot assess")
        return None
    M, names = matrix(files)
    rho = [spearman(M[i], M[j])
           for i in range(len(M)) for j in range(i + 1, len(M))]
    print(f"\n  {label}  ({len(files)} runs, {len(names)} inputs)")
    print(f"    Spearman rho between runs: mean {np.mean(rho):.3f}  "
          f"min {np.min(rho):.3f}  max {np.max(rho):.3f}")
    return M, names, rho


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="vitaldb")
    ap.add_argument("--dir", default=None)
    ap.add_argument("--top_k", type=int, default=5)
    a = ap.parse_args()

    d = Path(a.dir) if a.dir else (
        _SIM / "results" / "phase5" / "attribution" / a.dataset)
    files = sorted(d.glob("attribution_*.csv"))
    if not files:
        raise SystemExit(f"[FATAL] no attribution CSVs in {d}. "
                         f"Run scripts/attribution.py first.")

    by_group = defaultdict(list)
    for f in files:
        g = group_of(f.stem)
        if g is None:
            print(f"  [skip] unparseable name: {f.name}")
            continue
        by_group[(g[0], g[2])].append((g[1], f))
    for k in by_group:
        by_group[k].sort()

    print("=" * 74)
    print(f"ATTRIBUTION STABILITY — {a.dataset}")
    print("=" * 74)
    for (recipe, base), items in sorted(by_group.items()):
        print(f"  {recipe:<12} baseline={base:<5} seeds "
              f"{[s for s, _ in items]}")

    summary = {}

    # ── 1. seed stability, per recipe, mean baseline ────────────────
    print("\n" + "=" * 74)
    print("  1. SEED STABILITY")
    print("=" * 74)
    for (recipe, base), items in sorted(by_group.items()):
        if base != "mean":
            continue
        if len(items) < 2:
            print(f"  {recipe}: only {len(items)} seed — stability unassessable, "
                  f"do not quote this ranking yet")
            continue
        got = report_pairwise(f"{recipe}", [f for _, f in items], recipe)
        if not got:
            continue
        M, names, rho = got
        mean_share = M.mean(0)
        sd_share = M.std(0, ddof=1)
        order = np.argsort(-mean_share)

        # How often each input lands in the top-k, across seeds.
        hits = defaultdict(int)
        for row in M:
            for i in np.argsort(-row)[:a.top_k]:
                hits[names[i]] += 1

        print(f"    {'input':<24}{'share %':>10}{'sd':>8}"
              f"{'top-' + str(a.top_k):>8}")
        for i in order[:8]:
            print(f"    {names[i]:<24}{mean_share[i]:>9.2f}%{sd_share[i]:>8.2f}"
                  f"{hits[names[i]]:>5}/{len(M)}")
        unstable = [names[i] for i in order[:a.top_k]
                    if hits[names[i]] < len(M)]
        print(f"    -> top-{a.top_k} membership is "
              + ("STABLE across all seeds" if not unstable
                 else f"UNSTABLE: {unstable} drop out on some seeds"))
        summary[f"{recipe}_seed_rho_mean"] = float(np.mean(rho))
        summary[f"{recipe}_top{a.top_k}_stable"] = not unstable

    # ── 2. baseline sensitivity ─────────────────────────────────────
    print("\n" + "=" * 74)
    print("  2. BASELINE SENSITIVITY  (mean vs zero)")
    print("=" * 74)
    done = False
    for (recipe, base), items in sorted(by_group.items()):
        if base != "mean":
            continue
        other = by_group.get((recipe, "zero"))
        if not other:
            continue
        shared = sorted(set(s for s, _ in items) & set(s for s, _ in other))
        if not shared:
            continue
        rhos = []
        for s in shared:
            fm = dict(items)[s]
            fz = dict(other)[s]
            dm, _ = load(fm)
            dz, _ = load(fz)
            nm = sorted(set(dm) & set(dz))
            rhos.append(spearman([dm[n] for n in nm], [dz[n] for n in nm]))
        print(f"  {recipe}: rho(mean, zero) over seeds {shared} = "
              f"{np.mean(rhos):.3f}")
        print("    -> " + ("ranking is robust to the baseline choice"
                           if np.mean(rhos) > 0.8 else
                           "ranking DEPENDS on the baseline — report both, and "
                           "do not quote a single ordering"))
        summary[f"{recipe}_baseline_rho"] = float(np.mean(rhos))
        done = True
    if not done:
        print("  no recipe has both baselines — run with --baseline zero too")

    # ── 3. recipe effect: does DP move the evidence? ────────────────
    print("\n" + "=" * 74)
    print("  3. RECIPE EFFECT  (does DP change what the model attends to?)")
    print("=" * 74)
    means = {}
    for (recipe, base), items in sorted(by_group.items()):
        if base != "mean":
            continue
        M, names = matrix([f for _, f in items])
        means[recipe] = (M.mean(0), names)
    if len(means) < 2:
        print("  need at least two recipes; run the factorial checkpoints too")
    else:
        keys = sorted(means)
        print(f"  {'pair':<30}{'rho':>8}{'mask share A':>15}{'mask share B':>15}")
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                ka, kb = keys[i], keys[j]
                va, na = means[ka]
                vb, nb = means[kb]
                shared = sorted(set(na) & set(nb))
                xa = [va[na.index(n)] for n in shared]
                xb = [vb[nb.index(n)] for n in shared]
                print(f"  {ka + ' vs ' + kb:<30}{spearman(xa, xb):>8.3f}"
                      f"{'':>15}{'':>15}")

        print(f"\n  {'recipe':<16}{'missingness share %':>22}")
        for k in keys:
            v, names = means[k]
            share = sum(v[i] for i, n in enumerate(names)
                        if n.endswith(("_observed", "_missing"))
                        or n == "abg_done")
            print(f"  {k:<16}{share:>21.2f}%")
            summary[f"{k}_missingness_share"] = float(share)
        print("\n  A large rho with a shifted missingness share means DP keeps "
              "the ordering\n  but changes how much the model leans on "
              "whether a measurement exists.")

    out = d / "stability_summary.json"
    json.dump(summary, open(out, "w"), indent=2)
    print(f"\nWritten: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
