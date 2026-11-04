"""fig01_overview.py — Fig. 1: overview of PP-HFM.

Left: the three tiers as a 2.5-D (dimetric) scene — hospitals on the ground
plane, one edge server floating above each group of clients, the cloud above
both — so the hierarchy reads bottom-up. Right: a flat 2-D zoom into one
client, showing what happens inside the privacy boundary. Bottom: the privacy
ledger. Theme: neutral greys for structure, vermilion only for privacy.

Every figure on the drawing is read from a file: the ledger from
results/phase5/privacy_total_vitaldb.json (the headline run), tau_e and the
sparsification ratio from config/hfl_config.json.

    python fig01_overview.py [--core]   -> fig01_overview_core.{pdf,png}
(--core is accepted for the build scripts.)"""
import json
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon, Circle
from _figstyle import plt, RES, DOUBLE, C, save
import _illus as I

SIM = RES.parent
LEDGER = json.load(open(RES / "phase5" / "privacy_total_vitaldb.json"))
CFG = json.load(open(SIM / "config" / "hfl_config.json"))
TAU_E = CFG["federated_learning"]["tau_e"]
SPARSITY = CFG["model"]["sparsification_ratio"]

# ── theme ──────────────────────────────────────────────────────────────
INK, MUTED, LINE = "#1F2937", "#6B7280", "#9CA3AF"
CARD, CARD_EDGE = "#F7F7F8", "#D1D5DB"
PRIV, PRIV_LIGHT = C["indiv"], "#FBE6D9"            # vermilion = privacy only
FACE = dict(slab=("#F3F4F6", "#E2E4E8", "#CDD1D7"),   # top, left, right
            bldg=("#FFFFFF", "#E9ECEF", "#D3D8DE"),
            rack=("#8EA3B8", "#5B7C99", "#46637E"))
W, H = DOUBLE, 3.0

# ── oblique (cabinet) projection, inches: x right, z up, depth y recedes ─
U, KX, KY = 0.30, 0.42, 0.30
OX, OY = 1.30, 0.80


def P(x, y, z=0.0):
    return (OX + U * (x + KX * y), OY + U * (KY * y + z))


def block(ax, x, y, z, dx, dy, dz, faces, ec=LINE, lw=0.45, zo=3, edge_top=None):
    """Visible faces: front (y = y0), right (x = x0 + dx) and top."""
    top, front, right = faces
    q = lambda pts: [P(*p) for p in pts]
    ax.add_patch(Polygon(q([(x + dx, y, z), (x + dx, y + dy, z), (x + dx, y + dy, z + dz),
                            (x + dx, y, z + dz)]), fc=right, ec=ec, lw=lw, zorder=zo,
                         joinstyle="round"))
    ax.add_patch(Polygon(q([(x, y, z), (x + dx, y, z), (x + dx, y, z + dz), (x, y, z + dz)]),
                         fc=front, ec=ec, lw=lw, zorder=zo, joinstyle="round"))
    ax.add_patch(Polygon(q([(x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz),
                            (x, y + dy, z + dz)]), fc=top, ec=edge_top or ec,
                         lw=lw if edge_top is None else 1.1, zorder=zo + 0.01,
                         joinstyle="round"))


def face_quad(ax, pts, fc, zo):
    ax.add_patch(Polygon([P(*p) for p in pts], fc=fc, ec="none", zorder=zo))


HD = 0.80                                           # hospital footprint and height


def hospital(ax, x, y, highlight=False, zo=3):
    block(ax, x, y, 0, HD, HD, 1.0, FACE["bldg"], zo=zo,
          ec=PRIV if highlight else LINE, lw=0.9 if highlight else 0.45)
    for i in range(3):                                # windows on the front face
        for j in range(2):
            u0, w0 = 0.09 + i * 0.235, 0.16 + j * 0.30
            face_quad(ax, [(x + u0, y, w0), (x + u0 + 0.14, y, w0),
                           (x + u0 + 0.14, y, w0 + 0.17), (x + u0, y, w0 + 0.17)],
                      "#A9C9E6", zo + 0.05)
    face_quad(ax, [(x + 0.31, y, 0), (x + 0.49, y, 0), (x + 0.49, y, 0.12),
                   (x + 0.31, y, 0.12)], "#7A8C9C", zo + 0.05)        # door
    cx, cz, a, b = x + HD / 2, 0.82, 0.13, 0.045        # red cross on the facade
    for (u, v) in ((a, b), (b, a)):
        face_quad(ax, [(cx - u, y, cz - v), (cx + u, y, cz - v),
                       (cx + u, y, cz + v), (cx - u, y, cz + v)], "#D64545", zo + 0.06)


