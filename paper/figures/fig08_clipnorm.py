"""fig08_clipnorm.py — Fig. 8: normalized clipping on eICU's natural partition,
amendment N-A2 (paper/figs.md, Fig. 8). (a) clip saturation per round per
rule; (b) AUPRC per rule; (c) paired difference k - none against the
registered threshold, with the one-sided 95 % upper bound."""
import csv
import json
from collections import defaultdict
import numpy as np
from scipy import stats as st
from _figstyle import plt, RES, DOUBLE, C, tci, panel, ygrid, save

D = RES / "phase5" / "nd_clipnorm" / "eicu"
RULES = (("none", "none", C["indiv"], "-", "o"),
         ("sqrt_k", "$\\sqrt{k}$", C["purple"], "-.", "^"),
         ("k", "$k$", C["record"], "--", "s"))
THRESH = 0.010


def main():
    rows = json.load(open(D / "nd_clipnorm_eicu_natural.json"))["rows"]
    seeds = sorted({r["seed"] for r in rows})
    fig, axs = plt.subplots(1, 3, figsize=(DOUBLE, 2.4),
                            gridspec_kw=dict(width_ratios=[1.25, 0.9, 1.1]))

    ax = axs[0]
    for mode, lab, col, ls, mk in RULES:
        curves = []
        for sd in seeds:
            h = list(csv.DictReader(open(D / f"hist_natural_seed{sd}_{mode}.csv")))
            r = [int(x["global_round"]) for x in h]
            s = [float(x["clip_saturation"]) for x in h]
            ax.plot(r, s, ls=ls, color=col, lw=0.4, alpha=0.5)
            curves.append(s)
        n = min(map(len, curves))
        ax.plot(range(1, n + 1), np.mean([c[:n] for c in curves], 0), ls=ls,
                color=col, lw=1.4, marker=mk, ms=3, label=lab)
    ax.set_xlabel("Global round")
    ax.set_ylabel("Fraction of individuals clipped")
    ax.set_ylim(0, 1.03)
    ax.legend(title="normalization", title_fontsize=6.5, loc="lower left")
    ygrid(ax); panel(ax, "a", x=-0.2)

    ax = axs[1]
    by = defaultdict(dict)
    for r in rows:
        by[r["mode"]][r["seed"]] = r["auprc"]
    for i, (mode, lab, col, ls, mk) in enumerate(RULES):
        v = [by[mode][s] for s in seeds]
        ax.plot([i] * len(v), v, mk, mfc="none", mec=col, ms=3.5, mew=0.7)
        m, h = tci(v)
        ax.errorbar(i, m, yerr=h, fmt=mk, color=col, ms=5, elinewidth=0.75)
    ax.set_xticks(range(3), [r[1] for r in RULES])
    ax.set_xlim(-0.5, 2.5)
    ax.set_xlabel("Normalization")
    ax.set_ylabel("Average precision")
    ygrid(ax); panel(ax, "b", x=-0.36)

    ax = axs[2]
    d = [by["k"][s] - by["none"][s] for s in seeds]
    m, h = tci(d)
    n = len(d)
    sd = np.std(d, ddof=1)
    ub = m + st.t.ppf(0.95, n - 1) * sd / np.sqrt(n)
    ax.axvspan(THRESH, 0.03, color=C["ctrl"], alpha=0.15, lw=0)
    ax.axvline(THRESH, color="k", ls="--", lw=0.8)
    ax.axvline(0, color="#444444", lw=0.5)
    ax.errorbar(m, 0.5, xerr=h, fmt="o", color=C["record"], ms=5, elinewidth=0.9)
    ax.plot([ub, ub], [0.38, 0.62], color=C["record"], lw=2.2)
    ax.text(ub - 0.001, 0.68, f"one-sided\nUB {ub:+.4f}", ha="right", fontsize=6.5)
    ax.text(m, 0.32, f"{m:+.4f}", ha="center", va="top", fontsize=6.5)
    ax.text(0.0205, 0.88, "recovery\npredicted", ha="center", fontsize=6.5)
    ax.text(THRESH, 0.04, f" threshold {THRESH:+.3f}", fontsize=6.3)
    ax.set_xlim(-0.02, 0.03)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("$\\Delta$AUPRC ($k$ $-$ none)")
    panel(ax, "c", x=-0.05)
    print(f"diff={m:+.4f} +-{h:.4f} UB={ub:+.4f} n={n}")
    fig.tight_layout(w_pad=0.8)
    save(fig, "fig08_clipnorm")


if __name__ == "__main__":
    main()
