"""
run_statistics.py — Phase 6 deliverable D6.4 (Phase 6.txt §6.4).

Turns repeated runs into defensible statements: mean +- sd, 95 % confidence
intervals, and paired significance tests between arms.

Three rules this implements, because breaking any of them is how a plausible
number becomes an indefensible claim:

1. PAIRED, not unpaired. Arms are compared seed-by-seed. Two arms trained on
   seeds {42,43,44} share their data order and initialisation per seed, so the
   seed is a blocking factor; an unpaired t-test throws that away and inflates
   the variance it is testing against.

2. A DIFFERENCE IS NOT A RESULT UNTIL IT CLEARS THE SEED NOISE. Every contrast
   reports the effect size next to the seed sd, and the verdict is driven by
   the CI containing zero — not by p alone. With 3-5 seeds, p is fragile and
   the interval is the honest summary.

3. n IS REPORTED EVERYWHERE. §6.4.1 asks for >=5 seeds. Fewer is usable but
   must be visible, so every line carries its n and the script warns when
   n < 5 rather than quietly reporting a mean of two numbers.

NAME: deliberately NOT statistics.py. scripts/ lands on sys.path for
anything run from it, so a module named statistics.py SHADOWS the
Python standard library for every sibling script — membership_inference.py
failed with "module 'statistics' has no attribute 'mean'" because of it.

Reads whatever the pipeline has produced (epsilon sweep, ablation, joint eval,
baselines) and writes results/phase6/<dataset>/statistics.txt.
"""

import os
import sys
import csv
import json
import glob
import math
import argparse
from pathlib import Path
from collections import defaultdict

import numpy as np

_SIM = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIM / "data" / "loaders"))
from datasets import REGISTRY                                 # noqa: E402

MIN_SEEDS = 5          # Phase 6.txt §6.4.1


def mean_ci(x, conf=0.95):
    """Mean and half-width of the Student-t CI. t, not z: with 3-5 seeds the
    normal approximation is materially too narrow (t=4.30 vs z=1.96 at n=3)."""
    x = np.asarray([v for v in x if v is not None and not np.isnan(v)], float)
    n = len(x)
    if n == 0:
        return None, None, 0
    if n == 1:
        return float(x[0]), float("nan"), 1
    sd = float(np.std(x, ddof=1))
    try:
        from scipy import stats
        t = float(stats.t.ppf(0.5 + conf / 2, n - 1))
    except Exception:
        t = 1.96
    return float(np.mean(x)), t * sd / math.sqrt(n), n


def paired_test(a, b):
    """Paired comparison of b vs a. Returns dict or None if unusable."""
    pairs = [(x, y) for x, y in zip(a, b)
             if x is not None and y is not None
             and not np.isnan(x) and not np.isnan(y)]
    if len(pairs) < 2:
        return None
    d = np.array([y - x for x, y in pairs], float)
    n = len(d)
    mean_d = float(np.mean(d))
    sd_d = float(np.std(d, ddof=1))
    out = {"n": n, "mean_diff": mean_d, "sd_diff": sd_d}
    try:
        from scipy import stats
        t_stat, p_t = stats.ttest_rel([x for x, _ in pairs], [y for _, y in pairs])
        out["t_stat"], out["p_ttest"] = float(t_stat), float(p_t)
        if n >= 5:
            # Wilcoxon needs a handful of pairs to say anything; below that it
            # cannot reach significance regardless of effect size, so running
            # it would only produce a misleading "n.s.".
            try:
                w, p_w = stats.wilcoxon([x for x, _ in pairs], [y for _, y in pairs])
                out["p_wilcoxon"] = float(p_w)
            except ValueError:
                pass
        tcrit = float(stats.t.ppf(0.975, n - 1))
    except Exception:
        tcrit = 1.96
    half = tcrit * sd_d / math.sqrt(n)
    out["ci_low"], out["ci_high"] = mean_d - half, mean_d + half
    out["significant"] = not (out["ci_low"] <= 0 <= out["ci_high"])
    return out


def load_sweep(ds):
    """{(epsilon, recipe): {seed: metric}} from the epsilon sweep."""
    p = _SIM / "results" / "phase5" / "epsilon_sweep" / ds / "epsilon_sweep.csv"
    if not p.exists():
        return {}
    out = defaultdict(dict)
    with open(p) as f:
        for r in csv.DictReader(f):
            for key in ("macro_auc", "auprc", "accuracy"):
                try:
                    v = float(r[key])
                except (KeyError, TypeError, ValueError):
                    v = None
                out[(r["epsilon"], r["recipe"], key)][r["seed"]] = v
    return out


