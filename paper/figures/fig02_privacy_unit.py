"""fig02_privacy_unit.py — Fig. 2: where the privacy unit is fixed
(paper/figs.md, Fig. 2). (a) per-record clipping bounds a window, so a
patient's influence is k_p C; summing first and clipping once bounds the
patient at C. (b) fraction of individuals clipped per records-per-individual
bin on eICU, read from data/fig02_clip_bins.csv (transcribed from the frozen
preregistration amendment N-A1, the only record of that probe)."""
import csv
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch
from _figstyle import plt, HERE, SINGLE, C, panel, ygrid, save

KP = 8                     # windows drawn for the illustrative patient


def arr(ax, p, q, col, lw=0.9, ms=5):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=ms,
                                 lw=lw, color=col, shrinkA=0, shrinkB=0))


def main():
    rows, meta = [], {}
    with open(HERE / "data" / "fig02_clip_bins.csv") as f:
        for line in f:
            if line.startswith("# spearman"):
                meta = dict(kv.split("=") for kv in line.split(":")[1].split())
        f.seek(0)
        rows = list(csv.DictReader(l for l in f if not l.startswith("#")))

    fig = plt.figure(figsize=(SINGLE, 3.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.15, 1], hspace=0.45)
    ax = fig.add_subplot(gs[0]); ax.set_xlim(0, 10); ax.set_ylim(0, 5.2)
    ax.set_aspect("equal"); ax.axis("off")
    rng = np.random.default_rng(3)
    ang = rng.uniform(-0.5, 0.5, KP) + 0.35
    mag = rng.uniform(0.9, 1.6, KP)

    # row 1: record-level — clip each, then sum
    y = 3.7
    ax.text(0, y + 1.35, "Record level: clip each window, then sum", fontsize=6.8,
            color=C["record"], weight="bold")
    for i in range(KP):
        x0 = 0.35 + i * 0.55
        ax.add_patch(Circle((x0, y), 0.42, fill=False, ls=":", lw=0.5, ec="#888888"))
        L = min(mag[i], 1.0) * 0.42
        arr(ax, (x0, y), (x0 + L * np.cos(ang[i]), y + L * np.sin(ang[i])),
            C["record"], lw=0.8, ms=4)
    ax.text(4.95, y, "$\\Rightarrow$", fontsize=9, va="center")
    tot = np.array([sum(min(m, 1) * np.cos(a) for m, a in zip(mag, ang)),
                    sum(min(m, 1) * np.sin(a) for m, a in zip(mag, ang))]) * 0.42
    s = 2.3 / np.linalg.norm(tot)   # tip clears the label
    arr(ax, (5.6, y - 0.6), (5.6 + tot[0] * s, y - 0.6 + tot[1] * s), C["record"], lw=1.4)
    ax.text(9.95, y - 0.2, "sensitivity\n$k_p\\,C$", fontsize=6.8, ha="right",
            va="center", color=C["record"])

    # row 2: individual-level — sum, then clip once
    y = 1.0
    ax.text(0, y + 1.35, "Individual level: sum the windows, then clip once",
            fontsize=6.8, color=C["indiv"], weight="bold")
    xs = 0.35
    px, py = xs, y - 0.4
    for i in range(KP):
        dx, dy = mag[i] * 0.42 * np.cos(ang[i]) * 0.55, mag[i] * 0.42 * np.sin(ang[i]) * 0.55
        arr(ax, (px, py), (px + dx, py + dy), C["indiv"], lw=0.6, ms=3)
        px, py = px + dx, py + dy
    ax.text(4.95, y, "$\\Rightarrow$", fontsize=9, va="center")
    cx, cy = 6.4, y - 0.1
    ax.add_patch(Circle((cx, cy), 0.75, fill=False, ls=":", lw=0.6, ec="#888888"))
    v = np.array([px - xs, py - (y - 0.4)]); v = v / np.linalg.norm(v) * 0.75
    arr(ax, (cx, cy), (cx + v[0], cy + v[1]), C["indiv"], lw=1.4)
    ax.text(cx, cy - 0.95, "radius $C$", fontsize=6, ha="center")
    ax.text(9.95, y - 0.1, "sensitivity\n$C$", fontsize=6.8, ha="right",
            va="center", color=C["indiv"])
    panel(ax, "a", x=-0.13, y=0.93)

    # (b) saturation per bin
    ax = fig.add_subplot(gs[1])
    x = np.arange(len(rows))
    sat = [float(r["saturation"]) for r in rows]
    ax.bar(x, sat, 0.6, color=C["indiv"])
    for xi, r, sv in zip(x, rows, sat):
        ax.text(xi, sv + 0.012, f"$n$={int(r['patients']):,}", ha="center", fontsize=6.3)
    ax.set_xticks(x, [r["k_bin"].replace("-", "–") for r in rows])
    ax.set_xlabel("Records per individual")
    ax.set_ylabel("Fraction clipped")
    ax.set_ylim(0, 0.6)
    if meta:
        p = float(meta["p"])
        e = int(np.floor(np.log10(p)))
        ax.text(0.02, 0.95, f"Spearman $\\rho={float(meta['rho']):.3f}$, "
                f"$p={p / 10**e:.1f}\\times10^{{{e}}}$", transform=ax.transAxes,
                va="top", fontsize=6.5)
    ygrid(ax); panel(ax, "b", x=-0.2)
    save(fig, "fig02_privacy_unit")


if __name__ == "__main__":
    main()
