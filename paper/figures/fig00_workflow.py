"""fig00_workflow.py — study workflow as a data-flow map.

The individual-level split is a gate; three streams leave it and end where
they are used: the public pool feeds the encoders, the training clients feed
the private training loop (one cloud round drawn as a ring), and the held-out
validation and test cohorts pass beneath the ring, bypassing training, to model
selection and evaluation.

Drawn as a vector illustration: shaded 2.5-D objects from _illus.py (the same
oblique style as Fig. 1), hairline cards, curved streams. Theme as Fig. 1: slate ink for structure, vermilion
only for the privacy mechanism, corpus colours only where a corpus is named.

Every number on the drawing is read from a file: client counts from each
corpus' partition_meta.json, tau_e and the sparsification ratio from
config/hfl_config.json.

    python fig00_workflow.py        -> fig00_workflow.{pdf,png}
"""
import json
import numpy as np
from matplotlib.path import Path
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, PathPatch, Circle, Ellipse
from _figstyle import plt, RES, DOUBLE, C, CORPUS, save
import _illus as I

SIM = RES.parent
CFG = json.load(open(SIM / "config" / "hfl_config.json"))
TAU_E = CFG["federated_learning"]["tau_e"]
SPARSITY = CFG["model"]["sparsification_ratio"]
DS = ("vitaldb", "wear", "eicu")
META = {d: json.load(open(SIM / "data" / "processed" / "partitions" / d /
                          "partition_meta.json")) for d in DS}
LABEL = dict(vitaldb="VitalDB", wear="WEAR", eicu="eICU")

# ── palette ────────────────────────────────────────────────────────────
INK, SLATE, HAIR = "#1E293B", "#64748B", "#CBD5E1"
TINT, SHADOW = "#EEF2F7", "#E6EAF0"
PRIV, PRIV_TINT, PRIV_DEEP = C["indiv"], "#FCE9DD", "#A84A00"
HELD = "#334155"
W, H = DOUBLE, 2.78


def card(ax, x, y, w, h, fc="white", ec=HAIR, lw=0.55, r=0.045, shadow=True, zo=2):
    if shadow:
        ax.add_patch(FancyBboxPatch((x + 0.014, y - 0.016), w, h, fc=SHADOW, ec="none",
                                    boxstyle=f"round,pad=0,rounding_size={r}",
                                    zorder=zo - 0.2))
    ax.add_patch(FancyBboxPatch((x, y), w, h, fc=fc, ec=ec, lw=lw, zorder=zo,
                                boxstyle=f"round,pad=0,rounding_size={r}"))


def pic(ax, name, x, y, s, zo=4, **kw):
    """Place one illustrated object from _illus.py."""
    getattr(I, name)(ax, x, y, s, zo=zo + 1, **kw)


def txt(ax, x, y, s, fs=7, **kw):
    kw.setdefault("ha", "left"); kw.setdefault("va", "center")
    kw.setdefault("color", INK); kw.setdefault("linespacing", 1.18)
    ax.text(x, y, s, fontsize=fs, zorder=kw.pop("zorder", 7), **kw)


def curve(ax, p0, p1, color, lw=1.1, ls="-", head=True, bend=0.5, zo=3):
    """Horizontal-tangent cubic from p0 to p1 (an S-curve), arrowhead at p1."""
    (x0, y0), (x1, y1) = p0, p1
    dx = (x1 - x0) * bend
    path = Path([(x0, y0), (x0 + dx, y0), (x1 - dx, y1), (x1, y1)],
                [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
    ax.add_patch(PathPatch(path, fill=False, ec=color, lw=lw, ls=ls, zorder=zo,
                           capstyle="round"))
    if head:
        ax.add_patch(FancyArrowPatch((x1 - 0.06, y1), (x1, y1), arrowstyle="-|>",
                                     mutation_scale=6.5, lw=lw, color=color,
                                     shrinkA=0, shrinkB=0, zorder=zo))


def arrow(ax, p, q, color=INK, lw=0.8, ms=6, ls="-", zo=4, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=ms, lw=lw,
                                 color=color, ls=ls, shrinkA=0, shrinkB=0, zorder=zo,
                                 connectionstyle=f"arc3,rad={rad}"))


def chip(ax, x, y, s, color):
    """Stream label: a small pill outlined in the stream's colour."""
    w = 0.075 * len(max(s.split("\n"), key=len)) * 0.62 + 0.14
    h = 0.15 if "\n" not in s else 0.26
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, fc="white", ec=color,
                                lw=0.7, boxstyle=f"round,pad=0,rounding_size={h / 2}",
                                zorder=5))
    txt(ax, x, y, s, color=color, ha="center", zorder=6)


