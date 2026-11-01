"""fig05_init_vs_subset.py — Fig. 5: decomposition of the recipe's advantage
across epsilon (paper/figs.md, Fig. 5). Initialization step = full_pre - full
(B4 -> B7); subset step = head - full_pre (B7 -> B6); both paired by seed,
macro AUROC, Student-t 95 % intervals."""
import csv
from collections import defaultdict
import numpy as np
from _figstyle import plt, RES, DOUBLE, C, tci, panel, ygrid, save


def load(ds):
    by = defaultdict(dict)
    for r in csv.DictReader(open(RES / "phase5" / "epsilon_sweep" / ds /
                                 "epsilon_sweep.csv")):
        by[(r["epsilon"], r["seed"])][r["recipe"]] = float(r["macro_auc"])
    eps = sorted({e for e, _ in by}, key=lambda e: (e == "inf", float(e) if e != "inf" else 0))
    init, sub = {}, {}
    for e in eps:
        rows = [v for (ee, _), v in by.items() if ee == e
                and {"full", "full_pre", "head"} <= v.keys()]
        init[e] = [v["full_pre"] - v["full"] for v in rows]
        sub[e] = [v["head"] - v["full_pre"] for v in rows]
    return eps, init, sub


def main():
    fig, axs = plt.subplots(1, 2, figsize=(DOUBLE, 2.5), sharey=True)
    for ax, ds, letter, title in zip(axs, ("vitaldb", "wear"), "ab",
                                     ("VitalDB (clinical)", "WEAR (wearable)")):
        eps, init, sub = load(ds)
        x = np.arange(len(eps)); w = 0.36
        mi = [tci(init[e]) for e in eps]; ms = [tci(sub[e]) for e in eps]
        ax.bar(x - w / 2, [a for a, _ in mi], w, yerr=[h for _, h in mi],
               color=C["pre"], ecolor="#333333", error_kw=dict(elinewidth=0.75),
               label="initialization (random $\\to$ pretrained)")
        ax.bar(x + w / 2, [a for a, _ in ms], w, yerr=[h for _, h in ms],
               color=C["indiv"], ecolor="#333333", error_kw=dict(elinewidth=0.75),
               hatch="////", edgecolor="white", lw=0,
               label="privatized subset (full $\\to$ head)")
        ax.axhline(0, color="#444444", lw=0.5)
        ax.set_xticks(x, [("$\\infty$\n(no DP)" if e == "inf" else e) for e in eps])
        ax.set_xlabel("Privacy budget $\\varepsilon$")
        ax.set_title(title, fontsize=8)
        n = len(init[eps[0]])
        ax.text(0.98, 0.95, f"$n={n}$ seeds", transform=ax.transAxes, ha="right",
                va="top", fontsize=7)
        ygrid(ax)
        panel(ax, letter, x=-0.10 if letter == "a" else -0.04)
    # direct labels on the panel with free space (b)
    ax = axs[1]; eps, init, sub = load("wear"); w = 0.36
    i4 = eps.index("4") if "4" in eps else 3
    ax.annotate("solid: initialization effect\n(same budget, pretrained start)",
                xy=(i4 - w / 2, np.mean(init[eps[i4]])), xytext=(3.2, 0.33),
                fontsize=6.3, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color="#555555", lw=0.5))
    ax.annotate("hatched: privatized-subset effect\n(noise on head only), $\\approx 0$",
                xy=(i4 + 1 + w / 2, 0.003), xytext=(3.2, 0.21),
                fontsize=6.3, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color="#555555", lw=0.5))
    axs[0].set_ylabel("$\\Delta$AUROC")
    axs[0].legend(loc="upper center", bbox_to_anchor=(0.5, 0.88))
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig05_init_vs_subset")


if __name__ == "__main__":
    main()
