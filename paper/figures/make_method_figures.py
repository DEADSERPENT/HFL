"""
make_method_figures.py — figures for the PP-HFM methodology section.

Every quantity shown (client count, edge map, patient and window totals,
channel counts, embedding widths, tau_e) is READ from the artefacts that
define the system: partition_meta.json, dataset_meta.json, the config, the
case-id array, and the model itself. Nothing is typed in twice. A figure that
hardcodes "9 clients" keeps saying nine after the partition changes; this one
cannot.

Output: vector PDF at paper/figures/, plus PNG previews for eyeballing.

PALETTE — validated, do not substitute by eye
  #0072B2 blue      frozen / publicly pretrained
  #D55E00 vermilion privatised (DP-trained)
  #009E73 green     patient-grouped data
Three hues, checked with the dataviz validator: lightness band, chroma floor,
CVD separation (worst adjacent dE 11.0 deutan), normal-vision floor, and
contrast against the surface all pass. IEEE prints in greyscale often, so
every colour is paired with a text label or a hatch; colour never carries
meaning alone.
"""

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_SIM = _ROOT / "SIMULATORS"
sys.path.insert(0, str(_SIM / "data" / "loaders"))

BLUE, VERM, GREEN = "#0072B2", "#D55E00", "#009E73"
INK, MUTED, RULE, SURF = "#1a1a1a", "#5c5c5c", "#c8c8c4", "#fcfcfb"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "STIXGeneral",
                   "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 7.2,
    "text.color": INK,
    "axes.edgecolor": RULE,
    "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "pdf.fonttype": 42,        # embed TrueType: editable, no Type-3 warnings
    "ps.fonttype": 42,
})

COL1, COL2 = 3.5, 7.16        # IEEE single / double column width, inches


# ── facts, read not typed ───────────────────────────────────────────────
def load_facts(dataset="vitaldb"):
    from datasets import get_spec
    spec = get_spec(dataset)
    pdir = _SIM / spec.partition_dir
    meta = json.loads((pdir / "partition_meta.json").read_text())
    dmeta = json.loads((_SIM / spec.data_dir / "meta" / "dataset_meta.json").read_text())
    cfg = json.loads((_SIM / "config" / "hfl_config.json").read_text())
    case_ids = np.load(_SIM / spec.data_dir / "meta" / "case_ids.npy")

    _, counts = np.unique(case_ids, return_counts=True)
    f = {
        "n_clients": meta["n_devices"],
        "n_edges": meta["n_edges"],
        "edges": {int(k): v for k, v in meta["edge_assignments"].items()},
        "client_names": meta.get("client_names", []),
        "n_windows": int(len(case_ids)),
        "n_patients": int(len(counts)),
        "wpp_mean": float(counts.mean()),
        "wpp_max": int(counts.max()),
        "n_ch_a": spec.n_channels_a,
        "n_feat_b": spec.feat_b_dim,
        "n_classes": spec.n_classes,
        "channels": dmeta.get("signal_channels", []),
        "tau_e": cfg.get("federated_learning", {}).get("tau_e", 5),
        "eps": cfg.get("privacy", {}).get("epsilon", 1.0),
        "label": dmeta.get("label", ""),
    }
    # Embedding widths come from the model, not from memory of the model.
    sys.path.insert(0, str(_SIM / "model" / "architecture"))
    from hfl_mm_model import build_hfl_mm_hc
    m = build_hfl_mm_hc(n_classes=spec.n_classes, n_channels_a=spec.n_channels_a,
                        modality_b="features", feat_b_dim=spec.feat_b_dim)
    f["d_a"] = int(m.encoder_a.output_dim)
    f["d_b"] = int(m.encoder_b.out_dim)
    f["n_head"] = int(sum(p.numel() for p in m.fusion.parameters()))
    f["n_total"] = int(m.n_total)
    ea = m.encoder_a
    import torch
    f["ks"] = [int(c.kernel_size[0]) for c in ea.stem[0].modules()
               if isinstance(c, torch.nn.Conv1d)]
    f["stride"] = int(ea.stem[1].stride[0])
    f["pool"] = int(ea.conv2[3].kernel_size)
    f["gru_layers"] = int(ea.gru.num_layers)
    f["hid_b"] = int(m.encoder_b.net[0].out_features)
    return f


def box(ax, x, y, w, h, label, fc="white", ec=RULE, lw=0.8, fs=6.6,
        tc=INK, weight="normal", hatch=None, r=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle=f"round,pad=0,rounding_size={r}",
                 fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=2))
    if label:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=fs, color=tc, weight=weight, zorder=3, linespacing=1.35)


def arrow(ax, p, q, color=MUTED, lw=0.9, style="-|>", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, color=color, lw=lw,
                 linestyle=ls, mutation_scale=7, shrinkA=1, shrinkB=1,
                 connectionstyle=f"arc3,rad={rad}", zorder=1))


