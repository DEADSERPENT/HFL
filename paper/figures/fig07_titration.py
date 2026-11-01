"""fig07_titration.py — Fig. 7: the fusion-balance titration F-A1 on eICU
(paper/figs.md, Fig. 7). (a) lever calibration on arm B only; (b) the three
arms at parity beside the matched control; (c) seed-paired gain."""
import json
import numpy as np
from scipy import stats as st
from _figstyle import plt, RES, DOUBLE, C, tci, panel, ygrid, save

P5 = RES / "phase5"
THRESH = 0.015        # registered minimum gain


def runs(f):
    return json.load(open(P5 / f))["runs"]


def main():
    fig, axs = plt.subplots(1, 3, figsize=(DOUBLE, 2.4),
                            gridspec_kw=dict(width_ratios=[1, 1.1, 0.9]))
    alpha = float((P5 / "fusbal_alpha.txt").read_text().strip())
    ctrl = runs("ablation_eicu_matched.json")
    test = runs("fusbal_test_n0.4.json")

    # (a) calibration
    ax = axs[0]
    cal = sorted(P5.glob("fusbal_calib_n*.json"))
    xs, ys = [], []
    for f in cal:
        a = float(f.stem.split("_n")[1])
        for r in runs(f.name)["b"]:
            ax.plot(a, r["auroc"], "o", mfc="none", mec=C["record"], ms=3.2, mew=0.7)
        xs.append(a); ys.append(np.mean([r["auroc"] for r in runs(f.name)["b"]]))
    xs.append(1.0); ys.append(np.mean([r["auroc"] for r in ctrl["b"]]))
    ax.plot(xs, ys, "s-", color=C["record"], ms=3.5, label="arm B (admission)")
    aA = np.mean([r["auroc"] for r in ctrl["a"]])
    ax.axhline(aA, ls="--", color=C["indiv"], lw=0.9, label="arm A (vitals)")
    ax.axvline(alpha, color="#555555", lw=0.6, ls=":")
    ax.text(alpha + 0.02, 0.83, f"$\\alpha^*={alpha:g}$", fontsize=7)
    ax.set_xlabel("Signal fraction $\\alpha$ of arm B")
    ax.set_ylabel("AUROC")
    ax.legend(loc="lower right", fontsize=6.3)
    ygrid(ax); panel(ax, "a", x=-0.28)

    # (b) arms at parity vs matched control
    ax = axs[1]
    arms = (("a", "vitals (A)", C["indiv"], "o"), ("b", "admission (B)", C["record"], "s"),
            ("both", "fused", C["fused"], "*"))
    for g, (src, x0, light) in enumerate(((test, 0, False), (ctrl, 4, True))):
        for i, (k, lab, col, mk) in enumerate(arms):
            v = [r["auroc"] for r in src[k]]
            m, h = tci(v)
            x = x0 + i
            ax.plot([x] * len(v), v, mk, mfc="none", mec=col, ms=3, mew=0.6,
                    alpha=0.6 if light else 0.8)
            ax.errorbar(x, m, yerr=h, fmt=mk, color=col, ms=5 if mk != "*" else 7,
                        elinewidth=0.75, alpha=0.6 if light else 1,
                        label=lab if g == 0 else None)
    ax.set_xticks([1, 5], [f"titrated ($\\alpha^*={alpha:g}$)", "matched control"])
    ax.set_xlim(-0.7, 6.7)
    ax.set_ylabel("AUROC")
    ax.legend(loc="upper left", fontsize=6.3)
    ygrid(ax); panel(ax, "b", x=-0.24)

    # (c) paired gain over best single arm
    ax = axs[2]
    a = {r["seed"]: r["auroc"] for r in test["a"]}
    b = {r["seed"]: r["auroc"] for r in test["b"]}
    f = {r["seed"]: r["auroc"] for r in test["both"]}
    seeds = sorted(set(a) & set(b) & set(f))
    best_arm = "a" if np.mean(list(a.values())) >= np.mean(list(b.values())) else "b"
    best = a if best_arm == "a" else b
    d = []
    for sd in seeds:
        ax.plot([0, 1], [best[sd], f[sd]], "-o", color=C["fused"], ms=3, lw=0.8)
        d.append(f[sd] - best[sd])
    m, h = tci(d)
    p = st.ttest_1samp(d, 0).pvalue
    ax.set_xticks([0, 1], ["best single", "fused"])
    ax.set_xlim(-0.3, 1.3)
    ax.set_ylabel("AUROC")
    ax.text(0.03, 0.97, f"$+{m:.4f}\\pm{h:.4f}$\n{sum(x > 0 for x in d)}/{len(d)} seeds, $p={p:.3f}$",
            transform=ax.transAxes, ha="left", va="top", fontsize=6.5)
    ygrid(ax); panel(ax, "c", x=-0.32)
    print(f"alpha*={alpha} gain={m:+.4f}+-{h:.4f} p={p:.4f} n={len(d)} thresh={THRESH}")
    fig.tight_layout(w_pad=0.8)
    save(fig, "fig07_titration")


if __name__ == "__main__":
    main()
