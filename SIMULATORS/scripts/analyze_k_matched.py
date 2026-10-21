#!/usr/bin/env python3
"""Amendment A2 analysis — how much of eICU's k-law shortfall is the budget?

PREREGISTRATION_EICU.md A2 records a confound: the forecast was FITTED on a
VitalDB grid trained at eps_train 0.9935 and TESTED on eICU at 0.7956. More
noise compresses the arms, which is the same direction as the observed
shortfall, so the P1b refutation could not be read as a corpus effect.

The correction A2 specifies is a VitalDB re-run at the eICU operating point.
That run completed 2026-09-21. This script reads all three grids and reports
the decomposition A2 asks for:

    original VitalDB  ->  matched VitalDB   = the budget's contribution
    matched VitalDB   ->  eICU              = the remaining corpus effect

Nothing is hardcoded: every grid path, its epsilon and its seeds are resolved
from the artefacts on disk.
"""
import argparse, csv, glob, json, math, os
from collections import defaultdict

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The forecast frozen in PREREGISTRATION_EICU.md §2, fitted on the ORIGINAL
# VitalDB grid. It is never refitted — A2 is explicit about that.
FORECAST_A, FORECAST_B = 0.0878, 0.883
BAND = 0.030          # registered acceptance band
CONTROL_ANCHOR = 0.020  # registered |gap| tolerance for the k=1 control


def forecast(k):
    return FORECAST_A * (1.0 - math.exp(-FORECAST_B * (k - 1)))


def load_grid(path):
    """-> {k: {seed: {arm: auprc}}} plus the seeds and ks actually present."""
    g = defaultdict(lambda: defaultdict(dict))
    with open(path) as fh:
        for r in csv.DictReader(fh):
            g[int(r["k"])][int(r["seed"])][r["arm"]] = float(r["auprc"])
    return g


def eps_of(grid_dir):
    """Resolve the training budget from the argv recorded alongside the grid.

    `run_metadata_*.json` stores the full command line under "argv", so the
    budget each grid was actually trained at is read back rather than assumed.
    Returns (epsilon, epsilon_conf); either may be None if never passed, and
    a None epsilon_conf means hfl_trainer's own default applied.
    """
    eps = conf = None
    for f in sorted(glob.glob(os.path.join(grid_dir, "*/run_metadata_*.json"))
                    + glob.glob(os.path.join(grid_dir, "run_metadata_*.json"))):
        try:
            argv = json.load(open(f)).get("argv") or []
        except Exception:
            continue
        for flag, slot in (("--epsilon", "eps"), ("--epsilon_conf", "conf")):
            if flag in argv:
                try:
                    v = float(argv[argv.index(flag) + 1])
                except (IndexError, ValueError):
                    continue
                if slot == "eps" and eps is None:
                    eps = v
                elif slot == "conf" and conf is None:
                    conf = v
        if eps is not None and conf is not None:
            break
    return eps, conf