def header(ax, x0, x1, s):
    txt(ax, x0, H - 0.11, s.upper(), fs=6.6, color=SLATE, weight="bold")
    ax.plot([x0, x1], [H - 0.20, H - 0.20], color=HAIR, lw=0.6, zorder=1)


def main():
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    header(ax, 0.06, 1.50, "Data")
    header(ax, 1.62, 5.00, "Private hierarchical training")
    header(ax, 5.14, 7.10, "Evaluation")

    # ── corpora ─────────────────────────────────────────────────────────
    for i, d in enumerate(("vitaldb", "wear", "eicu")):
        y = 1.86 - i * 0.62
        col, mk = CORPUS[d]
        card(ax, 0.06, y, 1.02, 0.46)
        pic(ax, "database", 0.27, y + 0.23, 0.42, color=col)
        ax.plot(0.49, y + 0.30, marker=mk, ms=3.4, color=col, ls="none", zorder=7)
        txt(ax, 0.56, y + 0.30, LABEL[d], fs=7.5, weight="bold")
        txt(ax, 0.49, y + 0.14, f"{META[d]['n_devices']} clients", color=SLATE)
        arrow(ax, (1.08, y + 0.23), (1.20, y + 0.23), color=SLATE, lw=0.7, ms=5)

    # ── the split gate ──────────────────────────────────────────────────
    gx, gw, gy0, gy1 = 1.20, 0.17, 0.10, 2.40
    ax.add_patch(FancyBboxPatch((gx, gy0), gw, gy1 - gy0, fc=INK, ec="none",
                                boxstyle="round,pad=0,rounding_size=0.085", zorder=3))
    txt(ax, gx + gw / 2, (gy0 + gy1) / 2 - 0.12, "split by individual  ·  "
        "no person spans two splits", color="white", ha="center", rotation=90)
    gr = gx + gw

    # ── encoder configuration (fed by the public pool) ──────────────────
    ex, ey, ew, eh = 2.06, 1.97, 3.00, 0.52
    card(ax, ex, ey, ew, eh)
    txt(ax, ex + 0.10, ey + eh - 0.12, "Frozen encoders, configured by corpus",
        weight="bold")
    rows = (("eicu", "disjoint encoders, pool-fitted constants", "end to end"),
            ("vitaldb", "oracle encoders (disjoint in F2)", "patient-level head"),
            ("wear", "oracle encoders, one person per client", "record-level head"))
    for i, (d, enc, head) in enumerate(rows):
        y = ey + eh - 0.29 - i * 0.115
        ax.plot(ex + 0.10, y, marker=CORPUS[d][1], ms=3.2, color=CORPUS[d][0],
                ls="none", zorder=7)
        txt(ax, ex + 0.17, y, LABEL[d], weight="bold")
        txt(ax, ex + 0.58, y, enc, color=INK)
        txt(ax, ex + ew - 0.07, y, head, ha="right", color=SLATE, style="italic")

    # ── one cloud round as a 2x2 loop: client k -> compress -> edge -> cloud
    def node(x, y, w, h, icon, title, sub, priv=False):
        card(ax, x, y, w, h, fc=PRIV if priv else "white", ec=PRIV if priv else HAIR,
             zo=3)
        pic(ax, icon, x + w - 0.21, y + h - 0.17, 0.27,
            **({"highlight": True} if icon == "hospital" else {}))
        txt(ax, x + 0.10, y + h - 0.15, title, weight="bold",
            color="white" if priv else INK)
        txt(ax, x + 0.10, y + h - 0.37, sub, color="#FFE9DA" if priv else SLATE,
            va="top", linespacing=1.12)
        return dict(l=(x, y + h / 2), r=(x + w, y + h / 2), t=(x + w / 2, y + h),
                    b=(x + w / 2, y))

    lx, rxx, nw = 2.10, 3.62, 1.36
    yt, ht, yb, hb = 1.08, 0.76, 0.30, 0.60
    ck = node(lx, yt, nw, ht, "hospital", "client $k$",
              "sample individuals at rate $q_k$;\nsum, clip to $C$;\n"
              "add $\\mathcal{N}(0,\\sigma_k^2C^2)$", priv=True)
    cp = node(lx, yb, nw, hb, "parcel", "compress",
              f"top-{SPARSITY:.0%} + 8-bit,\nerror feedback")
    ed = node(rxx, yb, nw, hb, "rack", "edge FedAvg",
              f"$\\tau_e = {TAU_E}$ rounds")
    cl = node(rxx, yt, nw, ht, "cloud", "cloud FedAvg", "global model,\nbroadcast")
    arrow(ax, ck["b"], cp["t"], color=INK, lw=0.9)
    arrow(ax, cp["r"], ed["l"], color=INK, lw=0.9)
    arrow(ax, ed["t"], cl["b"], color=INK, lw=0.9)
    arrow(ax, cl["l"], ck["r"], color=PRIV, lw=0.9)
    txt(ax, (lx + nw + rxx) / 2, (yb + hb + yt) / 2, "one cloud round, until the last",
        color=SLATE,
        style="italic", ha="center")

    # ── streams ─────────────────────────────────────────────────────────
    y_pool, y_held = 2.20, 0.22
    curve(ax, (gr, y_pool), (ex, y_pool), SLATE)
    chip(ax, 1.74, y_pool, "public pool\n(disjoint)", SLATE)
    curve(ax, (gr, 1.43), ck["l"], PRIV, lw=1.3)
    chip(ax, 1.74, 1.43, "training\nclients", PRIV)
    ax.plot([gr, 5.16], [y_held, y_held], color=HELD, lw=1.1, ls=(0, (4, 2)), zorder=3)
    arrow(ax, (5.08, y_held), (5.16, y_held), color=HELD, lw=1.1, ms=6.5)
    chip(ax, 1.74, y_held, "validation\n+ test", HELD)
    pic(ax, "padlock", 2.24, y_held - 0.10, 0.17)
    txt(ax, 2.36, y_held - 0.10, "held out: never enters training", color=HELD,
        style="italic", va="center")
    # frozen encoders configure the head of client k
    xa = lx + 0.62
    arrow(ax, (xa, ey), (xa, ck["t"][1]), color=SLATE, lw=0.7, ms=5)

    # ── evaluation: select on validation, then four analyses ────────────
    gx0, gw_ = 5.16, 1.94
    card(ax, gx0, 0.10, gw_, 2.38, fc="#F8FAFC", ec=HAIR, shadow=False, zo=1.5)
    sel_y = 1.98
    card(ax, gx0 + 0.08, sel_y, gw_ - 0.16, 0.42)
    pic(ax, "funnel", gx0 + 0.30, sel_y + 0.21, 0.36)
    txt(ax, gx0 + 0.52, sel_y + 0.27, "Select model", weight="bold")
    txt(ax, gx0 + 0.52, sel_y + 0.12, "on the validation cohort", color=SLATE)
    # global model from the cloud node into selection
    gy = sel_y + 0.21
    xm = cl["r"][0] + 0.07
    ax.plot([cl["r"][0], xm], [cl["r"][1]] * 2, color=INK, lw=0.9, zorder=3)
    curve(ax, (xm, cl["r"][1]), (gx0 + 0.08, gy), INK, lw=0.9, bend=0.0)
    tiles = (("bars", "Utility cost", "DP vs non-DP,\npaired seeds, 95% CI"),
             ("records", "Privacy-unit test", "cost vs records\nper individual $k$"),
             ("rack", "System cost", "NS-3 packets,\nCloudSim energy"),
             ("magnifier", "Privacy audit", "loss + LiRA,\npositive control"))
    tw, th = 0.89, 0.82
    for i, (icn, t, s_) in enumerate(tiles):
        tx = gx0 + 0.06 + (i % 2) * (tw + 0.04)
        ty = 1.04 - (i // 2) * (th + 0.08)
        card(ax, tx, ty, tw, th)
        pic(ax, icn, tx + 0.22, ty + th - 0.19, 0.28)
        txt(ax, tx + 0.07, ty + th - 0.41, t, weight="bold")
        txt(ax, tx + 0.07, ty + th - 0.50, s_, color=SLATE, va="top", linespacing=1.12)
    arrow(ax, (gx0 + gw_ / 2, sel_y), (gx0 + gw_ / 2, 1.04 + th), color=INK, lw=0.8)

    save(fig, "fig00_workflow")


if __name__ == "__main__":
    main()
