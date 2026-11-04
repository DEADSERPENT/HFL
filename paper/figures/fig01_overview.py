"""fig01_overview.py — Fig. 1: overview of PP-HFM (paper/figs.md, Fig. 1).
Three tiers left to right on shaded bands, drawn with flat 2-D icons
(_icons.py), and a ledger strip along the bottom stating the guarantee.

Every figure on the drawing is read from a file: the ledger from
results/phase5/privacy_total_vitaldb.json (the headline run), tau_e and the
sparsification ratio from config/hfl_config.json.

    python fig01_overview.py --core    -> fig01_overview_core.{pdf,png}
(--core is kept for the build scripts; the conformal variant was retired with
the component.)"""
import json
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from _figstyle import plt, RES, DOUBLE, C, save
from _icons import Icons

SIM = RES.parent
LEDGER = json.load(open(RES / "phase5" / "privacy_total_vitaldb.json"))
CFG = json.load(open(SIM / "config" / "hfl_config.json"))
TAU_E = CFG["federated_learning"]["tau_e"]
SPARSITY = CFG["model"]["sparsification_ratio"]
INK = "#2B2B2B"


def box(ax, x, y, w, h, text="", fc="white", ec=INK, lw=0.6, fs=6.3, ls="-",
        r=0.012, color=INK, weight="normal", z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=color, weight=weight, zorder=z + 0.1, linespacing=1.15)


def arrow(ax, p, q, lw=0.7, color=INK, ls="-", rad=0.0, ms=6, z=4):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=ms, lw=lw,
                                 color=color, ls=ls, shrinkA=0, shrinkB=0, zorder=z,
                                 connectionstyle=f"arc3,rad={rad}"))


