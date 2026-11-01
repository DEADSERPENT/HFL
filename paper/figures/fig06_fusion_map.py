"""fig06_fusion_map.py — Fig. 6: fusion gain against modality imbalance and
headroom (paper/figs.md, Fig. 6). Every point is recomputed from its ablation
JSON (runs.{a,b,both}[].auroc, mean over seeds)."""
import json
import numpy as np
from _figstyle import plt, RES, SINGLE, CORPUS, save, ygrid

P5 = RES / "phase5"
POINTS = [  # label, corpus, condition, file, label offset (points)
    ("VitalDB", "vitaldb", "natural", "ablation_vitaldb.json", (-48, -30)),
    ("WEAR", "wear", "natural", "ablation_wear.json", (14, 10)),
    ("eICU natural", "eicu", "natural", "ablation_eicu.json", (2, -44)),
    ("eICU matched", "eicu", "matched", "ablation_eicu_matched.json", (-36, -44)),
    ("eICU admission\nzeroed", "eicu", "zeroed", "ablation_eicu_noapache.json", (12, 16)),
    ("eICU titrated", "eicu", "titrated", "fusbal_test_n0.4.json", (-26, 22)),
]
COND = dict(natural=("o", "natural"), matched=("s", "matched control"),
            zeroed=("D", "admission zeroed"), titrated=("*", "titrated to parity"))
SCALE = 9000          # bubble area per unit AUROC gain


def stats_of(f):
    r = json.load(open(P5 / f))["runs"]
    m = {k: np.mean([x["auroc"] for x in v]) for k, v in r.items()}
    best = max(m["a"], m["b"])
    return abs(m["a"] - m["b"]), 1 - best, m["both"] - best, len(r["both"])


def main():
    fig, ax = plt.subplots(figsize=(SINGLE, 2.9))
    xy = {}
    for lab, ds, cond, f, off in POINTS:
        imb, head, gain, n = stats_of(f)
        col = CORPUS[ds][0]
        size = max(abs(gain) * SCALE, 12) * (1.6 if cond == "titrated" else 1)
        ax.scatter(imb, head, s=size, marker=COND[cond][0],
                   facecolor=col if gain > 0 else "none", edgecolor=col,
                   alpha=0.75 if gain > 0 else 1, lw=0.9, zorder=3)
        xy[lab] = (imb, head)
        ax.annotate(f"{lab}\n({gain:+.4f})" if lab.startswith("eICU n") or lab.startswith("eICU m") else f"{lab} ({gain:+.4f})", (imb, head), xytext=off,
                    textcoords="offset points", fontsize=6.0, va="center",
                    linespacing=1.1,
                    arrowprops=dict(arrowstyle="-", color="#999999", lw=0.4,
                                    shrinkA=1, shrinkB=5))
        print(f"{lab:22s} imb={imb:.4f} headroom={head:.4f} gain={gain:+.4f} n={n}")
    path = ["eICU matched", "eICU admission\nzeroed", "eICU titrated"]
    for i, (a, b) in enumerate(zip(path, path[1:]), 1):
        ax.annotate("", xy=xy[b], xytext=xy[a],
                    arrowprops=dict(arrowstyle="-|>", color="#555555", lw=0.8,
                                    mutation_scale=7, shrinkA=7, shrinkB=9))
        mx = np.sqrt(xy[a][0] * xy[b][0]); my = (xy[a][1] + xy[b][1]) / 2
        ax.text(mx, my, str(i), fontsize=6, ha="center", va="center", zorder=5,
                bbox=dict(boxstyle="circle,pad=0.15", fc="white", ec="#555555", lw=0.5))
    ax.set_xscale("log")
    ax.set_xlim(0.001, 0.4)
    ax.set_ylim(-0.02, 0.37)
    ax.set_xlabel("Modality imbalance $|\\mathrm{AUROC}_A-\\mathrm{AUROC}_B|$")
    ax.set_ylabel("Headroom $1-\\max(\\mathrm{AUROC}_A,\\mathrm{AUROC}_B)$")
    for ds in ("vitaldb", "wear", "eicu"):
        ax.scatter([], [], s=22, color=CORPUS[ds][0],
                   label={"vitaldb": "VitalDB", "wear": "WEAR", "eicu": "eICU"}[ds])
    for c, (mk, t) in COND.items():
        ax.scatter([], [], s=22, marker=mk, facecolor="none", edgecolor="#444444",
                   lw=0.8, label=t)
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0.0, 0.13), fontsize=5.8, ncol=1, handletextpad=0.3,
                    labelspacing=0.35, title="color: corpus; shape: condition",
                    title_fontsize=5.8, alignment="left")
    ax.add_artist(leg)
    hs = [ax.scatter([], [], s=g * SCALE, color="#BBBBBB", ec="#777777", lw=0.5)
          for g in (0.01, 0.03)]
    ax.legend(hs, ["0.01", "0.03"], loc="lower right", fontsize=5.8, ncol=2,
              title="area: |gain|; hollow: gain < 0", title_fontsize=5.8,
              borderpad=0.5, handletextpad=0.6, columnspacing=1.0, alignment="left")
    ygrid(ax)
    save(fig, "fig06_fusion_map")


if __name__ == "__main__":
    main()