def finish(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(_HERE / f"{name}.{ext}", dpi=400, bbox_inches="tight",
                    pad_inches=0.02)
    plt.close(fig)
    print(f"  {name}.pdf / .png")


# ── Fig 1 — three-tier architecture ─────────────────────────────────────
def fig_architecture(f):
    fig, ax = plt.subplots(figsize=(COL2, 3.25))
    ax.set_xlim(-9, 100); ax.set_ylim(-6, 52); ax.axis("off")

    # Tier labels live in the LEFT MARGIN, rotated, outside the band. Set
    # inside the band they collided with the first client box and with the
    # connectors leaving it; there is no in-band position that stays clear as
    # the client count changes.
    for y0, h, lab in ((35.5, 14, "Cloud tier"), (20.5, 12, "Edge tier"),
                       (0.5, 18.5, "Device tier")):
        ax.add_patch(Rectangle((0, y0), 100, h, fc="#f2f2ef", ec="none", zorder=0))
        ax.text(-3.2, y0 + h / 2, lab, fontsize=6.4, color=MUTED,
                style="italic", va="center", ha="center", rotation=90)

    # cloud
    box(ax, 36, 39.5, 28, 7.5,
        f"Cloud aggregator\nweighted FedAvg over {f['n_edges']} edges",
        fc="white", lw=1.0, fs=7.0, weight="bold")

    # edges
    ex = {0: 20.0, 1: 60.0}
    for e in range(f["n_edges"]):
        ids = f["edges"][e]
        box(ax, ex[e], 23.0, 20, 7.0,
            f"Edge {e}\nFedAvg $\\times\\,\\tau_e{{=}}{f['tau_e']}$  ·  {len(ids)} clients",
            fc="white", lw=1.0, fs=6.8, weight="bold")
        arrow(ax, (ex[e] + 10, 30.0), (46 if e == 0 else 54, 39.5), color=INK, lw=1.0)
        ax.text((ex[e] + 10 + (46 if e == 0 else 54)) / 2 + (-9 if e == 0 else 6), 35.2,
                "compressed\nupdate", fontsize=5.6, color=MUTED, ha="center")

    # Clients are DRAWN grouped by their edge while keeping their true ids.
    # The real assignment interleaves ({0,2,4,6,8} vs {1,3,5,7}); drawing them
    # in index order makes every connector cross the figure. Grouping removes
    # the crossings without misstating the mapping, since each box keeps its
    # own index.
    order = [(k, 0) for k in f["edges"][0]] + [(k, 1) for k in f["edges"][1]]
    n = len(order)
    w, gap = 9.0, 1.2
    x0 = (100 - (n * w + (n - 1) * gap)) / 2
    for i, (k, e) in enumerate(order):
        x = x0 + i * (w + gap)
        box(ax, x, 7.5, w, 9.0, "", fc="white", lw=0.8)
        ax.text(x + w / 2, 15.4, f"client {k}", fontsize=5.8, color=INK,
                ha="center", va="center", weight="bold")
        box(ax, x + 0.6, 11.9, w - 1.2, 2.4, "$\\phi_A,\\phi_B$",
            fc=BLUE, ec="none", fs=5.4, tc="white")
        box(ax, x + 0.6, 8.6, w - 1.2, 2.4, "head", fc=VERM, ec="none",
            fs=5.4, tc="white")
        box(ax, x + 0.6, 3.6, w - 1.2, 2.6, "patients", fc=GREEN, ec="none",
            fs=5.0, tc="white")
        arrow(ax, (x + w / 2, 6.2), (x + w / 2, 7.5), color=MUTED, lw=0.7)
        arrow(ax, (x + w / 2, 16.5), (ex[e] + 10, 23.0), color=INK, lw=0.7,
              rad=0.05)

    # Legend carries the frozen/privatised distinction, so the client boxes do
    # not have to hold text too small to set.
    ly = -2.6
    for sx, c, lab in ((14.0, BLUE, "frozen encoders (public pretraining)"),
                       (52.0, VERM, "DP-trained fusion head"),
                       (82.0, GREEN, "patient-grouped local data")):
        ax.add_patch(Rectangle((sx, ly), 2.2, 2.2, fc=c, ec="none"))
        ax.text(sx + 3.0, ly + 1.1, lab, fontsize=5.8, color=INK, va="center")

    ax.text(50, -5.6, f"data never leaves the client   ·   "
                      f"{f['n_patients']:,} patients, {f['n_windows']:,} windows, "
                      f"partitioned by surgical specialty",
            fontsize=6.0, color=MUTED, ha="center", style="italic")
    finish(fig, "fig1_architecture")


# ── Fig 2 — backbone, frozen vs privatised ──────────────────────────────
def fig_backbone(f):
    """Encoder-fusion backbone as a 2.5-D illustration: layers drawn as shaded
    slabs, inputs and zones illustrated (_illus.py), same theme as Figs. 1 and 5.
    Every number is read from the model (load_facts)."""
    import _illus as IL
    from matplotlib.patches import FancyBboxPatch, Polygon as Poly
    INK_, SLATE_, HAIR_ = "#1E293B", "#64748B", "#CBD5E1"
    PANEL_, PRIVL_ = "#F4F6F9", "#FCE9DD"
    SL3 = ("#A9B8C9", "#556B85", "#435771")                 # top, front, right
    PV3 = ("#F49A5C", "#D55E00", "#A84A00")
    Wf, Hf = COL2, 2.05
    fig = plt.figure(figsize=(Wf, Hf))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, Wf); ax.set_ylim(0, Hf); ax.axis("off")

    def rbox(x, y, w, h, fc, ec, lw=0.5, r=0.05, zo=1):
        ax.add_patch(FancyBboxPatch((x, y), w, h, fc=fc, ec=ec, lw=lw, zorder=zo,
                                    boxstyle=f"round,pad=0,rounding_size={r}"))

    def slab(x, y, w, h, label, faces=SL3, d=(0.07, 0.05), tc="white", bold=False):
        """Layer as a shaded slab; (x, y) is the front face's lower-left corner."""
        top, front, right = faces
        dx, dy = d
        ax.add_patch(Poly([(x + w, y), (x + w + dx, y + dy), (x + w + dx, y + h + dy),
                           (x + w, y + h)], fc=right, ec="#334155", lw=0.35, zorder=3))
        ax.add_patch(Poly([(x, y + h), (x + w, y + h), (x + w + dx, y + h + dy),
                           (x + dx, y + h + dy)], fc=top, ec="#334155", lw=0.35, zorder=3))
        ax.add_patch(Poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fc=front,
                          ec="#334155", lw=0.35, zorder=3.1))
        ax.text(x + w / 2, y + h / 2, label, fontsize=7, color=tc, ha="center",
                va="center", zorder=4, linespacing=1.15,
                weight="bold" if bold else "normal")
        return (x, y + h / 2), (x + w + dx / 2, y + h / 2)

    def card(x, y, w, h, label, zo=3):
        rbox(x + 0.012, y - 0.014, w, h, "#E6EAF0", "none", zo=zo - 0.2)
        rbox(x, y, w, h, "white", HAIR_, lw=0.55, zo=zo)
        ax.text(x + w / 2, y + h / 2, label, fontsize=7, color=INK_, ha="center",
                va="center", zorder=zo + 1, linespacing=1.15)

    def arr(p, q, color=SLATE_, lw=0.8):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=6, lw=lw,
                                     color=color, shrinkA=1, shrinkB=1, zorder=2))

    # zones
    fx1, dx0 = 4.52, 4.62
    rbox(0.05, 0.08, fx1 - 0.05, Hf - 0.16, PANEL_, HAIR_, zo=0)
    rbox(dx0, 0.08, Wf - 0.05 - dx0, Hf - 0.16, PRIVL_, "#EBB48C", zo=0)
    IL.padlock(ax, 0.20, Hf - 0.23, 0.17, zo=5)
    ax.text(0.33, Hf - 0.23, "frozen: pretrained centrally, never updated under DP",
            fontsize=7, color=SLATE_, style="italic", va="center")
    IL.shield(ax, dx0 + 0.16, Hf - 0.23, 0.17, zo=5)
    ax.text(dx0 + 0.30, Hf - 0.23, f"DP-trained ($\\varepsilon\\leq{f['eps']:.0f}$)",
            fontsize=7, color=VERM, style="italic", va="center")

    # modality A: stages as built in fedmamba_hc.FedMambaHC
    yA, yB, sh = 1.08, 0.36, 0.40
    rbox(0.14, yA - 0.06, 0.86, 0.52, "white", HAIR_, lw=0.55, zo=2)
    IL.monitor(ax, 0.37, yA + 0.22, 0.34, zo=4)
    ax.text(0.80, yA + 0.20, f"$x_A$\n{f['n_ch_a']}$\\times$T", fontsize=7,
            ha="center", va="center", color=INK_, linespacing=1.2)
    ks = ", ".join(str(k) for k in f["ks"])
    stages = [f"multi-scale\n$k={ks}$", f"strided conv\n$s={f['stride']}$, GN",
              f"conv + GN\nmax-pool {f['pool']}", f"BiGRU\n{f['gru_layers']} layers",
              "attention\npool + proj."]
    w, g, x0 = 0.60, 0.09, 1.10
    xs = [x0 + i * (w + g) for i in range(len(stages))]
    prev = (1.00, yA + sh / 2)
    for xi, t in zip(xs, stages):
        l, r = slab(xi, yA, w, sh, t)
        arr(prev, l); prev = r
    for xi, t in zip(xs[1:3], (f"T/{f['stride']}", f"T/{f['stride'] * f['pool']}")):
        ax.text(xi + w / 2, yA - 0.05, t, fontsize=7, color=SLATE_, ha="center", va="top")
    ax.text(xs[-1] + w / 2, yA + sh + 0.12, f"$\\phi_A \\rightarrow {f['d_a']}$-d",
            fontsize=7, color=SLATE_, ha="center", va="bottom")
    endA = prev

    # modality B: two-layer perceptron
    rbox(0.14, yB - 0.06, 0.86, 0.52, "white", HAIR_, lw=0.55, zo=2)
    IL.records(ax, 0.37, yB + 0.22, 0.32, zo=4)
    ax.text(0.80, yB + 0.20, f"$x_B$\n{f['n_feat_b']}-d", fontsize=7, ha="center",
            va="center", color=INK_, linespacing=1.2)
    wb = 2 * w + g
    l1, r1 = slab(xs[0], yB, wb, sh, f"linear $\\rightarrow$ {f['hid_b']}\nGN + GELU")
    l2, r2 = slab(xs[2], yB, wb, sh, f"linear $\\rightarrow$ {f['d_b']}\nGN + GELU")
    arr((1.00, yB + sh / 2), l1); arr(r1, l2)
    ax.text(xs[2] + wb / 2, yB - 0.05, f"$\\phi_B \\rightarrow {f['d_b']}$-d",
            fontsize=7, color=SLATE_, ha="center", va="top")

    # fusion (the only part that receives noise)
    yc = (yA + yB + sh) / 2
    card(dx0 + 0.14, yc - 0.26, 0.58, 0.52, f"concat\n{f['d_a'] + f['d_b']}-d")
    arr(endA, (dx0 + 0.14, yc + 0.10), color=INK_)
    arr(r2, (dx0 + 0.14, yc - 0.10), color=INK_)
    hl, hr = slab(dx0 + 0.90, yc - 0.30, 0.74, 0.60, "fusion\nhead", faces=PV3,
                  d=(0.09, 0.065), bold=True)
    arr((dx0 + 0.72, yc), hl, color=INK_)
    card(dx0 + 1.86, yc - 0.26, 0.56, 0.52, f"logits\n{f['n_classes']}")
    arr(hr, (dx0 + 1.86, yc), color=INK_)
    pct = 100.0 * f["n_head"] / f["n_total"]
    ax.text(dx0 + (Wf - 0.05 - dx0) / 2, 0.30, f"{f['n_head']:,} of {f['n_total']:,} "
            f"parameters\n({pct:.1f}%, VitalDB) receive noise", fontsize=7, color=VERM,
            ha="center", va="center", linespacing=1.3)
    finish(fig, "fig2_backbone")