def rack(ax, x, y, z):
    block(ax, x, y, z, 0.62, 0.55, 1.05, FACE["rack"], ec="#3B5266", zo=6)
    for k in range(3):
        h = z + 0.20 + k * 0.32
        ax.plot(*zip(P(x + 0.07, y, h), P(x + 0.36, y, h)), color="#DDE6EE", lw=0.7,
                zorder=6.1)
        for d, c in ((0.45, "#7CE07C"), (0.54, "#F5C542")):
            px, py = P(x + d, y, h)
            ax.add_patch(Circle((px, py), 0.013, fc=c, ec="none", zorder=6.2))


def arrow(ax, p, q, color=INK, lw=0.8, ls="-", ms=7, rad=0.0, zo=8, style="-|>"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, lw=lw,
                                 color=color, ls=ls, shrinkA=1.5, shrinkB=1.5, zorder=zo,
                                 connectionstyle=f"arc3,rad={rad}"))


def rbox(ax, x, y, w, h, fc, ec, lw=0.6, ls="-", r=0.05, zo=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=zo))


def badge(ax, x, y, n):
    ax.add_patch(Circle((x, y), 0.075, fc=INK, ec="none", zorder=9))
    ax.text(x, y - 0.004, str(n), color="white", fontsize=7, weight="bold",
            ha="center", va="center", zorder=9.1)