def paired(grid, k):
    seeds = sorted(s for s, a in grid[k].items() if {"sample", "patient"} <= set(a))
    s = [grid[k][x]["sample"] for x in seeds]
    p = [grid[k][x]["patient"] for x in seeds]
    d = np.asarray(s) - np.asarray(p)
    n = len(d)
    if n < 2:
        return dict(n=n, mean=float(d.mean()) if n else float("nan"),
                    hw=float("nan"), p=float("nan"),
                    sample=float(np.mean(s)) if n else float("nan"),
                    patient=float(np.mean(p)) if n else float("nan"), seeds=seeds)
    hw = stats.t.ppf(0.975, n - 1) * d.std(ddof=1) / math.sqrt(n)
    return dict(n=n, mean=float(d.mean()), hw=float(hw),
                p=float(stats.ttest_rel(s, p).pvalue),
                sample=float(np.mean(s)), patient=float(np.mean(p)), seeds=seeds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.path.join(ROOT, "results/phase5/k_scaling"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    grids = {
        "vitaldb_original": os.path.join(a.base, "vitaldb"),
        "vitaldb_matched": os.path.join(a.base, "vitaldb_eps080"),
        "eicu": os.path.join(a.base, "eicu"),
    }
    loaded, report = {}, {}
    for name, d in grids.items():
        hits = glob.glob(os.path.join(d, "k_scaling_*.csv"))
        if not hits:
            print(f"  [skip] {name}: no k_scaling_*.csv under {d}")
            continue
        loaded[name] = load_grid(hits[0])
        e, c = eps_of(d)
        report[name] = {"csv": os.path.relpath(hits[0], ROOT),
                        "eps_train": e, "eps_conf": c}

    print("=" * 78)
    print("  AMENDMENT A2 — budget vs corpus in the records-per-individual law")
    print("=" * 78)
    for name, meta in report.items():
        e, c = meta["eps_train"], meta["eps_conf"]
        cs = "trainer default" if c is None else f"{c:g}"
        print(f"  {name:18} eps_train={'?' if e is None else format(e, 'g'):<7}"
              f"eps_conf={cs:<16}{meta['csv']}")

    ks = sorted(set().union(*[set(g) for g in loaded.values()]))
    print(f"\n  AUPRC gap = record arm - individual arm, paired by seed\n")
    head = f"  {'k':>3} {'forecast':>9}"
    for n in loaded:
        head += f" | {n:>26}"
    print(head)
    print("  " + "-" * (len(head) - 2))

    table = defaultdict(dict)
    for k in ks:
        row = f"  {k:>3} {forecast(k):>9.4f}"
        for name, g in loaded.items():
            if k not in g:
                row += f" | {'—':>26}"
                continue
            r = paired(g, k)
            table[k][name] = r
            row += f" | {r['mean']:>+8.4f}±{r['hw']:.4f} p={r['p']:>5.3f}"
        print(row)

    # --- the decomposition A2 asks for -------------------------------------
    print("\n" + "=" * 78)
    print("  DECOMPOSITION")
    print("=" * 78)
    for k in ks:
        o = table[k].get("vitaldb_original")
        m = table[k].get("vitaldb_matched")
        e = table[k].get("eicu")
        if not (o and m and e):
            continue
        budget = m["mean"] - o["mean"]
        corpus = e["mean"] - m["mean"]
        print(f"  k={k:<3} budget contribution {budget:+.4f}   "
              f"corpus contribution {corpus:+.4f}   "
              f"(total {e['mean'] - o['mean']:+.4f})")

    # --- the same decomposition, corrected for a control pedestal ----------
    # If a grid separates the arms at k=1 — where construction says it must
    # not — that offset is apparatus, not unit, and the most conservative
    # reading is that it sits under every k on that grid. Subtracting it is a
    # SENSITIVITY check, not a correction we claim is right; both readings are
    # printed so the conclusion can be judged against the worse of the two.
    print("\n" + "=" * 78)
    print("  SENSITIVITY — same decomposition with each grid's k=1 offset removed")
    print("=" * 78)
    ped = {}
    for name in loaded:
        r = table.get(1, {}).get(name)
        ped[name] = r["mean"] if r else 0.0
        print(f"  {name:18} pedestal {ped[name]:+.4f}")
    print()
    for k in ks:
        o = table[k].get("vitaldb_original")
        m = table[k].get("vitaldb_matched")
        e = table[k].get("eicu")
        if not (o and m and e) or k == 1:
            continue
        oc = o["mean"] - ped["vitaldb_original"]
        mc = m["mean"] - ped["vitaldb_matched"]
        ec = e["mean"] - ped["eicu"]
        print(f"  k={k:<3} budget {mc - oc:+.4f}   corpus {ec - mc:+.4f}   "
              f"(total {ec - oc:+.4f})   [corrected gaps "
              f"orig {oc:+.4f} matched {mc:+.4f} eicu {ec:+.4f}]")

    # --- the control, checked on every grid --------------------------------
    print("\n" + "=" * 78)
    print(f"  k=1 POSITIVE CONTROL  (registered anchor |gap| < {CONTROL_ANCHOR})")
    print("=" * 78)
    for name in loaded:
        r = table.get(1, {}).get(name)
        if not r:
            continue
        ok = abs(r["mean"]) < CONTROL_ANCHOR
        signs = [loaded[name][1][s]["sample"] - loaded[name][1][s]["patient"]
                 for s in r["seeds"]]
        pos = sum(1 for x in signs if x > 0)
        print(f"  {name:18} gap {r['mean']:+.4f} ±{r['hw']:.4f} p={r['p']:.3f}  "
              f"{'PASS' if ok else 'OUTSIDE ANCHOR'}   "
              f"sign {pos}/{len(signs)} positive")

    out = a.out or os.path.join(ROOT, "results/phase5/k_scaling/a2_matched_budget.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"grids": report, "forecast": {"A": FORECAST_A, "b": FORECAST_B,
                                             "band": BAND,
                                             "control_anchor": CONTROL_ANCHOR},
               "gaps": {str(k): table[k] for k in table}},
              open(out, "w"), indent=2, default=float)
    print(f"\n[SAVED] {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