def section(title, w=78):
    return "\n" + "=" * w + f"\n{title}\n" + "=" * w


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, choices=sorted(REGISTRY))
    ap.add_argument("--output", default=None)
    a = ap.parse_args()

    ds = a.dataset
    res = _SIM / "results" / "phase5"
    p6 = _SIM / "results" / "phase6" / ds
    p6.mkdir(parents=True, exist_ok=True)
    out_path = Path(a.output or p6 / "statistics.txt")

    L = []
    L.append(section(f"STATISTICAL ANALYSIS — {ds.upper()}   (Phase 6, D6.4)"))
    L.append(f"  min seeds required by Phase 6 §6.4.1 : {MIN_SEEDS}")
    L.append("  intervals are Student-t 95 % CIs; contrasts are PAIRED by seed")

    warnings = []

    # ── 1. epsilon sweep: per-point spread and the recipe contrast ──
    sweep = load_sweep(ds)
    if sweep:
        L.append(section("1. PRIVACY–UTILITY CURVE  (per point, across seeds)"))
        L.append(f"  {'eps':>6}{'recipe':>8}{'metric':>11}{'mean':>10}"
                 f"{'95% CI':>20}{'n':>4}")
        L.append("  " + "-" * 63)
        for (eps, rec, key) in sorted(sweep):
            if key != "macro_auc":
                continue
            vals = list(sweep[(eps, rec, key)].values())
            m, h, n = mean_ci(vals)
            if m is None:
                continue
            ci = f"[{m-h:.4f}, {m+h:.4f}]" if h == h else "—"
            L.append(f"  {eps:>6}{rec:>8}{key:>11}{m:>10.4f}{ci:>20}{n:>4}")
            if n < MIN_SEEDS:
                warnings.append(f"eps={eps} recipe={rec}: n={n} < {MIN_SEEDS}")

        # head-only vs full-model, paired at each eps
        L.append(section("2. RECIPE CONTRAST  head-only DP vs full-model DP"))
        L.append("   (paired by seed at each eps; positive = head-only better)")
        any_pair = False
        for eps in sorted({e for e, _, _ in sweep}):
            full = sweep.get((eps, "full", "macro_auc"), {})
            head = sweep.get((eps, "head", "macro_auc"), {})
            seeds = sorted(set(full) & set(head))
            if not seeds:
                continue
            any_pair = True
            t = paired_test([full[s] for s in seeds], [head[s] for s in seeds])
            if not t:
                continue
            verdict = ("SIGNIFICANT" if t["significant"] else "n.s.")
            L.append(f"\n   eps = {eps}   (n={t['n']} paired seeds)")
            L.append(f"     mean ΔAUROC = {t['mean_diff']:+.4f}   "
                     f"95% CI [{t['ci_low']:+.4f}, {t['ci_high']:+.4f}]   {verdict}")
            if "p_ttest" in t:
                L.append(f"     paired t-test p = {t['p_ttest']:.4g}"
                         + (f"   Wilcoxon p = {t['p_wilcoxon']:.4g}"
                            if "p_wilcoxon" in t else
                            f"   (Wilcoxon needs n>={MIN_SEEDS})"))
        if not any_pair:
            L.append("   — no eps has BOTH recipes at a shared seed yet.")
    else:
        L.append(section("1-2. PRIVACY–UTILITY CURVE"))
        L.append("   — epsilon_sweep.csv not found; run the epsilon_sweep stage.")

    # ── 3. cost of privacy: eps<=1 vs the eps=inf reference ─────────
    L.append(section("3. COST OF PRIVACY  (Objective 2: accuracy loss <= 2 pp)"))
    if sweep:
        ref = sweep.get(("inf", "none", "accuracy"), {})
        best = None
        for eps in sorted({e for e, _, _ in sweep if e != "inf"},
                          key=lambda e: float(e)):
            if float(eps) > 1.0:
                continue
            for rec in ("head", "full"):
                cur = sweep.get((eps, rec, "accuracy"), {})
                seeds = sorted(set(ref) & set(cur))
                if not seeds:
                    continue
                t = paired_test([ref[s] for s in seeds], [cur[s] for s in seeds])
                if not t:
                    continue
                loss_pp = -t["mean_diff"] * 100
                lo, hi = -t["ci_high"] * 100, -t["ci_low"] * 100
                ok = "PASS" if loss_pp <= 2.0 else "FAIL"
                L.append(f"   eps={eps:<5} recipe={rec:<5} n={t['n']}   "
                         f"accuracy loss vs no-DP = {loss_pp:+.2f} pp   "
                         f"95% CI [{lo:+.2f}, {hi:+.2f}] pp   → {ok}")
                best = best or ok
        if best is None:
            L.append("   — needs the eps=inf reference AND an eps<=1 point "
                     "at shared seeds.")
    else:
        L.append("   — epsilon_sweep.csv not found.")

    # ── 4. component ablation ───────────────────────────────────────
    abl = p6 / "ablation.csv"
    L.append(section("4. COMPONENT ABLATION  (effect of removing each component)"))
    if abl.exists():
        with open(abl) as f:
            rows = list(csv.DictReader(f))
        a0 = next((r for r in rows if r.get("arm") == "A0"), None)

        def fnum(r, k):
            try:
                return float(r.get(k, ""))
            except (TypeError, ValueError):
                return None
        base = fnum(a0, "test_macro_auc") if a0 else None
        if base is None:
            L.append("   — A0 (full system) missing; nothing to compare against.")
        else:
            L.append(f"   {'arm':<5}{'removes':<9}{'AUROC':>10}{'ΔvsA0':>10}   note")
            L.append("   " + "-" * 56)
            for r in rows:
                v = fnum(r, "test_macro_auc")
                if v is None:
                    continue
                d = v - base
                note = ("contributes" if d < -1e-4 else
                        "no measurable contribution")
                L.append(f"   {r.get('arm',''):<5}{r.get('removes','—'):<9}"
                         f"{v:>10.4f}{d:>+10.4f}   "
                         f"{'' if r.get('arm')=='A0' else note}")
            L.append("\n   Single-seed deltas — a component whose Δ is smaller "
                     "than the seed sd\n   in section 1 is NOT evidenced; re-run "
                     "the ablation across seeds to settle it.")
    else:
        L.append("   — ablation.csv not found; run scripts/component_ablation.py.")

    # ── 5. joint evaluation ─────────────────────────────────────────
    je = p6 / "joint_eval.csv"
    L.append(section("5. JOINT EVALUATION  (S0–S4)"))
    if je.exists():
        with open(je) as f:
            rows = list(csv.DictReader(f))
        L.append(f"   {'sys':<5}{'name':<22}{'acc':>9}{'AUROC':>9}{'ΔaccS0':>9}")
        L.append("   " + "-" * 54)
        for r in rows:
            def s(k, fmt="{:>9.4f}"):
                try:
                    return fmt.format(float(r[k]))
                except (KeyError, TypeError, ValueError):
                    return f"{'—':>9}"
            L.append(f"   {r['system']:<5}{r['name'][:21]:<22}"
                     f"{s('accuracy')}{s('macro_auc')}"
                     f"{s('acc_loss_vs_S0_pp', '{:>+9.2f}')}")
        L.append("\n   Single run per system — these are point estimates, not "
                 "intervals.\n   Repeat across seeds before quoting any "
                 "difference as a finding.")
    else:
        L.append("   — joint_eval.csv not found; run scripts/joint_eval.py.")

    # ── warnings ────────────────────────────────────────────────────
    L.append(section("POWER / SAMPLE-SIZE WARNINGS"))
    if warnings:
        for w in sorted(set(warnings)):
            L.append(f"   ⚠ {w}")
        L.append(f"\n   Phase 6 §6.4.1 requires >= {MIN_SEEDS} seeds. Results "
                 f"above with fewer\n   are reported for completeness but must "
                 f"not be quoted as significant.")
    elif not sweep:
        # "no warnings" must not read as "all clear" when nothing was measured.
        L.append("   n/a — no multi-seed results exist yet, so seed count "
                 "could not be checked.")
    else:
        L.append("   none — every reported point meets the seed requirement.")

    text = "\n".join(L) + "\n"
    out_path.write_text(text)
    print(text)
    print(f"Written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