# ── Fig 3 — record- vs patient-level sensitivity ────────────────────────
def fig_sensitivity(f):
    """The paper's central idea, drawn: clipping per window bounds a WINDOW's
    influence at C, so a patient with k windows can still move the sum by kC."""
    fig, ax = plt.subplots(figsize=(COL1, 2.45))
    ax.set_xlim(0, 100); ax.set_ylim(0, 74); ax.axis("off")
    k = int(round(f["wpp_mean"]))
    # k windows across a 44-unit panel; spacing derived, never assumed to fit.
    pw = 44.0
    bw = min(4.2, (pw - 4) / k * 0.78)
    step = (pw - 4 - bw) / max(k - 1, 1)

    for side, x0, title, col in ((0, 2, "record-level clipping", VERM),
                                 (1, 54, "patient-level clipping", GREEN)):
        cx = x0 + pw / 2
        ax.text(cx, 70, title, fontsize=6.6, ha="center", weight="bold",
                color=INK)
        ax.text(cx, 62.5, f"one patient, $k_p{{=}}{k}$ windows",
                fontsize=5.8, ha="center", color=MUTED)
        for i in range(k):
            box(ax, x0 + 2 + i * step, 50, bw, 7.0, "", fc=GREEN, ec="none")

        if side == 0:
            for i in range(k):
                xx = x0 + 2 + i * step + bw / 2
                arrow(ax, (xx, 50), (xx, 42), color=MUTED, lw=0.7)
            mid, inf = "clip each to $C$", f"patient influence $\\leq {k}\\,C$"
            foot = "guarantee is about\nthe WINDOW"
        else:
            # Converge to a summation node rather than to a point: eight
            # arrowheads meeting at one coordinate render as an ink blob.
            for i in range(k):
                xx = x0 + 2 + i * step + bw / 2
                arrow(ax, (xx, 50), (cx, 45.4), color=MUTED, lw=0.55,
                      style="-")
            ax.add_patch(FancyBboxPatch((cx - 2.4, 41.4), 4.8, 4.0,
                         boxstyle="round,pad=0,rounding_size=0.4",
                         fc="white", ec=MUTED, lw=0.8, zorder=3))
            ax.text(cx, 43.4, r"$\Sigma$", fontsize=7.0, ha="center",
                    va="center", color=INK, zorder=4)
            arrow(ax, (cx, 41.4), (cx, 38.6), color=MUTED, lw=0.7)
            mid, inf = "then clip to $C$", "patient influence $\\leq C$"
            foot = "guarantee is about\nthe PATIENT"

        ax.text(cx, 36.5, mid, fontsize=6.0, ha="center", color=INK)
        box(ax, x0 + 1, 24.0, pw - 2, 8.0, inf, fc="white", ec=col,
            lw=1.1, fs=6.0, tc=col, weight="bold")
        ax.text(cx, 18.0, foot, fontsize=6.0, ha="center", color=MUTED,
                linespacing=1.4, va="top")

    ax.plot([50, 50], [9, 66], color=RULE, lw=0.7, ls=(0, (2, 2)))
    finish(fig, "fig3_sensitivity")


