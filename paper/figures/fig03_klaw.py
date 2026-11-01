"""fig03_klaw.py — Fig. 3: cost of the individual-level guarantee against records
per individual k, VitalDB with its fitted law and eICU against the frozen
forecast (paper/figs.md, Fig. 3).

Gap = AUPRC(record arm) - AUPRC(individual arm), paired by (k, seed).
The law gap(k) = A(1 - exp(-b(k-1))) is read from the frozen forecast in
document/01_planning/PREREGISTRATION_EICU.md, not refitted: panel (b) tests
the curve registered before eICU existed, and refitting the unrounded VitalDB
means gives a slightly different b (0.882 vs the registered 0.8827).
"""
import csv
import json
import re
from collections import defaultdict
import numpy as np
from _figstyle import plt, RES, DOUBLE, C, tci, panel, ygrid, save

PREREG = RES.parents[1] / "document" / "01_planning" / "PREREGISTRATION_EICU.md"

BAND = 0.030          # pre-registered acceptance band around the forecast
CTRL_TOL = 0.020      # k = 1 control tolerance


def gaps(ds):
    path = RES / "phase5" / "k_scaling" / ds / f"k_scaling_{ds}.csv"
    by = defaultdict(dict)
    for r in csv.DictReader(open(path)):
        by[(int(r["k"]), int(r["seed"]))][r["arm"]] = float(r["auprc"])
    out = defaultdict(list)
    for (k, sd), arms in sorted(by.items()):
        if {"sample", "patient"} <= arms.keys():
            out[k].append(arms["sample"] - arms["patient"])
    return dict(sorted(out.items()))


def frozen_law():
    """(A, b) of the registered forecast, from its ``A = ...`` / ``b = ...`` lines."""
    txt = PREREG.read_text()
    get = lambda name: float(re.search(rf"^{name} = ([0-9.]+)", txt, re.M).group(1))
    return get("A"), get("b")


def law(k, A, b):
    return A * (1 - np.exp(-b * (np.asarray(k, float) - 1)))


def draw(ax, g, curve, dashed, show_curve=True):
    ks = list(g)
    rng = np.random.default_rng(0)
    for k in ks:
        x = np.log2(k) + rng.uniform(-0.06, 0.06, len(g[k]))
        ax.plot(x, g[k], "o", mfc="none", mec=C["indiv"], mew=0.6, ms=3.2,
                alpha=0.8, zorder=2)
    m = [tci(g[k]) for k in ks]
    ax.errorbar(np.log2(ks), [a for a, _ in m], yerr=[h for _, h in m],
                fmt="o", color=C["indiv"], ms=4.5, elinewidth=0.75, zorder=3,
                label="mean $\\pm$ 95 % CI")
    kk = np.linspace(1, max(ks), 200)
    if show_curve:
        ax.plot(np.log2(kk), law(kk, *curve), ls="--" if dashed else "-",
                color=C["ref"], lw=0.9, zorder=1,
                label="frozen forecast" if dashed else "fitted law")
    if dashed:
        ax.fill_between(np.log2(kk), law(kk, *curve) - BAND,
                        law(kk, *curve) + BAND, color=C["ctrl"], alpha=0.15,
                        lw=0, label="acceptance band $\\pm$0.030")
    ax.add_patch(plt.Rectangle((-0.25, -CTRL_TOL), 0.5, 2 * CTRL_TOL,
                               color=C["ctrl"], alpha=0.25, lw=0, zorder=0))
    ax.text(-0.22, -CTRL_TOL - 0.004, "$k=1$ control", ha="left", va="top",
            fontsize=6.5)
    ax.axhline(0, color="#444444", lw=0.4)
    ax.set_xticks(np.log2(ks), [str(k) for k in ks])
    ax.set_xlabel("Records per individual $k$")
    ygrid(ax)


def main():
    gv, ge = gaps("vitaldb"), gaps("eicu")
    A, b = frozen_law()
    print(f"frozen A={A:.4f} b={b:.4f}")

    fig, axs = plt.subplots(1, 2, figsize=(DOUBLE, 2.6), sharey=True)
    draw(axs[0], gv, (A, b), dashed=False, show_curve=False)
    # Proposition 2: one-parameter A(1 - 1/k), fitted on the post-fix grid
    th = json.load(open(RES / "phase5" / "k_scaling" / "klaw_theory_check.json"))
    Av = th["vitaldb"]["inv_k"]["A"]
    kk = np.linspace(1, 8, 200)
    axs[0].plot(np.log2(kk), Av * (1 - 1 / kk), color="k", lw=1.0,
                label="scaling hypothesis $A(1-1/k)$")
    draw(axs[1], ge, (A, b), dashed=True)
    axs[0].set_ylabel("AUPRC gap (record $-$ individual)")
    axs[0].set_ylim(-0.08, 0.13)
    axs[0].text(0.03, 0.97, f"$A={Av:.4f}$ (one parameter)", transform=axs[0].transAxes,
                va="top", fontsize=7)

    ks = list(ge)
    if 8 in ge and 16 in ge:
        d = [b16 - b8 for b8, b16 in zip(ge[8], ge[16])]
        m, h = tci(d)
        x8, x16 = np.log2(8), np.log2(16)
        y = max(np.mean(ge[k]) + tci(ge[k])[1] for k in (8, 16)) + 0.008
        axs[1].plot([x8, x8, x16, x16], [y - 0.004, y, y, y - 0.004], color="k", lw=0.6)
        axs[1].text((x8 + x16) / 2, y + 0.003,
                    f"$\\Delta={m:+.4f}$ [{m-h:+.3f}, {m+h:+.3f}]",
                    ha="center", fontsize=6.5)
    xk = np.log2(32)
    axs[1].axvspan(xk - 0.35, xk + 0.35, color=C["ctrl"], alpha=0.12, hatch="///",
                   lw=0)
    axs[1].text(xk, 0.0, "untested ($k=32$)", ha="center", va="center",
                fontsize=6.5, rotation=90)
    axs[1].set_xlim(-0.4, xk + 0.45)
    axs[1].set_xticks(np.log2(ks + [32]), [str(k) for k in ks] + ["32"])
    h0, l0 = axs[0].get_legend_handles_labels()
    h1, l1 = axs[1].get_legend_handles_labels()
    seen = dict(zip(l0 + l1, h0 + h1))
    fig.legend(seen.values(), seen.keys(), loc="lower center", ncol=4,
               bbox_to_anchor=(0.5, -0.01))
    panel(axs[0], "a"); panel(axs[1], "b", x=-0.06)
    axs[0].set_title("VitalDB (clinical)", fontsize=8)
    axs[1].set_title("eICU (external)", fontsize=8)
    fig.tight_layout(w_pad=1.0, rect=(0, 0.07, 1, 1))
    save(fig, "fig03_klaw")


if __name__ == "__main__":
    main()