def main():
    fig = plt.figure(figsize=(DOUBLE, 2.9))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ic = Icons(ax)

    # tier bands (same palette as the workflow figure)
    for (x0, x1), t, fc, ec in (((0.005, 0.50), "Client tier (hospitals)", "#FCEBDD", "#EBB48C"),
                                ((0.51, 0.745), "Edge tier", "#E3EEF9", "#9DBFE3"),
                                ((0.755, 0.995), "Cloud tier", "#E2F2EA", "#93CDB0")):
        ax.add_patch(FancyBboxPatch((x0, 0.105), x1 - x0, 0.89, fc=fc, ec=ec, lw=0.6,
                                    boxstyle="round,pad=0,rounding_size=0.012", zorder=0))
        ax.text((x0 + x1) / 2, 0.975, t, ha="center", va="top", fontsize=8,
                weight="bold", style="italic")

    # ── client k ────────────────────────────────────────────────────────
    box(ax, 0.015, 0.39, 0.475, 0.545, fc="white", ec=C["indiv"], ls="--", lw=0.9,
        r=0.02, z=1)
    ic.hospital(0.045, 0.855, 0.30)
    ax.text(0.072, 0.862, "client $k$", fontsize=7, weight="bold", va="center")
    yA, yB = 0.69, 0.49
    ic.patient(0.052, yA - 0.005, 0.40)
    ic.monitor(0.112, yA + 0.02, 0.28)
    ax.text(0.08, yA - 0.092, "patient $p$: windows\n$W_p=\\{w_1,\\ldots,w_k\\}$",
            fontsize=5.6, ha="center", va="center", linespacing=1.2)
    ic.database(0.045, yB, 0.24)
    ax.text(0.07, yB, "admission\nrecord of $p$", fontsize=5.6, va="center")
    for y, t in ((yA, "encoder A\nfrozen"), (yB, "encoder B\nfrozen")):
        box(ax, 0.165, y - 0.055, 0.075, 0.11, t, fc="#E4E4E4", ec="#777777", ls="--",
            fs=5.8)
        arrow(ax, (0.145, y), (0.165, y))
        arrow(ax, (0.24, y), (0.262, 0.59 + (y - 0.59) * 0.35))
    box(ax, 0.262, 0.535, 0.062, 0.11, "fusion\nhead", fc=C["indiv"], ec=C["indiv"],
        color="white", weight="bold", fs=6.5)
    # privatization: one clip per patient, over the sum of its k record gradients
    arrow(ax, (0.324, 0.59), (0.342, 0.64))
    box(ax, 0.342, 0.60, 0.13, 0.255, fc="#FBE3D6", ec=C["indiv"])
    ic.shield(0.357, 0.825, 0.15)
    ax.text(0.412, 0.825, "per patient $p$", fontsize=6, ha="center", va="center",
            weight="bold", color=C["indiv"])
    ax.text(0.407, 0.705, "$g_p=\\Sigma_{w\\in W_p}\\nabla\\ell_w$ (all $k$)\n"
            "$\\downarrow$ one clip to $C$\n$\\downarrow$ sum sampled $p$,\n"
            "$+\\mathcal{N}(0,\\sigma_k^2C^2)$", fontsize=5.8, ha="center", va="center",
            linespacing=1.15)
    # compression is client-side post-processing of the privatized update
    arrow(ax, (0.407, 0.60), (0.407, 0.578))
    box(ax, 0.342, 0.445, 0.13, 0.133, fc="#F4F4F4", ec="#777777")
    ax.text(0.407, 0.5115, "post-processing:\n"
            f"top-{SPARSITY:.0%} + 8-bit;\nresidual $e_k$ kept locally",
            fontsize=5.6, ha="center", va="center", linespacing=1.15)
    ax.text(0.25, 0.41, "only the privatized, compressed head update leaves the hospital",
            fontsize=5.6, ha="center", color=C["indiv"], style="italic")

    # ── other clients ───────────────────────────────────────────────────
    rows = (0.29, 0.165)
    for i, y in enumerate(rows):
        for j in range(3):
            ic.hospital(0.04 + 0.042 * j, y, 0.24)
        ax.text(0.162, y, "$\\cdots$", fontsize=8, va="center")
        ax.text(0.19, y, f"other clients of edge {i + 1}", fontsize=6.2, va="center")

    # ── edges ───────────────────────────────────────────────────────────
    ex, edge_y = 0.585, (0.70, 0.29)
    for i, y in enumerate(edge_y):
        ic.server(ex, y, 0.42)
        ax.text(ex + 0.04, y, f"edge server {i + 1}\nFedAvg", fontsize=6.3,
                va="center")
        ax.add_patch(FancyArrowPatch((ex - 0.03, y + 0.11), (ex + 0.03, y + 0.11),
                                     arrowstyle="-|>", mutation_scale=5, lw=0.6,
                                     color="#555555", connectionstyle="arc3,rad=-0.9",
                                     zorder=4))
        ax.text(ex + 0.04, y + 0.135, f"$\\tau_e={TAU_E}$ edge rounds", fontsize=5.8,
                va="center")
    # uplinks (thin: once per edge round)
    arrow(ax, (0.472, 0.51), (ex - 0.035, edge_y[0] - 0.02), lw=0.6)
    xr = 0.535
    ax.plot([0.32, xr], [rows[0], rows[0]], color=INK, lw=0.6, zorder=4)
    arrow(ax, (xr, rows[0]), (xr, edge_y[0] - 0.06), lw=0.6)
    arrow(ax, (xr, edge_y[0] - 0.06), (ex - 0.035, edge_y[0] - 0.04), lw=0.6)
    arrow(ax, (0.335, rows[1]), (ex - 0.035, edge_y[1] - 0.03), lw=0.6)
    ax.text(0.645, 0.505, "WLAN uplink:\ncompressed private update",
            fontsize=5.6, ha="center", va="center")

    # ── cloud ───────────────────────────────────────────────────────────
    cx, cy = 0.875, 0.52
    ic.cloud(cx, cy, 0.95)
    ax.text(cx, cy - 0.01, "cloud\nglobal FedAvg", fontsize=6.5, ha="center",
            va="center", zorder=5)
    for y in edge_y:
        arrow(ax, (ex + 0.12, y), (cx - 0.075, cy + (y - cy) * 0.25), lw=1.5)
    ax.text(cx, 0.80, "backhaul, once per\ncloud round", fontsize=5.8, ha="center",
            va="center")
    ax.text(cx, 0.24, "broadcast $\\theta^{(r)}$\nto every client", fontsize=5.8,
            ha="center", va="center", color="#555555", style="italic")

    # ── ledger ──────────────────────────────────────────────────────────
    ax.add_patch(Rectangle((0.015, 0.008), 0.97, 0.08, fc="#F4F4F4", ec="#999999",
                           lw=0.5, zorder=1))
    ic.shield(0.032, 0.048, 0.20)
    ax.text(0.05, 0.048, "Privacy ledger ($\\delta=10^{-5}$):", fontsize=6.8,
            va="center", weight="bold")
    ax.text(0.25, 0.048, f"$\\varepsilon={LEDGER['epsilon_training']:.3f}\\ \\leq 1$ "
            "per client, all tiers included; one client per person; "
            "validation cohort outside", fontsize=7, va="center", color=C["indiv"])
    save(fig, "fig01_overview_core")


if __name__ == "__main__":
    main()