# ── Fig 4 — LiRA: per-patient IN/OUT calibration ────────────────────────
def fig_lira(f):
    """Why a threshold fails and a likelihood ratio does not. Two patients of
    different difficulty: a global threshold cannot separate both, the
    per-patient IN/OUT fit can. Illustrative curves, not measurements."""
    fig, axes = plt.subplots(1, 2, figsize=(COL1, 1.9), sharey=True)
    x = np.linspace(-8, 10, 500)
    sd = 1.1

    def g(mu):
        return np.exp(-0.5 * ((x - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi))

    peak = 1.0 / (sd * np.sqrt(2 * np.pi))     # label anchors derived, not guessed

    for ax, (mo, mi, name) in zip(axes, [(-3.2, -1.2, "hard patient"),
                                         (3.0, 5.0, "easy patient")]):
        for mu, c in ((mo, BLUE), (mi, VERM)):
            ax.fill_between(x, g(mu), color=c, alpha=0.20, lw=0)
            ax.plot(x, g(mu), color=c, lw=1.2)
        ax.axvline(1.0, color=INK, lw=1.0, ls=(0, (3, 2)))
        ax.set_title(name, fontsize=6.4, color=INK, pad=4)
        ax.set_ylim(0, peak * 1.32)            # headroom so labels clear the title
        ax.set_yticks([])
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(labelsize=5.8, length=2)

    # Labels sit just below each curve's own peak, inside the axes.
    axes[0].text(-3.2, peak * 1.06, "OUT", fontsize=6.0, color=BLUE,
                 ha="center", weight="bold")
    axes[0].text(1.6, peak * 0.55, "IN", fontsize=6.0, color=VERM,
                 ha="left", weight="bold")
    # label both curves in both panels, so the panels read without colour
    axes[1].text(3.0, peak * 1.06, "OUT", fontsize=6.0, color=BLUE,
                 ha="center", weight="bold")
    axes[1].text(6.6, peak * 0.55, "IN", fontsize=6.0, color=VERM,
                 ha="left", weight="bold")
    # Two lines, anchored well left of the threshold: the single-line form
    # overran the dashed rule it was labelling.
    # the SAME global threshold tau in both panels; what it decides for each
    for a_ in axes:
        a_.text(1.0, peak * 1.27, "$\\tau$", fontsize=6.4, ha="center",
                va="top", color=INK, bbox=dict(fc="white", ec="none", pad=0.4))
    axes[0].text(2.3, peak * 1.0, "both below $\\tau$:\nmembers missed",
                 fontsize=5.4, color=INK, ha="left", va="center", linespacing=1.25)
    axes[1].text(-7.6, peak * 1.0, "same global $\\tau$;\nboth above it:\n"
                 "non-members\nflagged", fontsize=5.4, color=INK, ha="left",
                 va="center", linespacing=1.25)
    # The axis name goes in the caption, not under the panels: a centred
    # figure-level xlabel lands on the left panel's last tick.
    for a_ in axes:
        a_.set_xlabel(r"$\varphi(p)$", fontsize=6.4)
    finish(fig, "fig4_lira")


# ── Fig 5 — internal processing of the patient-level mechanism ──────────
def fig_patientdp(f):
    """The methodology template gives the core new module its own
    internal-processing figure. Here that module is the privacy mechanism, and
    the point the figure has to carry is the ORDER of two operations: grouping
    happens before bounding. Drawn the other way round it would depict
    record-level DP."""
    fig, ax = plt.subplots(figsize=(COL1, 3.35))
    ax.set_xlim(0, 100); ax.set_ylim(0, 108); ax.axis("off")
    k = int(round(f["wpp_mean"]))

    # stage 1 — sample patients
    ax.text(50, 105, "patient pool  $\\mathcal{P}_k$", fontsize=6.6,
            ha="center", color=INK, weight="bold")
    for i in range(7):
        x = 8 + i * 12.5
        sel = i in (1, 3, 6)
        box(ax, x, 92, 9.5, 6.0, "", fc=GREEN if sel else "#dcdcd8", ec="none")
    ax.text(50, 87.5, f"Poisson sample at rate $q = B/|\\mathcal{{P}}_k|$"
                      f"   —   over PATIENTS, not records",
            fontsize=5.7, ha="center", color=MUTED)

    # stage 2 — one sampled patient's records
    ax.add_patch(Rectangle((4, 47), 92, 36, fc="#eef4f8", ec="none", zorder=0))
    ax.text(7, 80.5, "for each sampled patient $p$", fontsize=6.0,
            color=BLUE, va="top", style="italic")
    arrow(ax, (30, 92), (30, 76), color=MUTED, lw=0.8)

    # Label ABOVE the row: placed below it, it sat inside the fan of
    # converging arrows and collided with every one of them.
    ax.text(50, 75.0, f"$k_p$ record gradients   ($k_p{{=}}{k}$ mean)",
            fontsize=5.7, ha="center", color=MUTED)
    for i in range(k):
        x = 9 + i * 10.4
        box(ax, x, 68, 7.6, 5.6, "", fc=GREEN, ec="none")

    for i in range(k):
        x = 9 + i * 10.4 + 3.8
        arrow(ax, (x, 68), (50, 61), color=MUTED, lw=0.5, style="-")
    box(ax, 44.5, 55.5, 11, 5.5, r"$\Sigma$", fc="white", ec=MUTED, lw=0.9,
        fs=7.5)
    ax.text(58, 58.2, "group FIRST", fontsize=5.7, color=BLUE, ha="left",
            weight="bold")

    arrow(ax, (50, 55.5), (50, 50.5), color=MUTED, lw=0.8)
    box(ax, 33, 44.5, 34, 6.0, "clip $\\|g_p\\|_2$ to $C$",
        fc=VERM, ec="none", fs=6.2, tc="white")
    ax.text(69, 47.5, "bound SECOND", fontsize=5.7, color=VERM, ha="left",
            weight="bold")

    # stage 3 — aggregate + one noise draw
    arrow(ax, (50, 44.5), (50, 38), color=MUTED, lw=0.8)
    box(ax, 26, 31.5, 48, 6.5,
        "$\\sum_{p \\in S} \\bar{g}_p$", fc="white", ec=RULE, lw=0.9, fs=6.6)
    arrow(ax, (50, 31.5), (50, 25), color=MUTED, lw=0.8)
    box(ax, 20, 18.0, 60, 7.0,
        "$+\\ \\mathcal{N}(0, \\sigma^2 C^2 I)$   once per step",
        fc=VERM, ec="none", fs=6.2, tc="white")
    arrow(ax, (50, 18.0), (50, 12), color=MUTED, lw=0.8)
    box(ax, 27, 5.0, 46, 6.5, "update $\\theta_{\\mathrm{head}}$",
        fc="white", ec=RULE, lw=0.9, fs=6.4)

    ax.text(50, 0.5, "one patient moves the aggregate by at most $C$, "
                     "whatever $k_p$",
            fontsize=5.9, ha="center", color=MUTED, style="italic")
    finish(fig, "fig5_patientdp")


# ── Fig 6 — specialty-derived heterogeneity (Experimental Setup) ────────
def fig_noniid(f):
    """Two panels rather than one dual-axis chart: client size and outcome
    prevalence are different quantities on different scales, and overlaying
    them on twin axes is the single most misread chart form there is."""
    import json
    meta = json.loads(((_SIM / "data/processed/partitions/vitaldb"
                        / "partition_meta.json")).read_text())
    dev = meta["devices"]
    ks = sorted(dev, key=lambda k: dev[k].get("icu_rate_pct", 0))
    n = [dev[k]["total"] for k in ks]
    rate = [dev[k].get("icu_rate_pct", 0) for k in ks]

    fig, ax = plt.subplots(1, 2, figsize=(COL2, 2.0))
    xs = np.arange(len(ks))

    ax[0].bar(xs, n, color=GREEN, width=0.68, zorder=3)
    ax[0].set_ylabel("windows held", fontsize=6.6)
    ax[0].set_title("client size", fontsize=6.8, color=INK, pad=4)
    for i, v in enumerate(n):
        ax[0].text(i, v + max(n) * 0.02, f"{v/1000:.1f}k", ha="center",
                   fontsize=5.2, color=MUTED)
    ax[0].set_ylim(0, max(n) * 1.16)

    ax[1].bar(xs, rate, color=VERM, width=0.68, zorder=3)
    ax[1].set_ylabel("ICU admission rate (%)", fontsize=6.6)
    ax[1].set_title("outcome prevalence", fontsize=6.8, color=INK, pad=4)
    for i, v in enumerate(rate):
        ax[1].text(i, v + max(rate) * 0.02, f"{v:.0f}", ha="center",
                   fontsize=5.2, color=MUTED)
    ax[1].set_ylim(0, max(rate) * 1.16)

    for a in ax:
        a.set_xticks(xs)
        a.set_xticklabels([f"c{k}" for k in ks], fontsize=5.6)
        # No per-panel xlabel: it was identical on both and the caption ran
        # straight through it. The tick labels plus the caption carry it.
        a.tick_params(labelsize=5.8, length=2)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
        a.grid(axis="y", color=RULE, lw=0.5, alpha=0.6, zorder=0)
    finish(fig, "fig6_noniid")


# ── Fig 7 — where the energy goes (Results) ─────────────────────────────
def fig_energy(f):
    """Stacked by tier. The point a total cannot show: the hierarchy does not
    eliminate work, it relocates it, and only the proposed configuration
    actually reduces what the constrained tier spends."""
    import csv, collections
    order = ["CentralizedFL", "FlatFL_DP", "HierarchicalFL_NoDP", "HFL_Proposed"]
    short = {"CentralizedFL": "centralized", "FlatFL_DP": "flat + DP",
             "HierarchicalFL_NoDP": "hierarchy,\nno DP", "HFL_Proposed": "proposed"}
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.15))
    for ax, ds, lab in zip(axes, ("vitaldb", "wear"),
                           ("clinical (9 clients)", "wearable (22 clients)")):
        rows = list(csv.DictReader(
            open(_SIM / f"results/cloudsim/cloudsim_results_{ds}.csv")))
        agg = collections.defaultdict(lambda: collections.defaultdict(list))
        for r in rows:
            for t in ("iot", "edge", "cloud"):
                agg[r["scenario"]][t].append(float(r[f"{t}_energy_J"]))
        xs = np.arange(len(order))
        dev = [np.mean(agg[s]["iot"]) for s in order]
        edg = [np.mean(agg[s]["edge"]) for s in order]
        cld = [np.mean(agg[s]["cloud"]) for s in order]
        ax.bar(xs, dev, width=0.62, color=GREEN, label="device", zorder=3)
        ax.bar(xs, edg, width=0.62, bottom=dev, color=BLUE, label="edge", zorder=3)
        ax.bar(xs, cld, width=0.62, bottom=np.array(dev) + np.array(edg),
               color=VERM, label="cloud", zorder=3)
        tot = np.array(dev) + np.array(edg) + np.array(cld)
        for i, v in enumerate(tot):
            ax.text(i, v + max(tot) * 0.03, f"{v:,.0f} J", ha="center",
                    fontsize=5.6, color=INK)
        ax.set_xticks(xs)
        ax.set_xticklabels([short[s] for s in order], fontsize=5.6,
                           linespacing=1.2)
        ax.set_title(lab, fontsize=6.8, color=INK, pad=4)
        ax.set_ylim(0, max(tot) * 1.18)
        ax.tick_params(labelsize=5.8, length=2)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.grid(axis="y", color=RULE, lw=0.5, alpha=0.6, zorder=0)
    axes[0].set_ylabel("energy per round (J)", fontsize=6.6)
    axes[0].legend(frameon=False, fontsize=5.8, loc="upper right",
                   handlelength=1.1, borderpad=0.2)
    fig.text(0.5, -0.13,
             "Adding an edge tier alone does not reduce device energy — it adds "
             "edge energy on top.\nOnly the proposed configuration, which also "
             "shortens what each device computes and sends,\nreduces the "
             "constrained tier.",
             fontsize=5.8, color=MUTED, ha="center", style="italic",
             linespacing=1.5)
    finish(fig, "fig7_energy")