def main():
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    # ── scene: ground plane with two groups of three hospitals ──────────
    gx = ((0.0, 1.05, 2.10), (5.0, 6.05, 7.10))
    block(ax, -0.35, -0.30, -0.12, 8.6, 1.45, 0.12, FACE["slab"], zo=1)
    hk = gx[1][-1]                                   # client k: nearest the zoom card
    for g in gx:
        for xh in g:                                 # left to right: painter order
            hospital(ax, xh, 0.15, highlight=(xh == hk))

    # edge platforms + racks, and the cloud
    ez, edges = 3.05, []
    for g in gx:
        xc = (g[0] + g[-1] + HD) / 2
        block(ax, xc - 1.25, -0.05, ez - 0.12, 2.5, 1.0, 0.12, FACE["slab"], zo=5)
        rack(ax, xc - 0.31, 0.20, ez)
        edges.append(xc)
    xm = (edges[0] + edges[1]) / 2
    cxy = P(xm, 0.4, 6.0)
    I.cloud(ax, cxy[0], cxy[1] - 0.03, 0.86, zo=4)
    ax.text(cxy[0], cxy[1] - 0.03, "global FedAvg", fontsize=7, ha="center",
            va="center", zorder=5, color=INK)

    # uplinks: privatized, compressed head updates (vermilion)
    for g, xc in zip(gx, edges):
        for xh in g:
            arrow(ax, P(xh + HD / 2, 0.55, 1.0), P(xc + 0.0, 0.40, ez - 0.12),
                  color=PRIV, lw=0.75, ms=5, zo=4.5)
    # backhaul: edge -> cloud, once per cloud round (thick ink)
    for xc in edges:
        side = -1 if xc < xm else 1
        arrow(ax, P(xc + 0.0, 0.47, ez + 1.08), (cxy[0] + side * 0.36, cxy[1] - 0.10),
              lw=1.5, ms=8)
    # tau_e loop to the right of each rack
    for xc in edges:
        px, py = P(xc + 0.62, 0.2, ez + 0.55)
        ax.add_patch(FancyArrowPatch((px, py + 0.11), (px, py - 0.11),
                                     arrowstyle="-|>", mutation_scale=5, lw=0.7,
                                     color=MUTED, connectionstyle="arc3,rad=-1.3",
                                     zorder=7))
        ax.text(px + 0.12, py, f"$\\times\\tau_e$", fontsize=7, color=MUTED,
                va="center", ha="left")
    # broadcast back down the middle (dashed)
    arrow(ax, (cxy[0], cxy[1] - 0.24), P(xm - 0.25, 0.4, 0.15), color=MUTED, lw=0.75,
          ls=(0, (3, 2)), ms=6, zo=4)

    # captions on the ground and a key for the three link types
    for g, lab in zip(gx, ("clients of edge 1", "clients of edge 2")):
        x0, y0 = P((g[0] + g[-1] + HD) / 2, -0.30, -0.12)
        ax.text(x0, y0 - 0.05, lab, fontsize=7, ha="center", va="top", color=MUTED)
    kx, ky = P(hk + HD, HD + 0.15, 1.0)
    ax.text(kx + 0.03, ky + 0.01, "client $k$", fontsize=7.5, ha="left", va="bottom",
            color=PRIV, weight="bold", zorder=9)
    ky0 = 0.36
    keys = ((PRIV, "-", 0.9, "privatized update (WLAN uplink)"),
            (INK, "-", 1.5, "backhaul"),
            (MUTED, (0, (3, 2)), 0.8, "broadcast $\\theta^{(r)}$ to every client"))
    kxs = (0.25, 2.05, 2.95)
    for (col, ls, lw, lab), x0 in zip(keys, kxs):
        arrow(ax, (x0, ky0), (x0 + 0.22, ky0), color=col, ls=ls, lw=lw, ms=5, zo=9)
        ax.text(x0 + 0.27, ky0, lab, fontsize=7, va="center", color=INK)

    # ── tier rail on the left ───────────────────────────────────────────
    rail = ((cxy[1] + 0.05, 3, "Cloud", "backhaul once per\ncloud round"),
            (P(0, 0.5, ez + 0.55)[1], 2, "Edge", f"FedAvg over\n$\\tau_e={TAU_E}$ edge rounds"),
            (P(0, 0.5, 0.55)[1], 1, "Clients", "hospitals; local\npatient-level DP"))
    for y, n, name, sub in rail:
        badge(ax, 0.12, y + 0.08, n)
        ax.text(0.25, y + 0.08, name, fontsize=8, weight="bold", va="center", color=INK)
        ax.text(0.04, y - 0.06, sub, fontsize=7, va="top", color=MUTED, linespacing=1.1)

    # ── zoom: inside client k ───────────────────────────────────────────
    zx, zy, zw, zh = 4.42, 0.55, 2.68, 2.38
    hx0, hy0 = P(hk + HD, 0.15, 1.0)
    hx1, hy1 = P(hk + HD, 0.15, 0.0)
    for (px, py), cy_ in (((hx0, hy0), zy + zh - 0.06), ((hx1, hy1), zy + 0.06)):
        ax.plot([px, zx], [py, cy_], color=PRIV, lw=0.5, ls=(0, (2, 2)), zorder=1.5)
    rbox(ax, zx, zy, zw, zh, "white", PRIV, lw=1.0, ls=(0, (4, 2)), r=0.08, zo=2)
    I.hospital(ax, zx + 0.18, zy + zh - 0.18, 0.22, highlight=True)
    ax.text(zx + 0.40, zy + zh - 0.17, "Inside client $k$", fontsize=8, weight="bold",
            va="center", color=INK)
    ax.text(zx + zw - 0.08, zy + zh - 0.17, "privacy boundary", fontsize=7, ha="right",
            va="center", color=PRIV, style="italic")

    # row A: inputs -> frozen encoders -> fusion head
    yA, yB = zy + 1.82, zy + 1.30
    I.bed_patient(ax, zx + 0.27, yA + 0.12, 0.34)
    I.monitor(ax, zx + 0.60, yA + 0.15, 0.24)
    ax.text(zx + 0.36, yA - 0.19, "patient $p$: windows\n$W_p=\\{w_1,\\ldots,w_k\\}$",
            fontsize=7, ha="center", va="center", linespacing=1.15)
    I.database(ax, zx + 0.17, yB, 0.26)
    ax.text(zx + 0.30, yB, "admission\nrecord of $p$", fontsize=7, va="center",
            linespacing=1.1)
    ex0 = zx + 1.02
    for y, t in ((yA, "encoder A"), (yB, "encoder B")):
        rbox(ax, ex0, y - 0.16, 0.62, 0.32, CARD, LINE, ls=(0, (2.5, 1.5)), r=0.04, zo=3)
        ax.text(ex0 + 0.31, y, f"{t}\nfrozen", fontsize=7, ha="center", va="center",
                color=INK, linespacing=1.1, zorder=3.1)
        arrow(ax, (ex0 - 0.17, y), (ex0, y), lw=0.6, ms=5)
    fhx, fhy = zx + 1.86, (yA + yB) / 2
    rbox(ax, fhx, fhy - 0.2, 0.62, 0.40, PRIV, PRIV, r=0.05, zo=3)
    ax.text(fhx + 0.31, fhy, "fusion\nhead", fontsize=7.5, ha="center", va="center",
            color="white", weight="bold", linespacing=1.1, zorder=3.1)
    for y in (yA, yB):
        arrow(ax, (ex0 + 0.62, y), (fhx, fhy + (y - fhy) * 0.35), lw=0.6, ms=5)

    # row B: per-patient privatization -> post-processing -> out
    pbx, pby, pbw, pbh = zx + 1.30, zy + 0.10, 1.32, 0.86
    rbox(ax, pbx, pby, pbw, pbh, PRIV_LIGHT, PRIV, lw=0.7, r=0.05, zo=3)
    I.shield(ax, pbx + 0.13, pby + pbh - 0.13, 0.17)
    ax.text(pbx + 0.25, pby + pbh - 0.13, "per patient $p$", fontsize=7.5,
            weight="bold", color=PRIV, va="center", zorder=3.1)
    ax.text(pbx + pbw / 2, pby + 0.36,
            "$g_p=\\Sigma_{w\\in W_p}\\nabla\\ell_w$ (all $k$)\n"
            "$\\downarrow$ one clip to $C$\n$\\downarrow$ sum sampled $p$, "
            "$+\\mathcal{N}(0,\\sigma_k^2C^2)$", fontsize=7, ha="center", va="center",
            linespacing=1.25, zorder=3.1)
    arrow(ax, (fhx + 0.31, fhy - 0.2), (fhx + 0.31, pby + pbh), lw=0.7, ms=5)
    ppx, ppw = zx + 0.12, 1.05
    rbox(ax, ppx, pby + 0.08, ppw, 0.70, CARD, LINE, r=0.05, zo=3)
    ax.text(ppx + ppw / 2, pby + 0.43, "post-processing:\n"
            f"top-{SPARSITY:.0%} + 8-bit;\nresidual $e_k$ kept\nlocally",
            fontsize=7, ha="center", va="center", linespacing=1.15, zorder=3.1)
    arrow(ax, (pbx, pby + 0.43), (ppx + ppw, pby + 0.43), lw=0.7, ms=5)
    # the only thing that leaves: out through the boundary, toward the edge
    ox_, oy_ = ppx, pby + 0.43
    arrow(ax, (ox_, oy_), (zx - 0.12, oy_), color=PRIV, lw=1.1, ms=7)
    ax.text(zx + zw / 2, zy - 0.12, "only the privatized, compressed head update "
            "leaves the hospital", fontsize=7, color=PRIV, style="italic",
            va="center", ha="center")

    # ── ledger ──────────────────────────────────────────────────────────
    rbox(ax, 0.04, 0.03, W - 0.08, 0.20, CARD, CARD_EDGE, lw=0.5, r=0.04, zo=1)
    I.shield(ax, 0.17, 0.13, 0.15)
    ax.text(0.29, 0.13, "Privacy ledger ($\\delta=10^{-5}$):", fontsize=7, va="center",
            weight="bold", color=INK)
    ax.text(1.80, 0.13, f"$\\varepsilon={LEDGER['epsilon_training']:.3f}\\ \\leq 1$ "
            "per client, all tiers included; one client per person; "
            "validation cohort outside", fontsize=7, va="center", color=PRIV)
    save(fig, "fig01_overview_core")


if __name__ == "__main__":
    main()
