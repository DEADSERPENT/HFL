"""fig04_arms.py — Fig. 4: which arm moves. AUPRC of the record and the
individual arm against k on both corpora (paper/figs.md, Fig. 4). The
individual arm's min-max range is shaded; the same y-span is used per panel so
slopes are comparable."""
import csv
from collections import defaultdict
import numpy as np
from _figstyle import plt, RES, SINGLE, C, tci, panel, ygrid, save

SPAN = 0.12


def load(ds):
    path = RES / "phase5" / "k_scaling" / ds / f"k_scaling_{ds}.csv"
    by = defaultdict(list)
    for r in csv.DictReader(open(path)):
        by[(r["arm"], int(r["k"]))].append(float(r["auprc"]))
    return by


def main():
    fig, axs = plt.subplots(1, 2, figsize=(SINGLE, 2.3))
    for ax, ds, letter, title in zip(axs, ("vitaldb", "eicu"), "ab",
                                     ("VitalDB", "eICU")):
        by = load(ds)
        ks = sorted({k for _, k in by})
        x = np.arange(len(ks))
        for arm, col, mk, ls, lab in (("sample", C["record"], "s", "--", "record-level"),
                                      ("patient", C["indiv"], "o", "-", "patient-level")):
            m = [tci(by[(arm, k)]) for k in ks]
            ax.errorbar(x, [a for a, _ in m], yerr=[h for _, h in m], color=col,
                        marker=mk, ls=ls, ms=3.5, elinewidth=0.75, label=lab)
        ind = [np.mean(by[("patient", k)]) for k in ks]
        ax.axhspan(min(ind), max(ind), color=C["indiv"], alpha=0.12, lw=0)
        allv = [v for key in by for v in by[key]]
        lo = (min(allv) + max(allv)) / 2 - SPAN / 2
        ax.set_ylim(lo, lo + SPAN)
        ax.set_xticks(x, [str(k) for k in ks])
        ax.set_xlabel("$k$")
        ax.set_title(title, fontsize=8)
        ygrid(ax)
        panel(ax, letter, x=-0.32)
    axs[0].set_ylabel("Average precision")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, [f"{x} arm" for x in l], loc="upper center", ncol=2,
               handlelength=1.8, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(w_pad=0.6, rect=(0, 0, 1, 0.9))
    save(fig, "fig04_arms")


if __name__ == "__main__":
    main()