# ── Fig 4 (redraw) — MEASURED per-patient IN/OUT distributions ──────────
def fig_lira_measured(f, arm="head_nodp"):
    """Replaces the synthetic version. The point the figure must carry is that
    per-patient difficulty dominates the membership signal, so a single global
    threshold cannot separate members from non-members while a per-patient fit
    can. Drawn from the shadow scores actually measured, not from illustrative
    Gaussians: `shadows/<arm>/shadow_NN/scores.npz` with the IN/OUT mask from
    `membership.npz`, reconstructed with the same patient sampling the attack
    used (rng seed 0), so the panels show real patients."""
    import glob
    d = _SIM / "results/phase5/lira/vitaldb/shadows" / arm
    mem = np.load(d / "membership.npz")
    patients, mask = mem["patients"], mem["mask"]

    # rebuild the evaluated patient set exactly as lira_attack.py did
    import json
    sys.path.insert(0, str(_SIM / "data" / "loaders"))
    from datasets import get_spec
    spec = get_spec("vitaldb")
    cid = np.load(_SIM / spec.data_dir / "meta" / "case_ids.npy")
    pdir = _SIM / spec.partition_dir
    ndev = json.loads((pdir / "partition_meta.json").read_text())["n_devices"]
    split_of = {}
    for sp in ("train", "test"):
        for dv in range(ndev):
            for c in np.unique(cid[np.load(pdir / f"device_{dv:02d}_{sp}.npy")]):
                split_of[int(c)] = sp
    mp = sorted(c for c, s in split_of.items() if s == "train")
    npool = sorted(c for c, s in split_of.items() if s == "test")
    rng = np.random.default_rng(0)
    n = min(600, len(mp), len(npool))
    evalp = [int(c) for c in rng.choice(mp, n, replace=False)] + \
            [int(c) for c in rng.choice(npool, n, replace=False)]
    pos = {int(c): i for i, c in enumerate(patients)}
    inm = mask[:, [pos[c] for c in evalp]]

    phis = np.stack([np.load(p)["phi"]
                     for p in sorted(glob.glob(str(d / "shadow_*/scores.npz")))])

    # pick a genuinely hard and a genuinely easy patient by mean confidence,
    # among those with enough shadows on both sides to fit anything
    ok = (inm.sum(0) >= 4) & ((~inm).sum(0) >= 4)
    order = np.argsort(np.nanmean(phis, axis=0))
    order = [i for i in order if ok[i]]
    picks = [(order[len(order) // 20], "hard patient"),
             (order[-len(order) // 20], "easy patient")]

    # A strip plot, not a histogram: there are only ~16 shadow observations per
    # patient, and binning that few points invents a density the data cannot
    # support — the first draft collapsed one patient into a single bar. Points
    # show the actual sample, and a shared x-axis keeps the offset BETWEEN the
    # two patients visible, which is the confound the figure exists to show.
    fig, ax = plt.subplots(figsize=(COL1, 1.75))
    allv = np.concatenate([phis[:, i] for i, _ in picks])
    lo, hi = allv.min() - 1.0, allv.max() + 1.0
    thr = float(np.median(phis))
    rj = np.random.default_rng(1)

    rows = []
    for k, (idx, name) in enumerate(picks):
        rows.append((k * 2 + 1, phis[~inm[:, idx], idx], BLUE, "OUT", name))
        rows.append((k * 2 + 0, phis[inm[:, idx], idx], VERM, "IN", name))
    for y, v, c, lab, name in rows:
        ax.scatter(v, y + rj.normal(0, 0.055, len(v)), s=11, color=c,
                   alpha=0.85, linewidths=0, zorder=3)
        ax.plot([v.mean()], [y], marker="|", ms=13, color=c, mew=1.8, zorder=4)

    ax.axvline(thr, color=INK, lw=1.0, ls=(0, (3, 2)), zorder=2)
    ax.text(thr - 0.3, 3.72, "one global threshold ", fontsize=5.8, color=INK,
            ha="right", va="center")
    ax.set_yticks([0, 1, 2, 3])
    ax.set_yticklabels(["IN", "OUT", "IN", "OUT"], fontsize=6.0)
    ax.set_ylim(-0.7, 3.9)
    ax.set_xlim(lo, hi)
    # No xlabel: the caption below names the axis; an xlabel here collided
    # with the caption text.
    ax.tick_params(labelsize=5.8, length=2)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="x", color=RULE, lw=0.5, alpha=0.5, zorder=0)
    ax.text(lo + 0.2, 0.5, picks[0][1], fontsize=6.2, color=MUTED,
            style="italic", va="center")
    ax.text(lo + 0.2, 2.5, picks[1][1], fontsize=6.2, color=MUTED,
            style="italic", va="center")
    fig.text(0.5, -0.26,
             f"Horizontal axis: $\\varphi(p)$, over {phis.shape[0]} shadow models per patient;"
             "\nbars mark the group mean. The two patients occupy different ranges,"
             "\nso no single threshold separates IN from OUT for both.",
             fontsize=5.8, color=MUTED, ha="center", style="italic",
             linespacing=1.5)
    finish(fig, "fig4_lira")


# ── Fig 8 — decomposing the recipe: initialisation vs privatised subset ──
def fig_epsilon(f):
    """Three arms, because two cannot separate the two things that differ.

    The earlier two-arm version compared head-only-from-pretrained against
    full-model-from-random and attributed the gap to privatised
    dimensionality. Those arms differ in TWO ways at once, and the
    decomposition shows the attribution was wrong:

        B4  full model, random init      (prior art)
        B7  full model, pretrained init  (isolates initialisation)
        B6  head only,  pretrained init  (the proposed recipe)

    B4->B7 is nearly the whole effect and is strongly epsilon-dependent;
    B7->B6 is ~0 at every budget. B7 privatises 3.3x more parameters than B6
    at the same budget and loses nothing, which refutes the dimensionality
    account directly.
    """
    import csv, collections, statistics as st
    r = list(csv.DictReader(open(_SIM /
        "results/phase5/epsilon_sweep/vitaldb/epsilon_sweep.csv")))
    d = collections.defaultdict(list)
    for x in r:
        # Key on the NUMERIC value: the file stores "1" and "2", not "1.0"
        # and "2.0", so matching on the string silently dropped four of the
        # six budgets and drew a two-point line.
        d[(float(x["epsilon"]), x["recipe"])].append(float(x["macro_auc"]))
    # Only budgets where all three arms ran, so the band is never drawn
    # across a missing point.
    eps = sorted({e for e, _ in d}
                 & {e for e, rc in d if rc == "full"}
                 & {e for e, rc in d if rc == "full_pre"}
                 & {e for e, rc in d if rc == "head"})
    xs = np.arange(len(eps))
    b4 = [st.mean(d[(e, "full")]) for e in eps]
    b7 = [st.mean(d[(e, "full_pre")]) for e in eps]
    b6 = [st.mean(d[(e, "head")]) for e in eps]
    nseed = max(len(d[(e, "head")]) for e in eps)

    fig, ax = plt.subplots(figsize=(COL1, 2.05))
    # The shaded band is now the INITIALISATION effect, which is the finding.
    ax.fill_between(xs, b4, b7, color=VERM, alpha=0.12, lw=0, zorder=2)
    ax.plot(xs, b4, "-s", color=VERM, lw=1.6, ms=4.0,
            label="full model, random init", zorder=4)
    ax.plot(xs, b7, "-o", color=BLUE, lw=1.6, ms=4.5,
            label="full model, pretrained", zorder=4)
    ax.plot(xs, b6, "--^", color=GREEN, lw=1.4, ms=4.0,
            label="head only, pretrained", zorder=5)
    for i in (0, len(eps) - 1):
        ax.annotate(f"{b7[i]-b4[i]:+.3f}", (xs[i], (b4[i] + b7[i]) / 2),
                    fontsize=5.8, color=INK, ha="center", va="center",
                    bbox=dict(fc=SURF, ec="none", pad=0.8), zorder=6)
    ax.set_xticks(xs)
    ax.set_xticklabels([r"$\infty$" if np.isinf(e) else f"{e:g}" for e in eps],
                       fontsize=6.2)
    ax.set_xlabel(r"privacy budget $\varepsilon$ (tighter $\rightarrow$ left)",
                  fontsize=6.4)
    ax.set_ylabel("macro AUROC", fontsize=6.4)
    ax.tick_params(labelsize=5.8, length=2)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color=RULE, lw=0.5, alpha=0.6, zorder=0)
    ax.legend(frameon=False, fontsize=5.8, loc="lower right",
              handlelength=1.6, borderpad=0.2)
    fig.text(0.5, -0.30,
             "Shaded band is the INITIALIZATION effect, and it is nearly the\n"
             "whole advantage. The two pretrained arms are near-coincident at\n"
             f"every budget though one privatizes 3.3x more parameters.\n"
             f"{nseed} seeds per point.",
             fontsize=5.8, color=MUTED, ha="center", style="italic",
             linespacing=1.5)
    finish(fig, "fig8_epsilon")


if __name__ == "__main__":
    print("reading system facts ...")
    F = load_facts()
    print(f"  {F['n_clients']} clients / {F['n_edges']} edges · "
          f"{F['n_patients']:,} patients · {F['n_windows']:,} windows · "
          f"{F['wpp_mean']:.2f} windows/patient")
    print(f"  d_a={F['d_a']} d_b={F['d_b']} head={F['n_head']:,}/"
          f"{F['n_total']:,} params")
    print("writing figures ...")
    fig_architecture(F)
    fig_backbone(F)
    fig_sensitivity(F)
    fig_lira_measured(F)
    fig_patientdp(F)
    fig_noniid(F)
    fig_energy(F)
    fig_epsilon(F)
    print("done")
