"""fig00_workflow.py — study workflow: data -> private hierarchical training ->
evaluation and audit, drawn as three shaded stage bands with a round loop.

Every number on the drawing is read from a file: client and edge counts from
each corpus' partition_meta.json, tau_e from config/hfl_config.json, the
sparsification ratio from the same config.

    python fig00_workflow.py        -> fig00_workflow.{pdf,png}
"""
import json
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
from _figstyle import plt, RES, DOUBLE, C, CORPUS, save
from _icons import Icons

SIM = RES.parent
CFG = json.load(open(SIM / "config" / "hfl_config.json"))
TAU_E = CFG["federated_learning"]["tau_e"]
SPARSITY = CFG["model"]["sparsification_ratio"]
DS = ("vitaldb", "wear", "eicu")
META = {d: json.load(open(SIM / "data" / "processed" / "partitions" / d /
                          "partition_meta.json")) for d in DS}
LABEL = dict(vitaldb="VitalDB", wear="WEAR", eicu="eICU")

BAND = dict(data="#E3EEF9", train="#FCEBDD", eval="#E2F2EA")
BAND_EDGE = dict(data="#9DBFE3", train="#EBB48C", eval="#93CDB0")
INK = "#2B2B2B"


IC = None          # Icons instance, set once the axes exist
ICON_W = 0.034     # width of the icon column inside a box (axes units)


def box(ax, xy, w, h, text, fc="white", ec=INK, fs=6.2, color=INK, weight="normal",
        r=0.012, lw=0.6, icon=None, isz=0.22):
    """Rounded box; with icon=(name, kwargs) a flat icon sits in a left column
    and the text centres in the remaining width."""
    x, y = xy
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, lw=lw, fc=fc, ec=ec,
                                boxstyle=f"round,pad=0,rounding_size={r}"))
    tx = x
    if icon:
        name, kw = icon if isinstance(icon, tuple) else (icon, {})
        getattr(IC, name)(x - w / 2 + 0.006 + ICON_W / 2, y, isz, **kw)
        tx = x + ICON_W / 2 + 0.003
    ax.text(tx, y, text, ha="center", va="center", fontsize=fs, color=color,
            weight=weight, linespacing=1.15, zorder=5)
    return dict(l=(x - w / 2, y), r=(x + w / 2, y), t=(x, y + h / 2),
                b=(x, y - h / 2), c=(x, y))


def pill(ax, xy, text, fc):
    return box(ax, xy, 0.075, 0.075, text, fc=fc, ec="#5C8F3A", fs=6.8,
               weight="bold", r=0.035)


def diamond(ax, xy, w, h, text, fc="#F6C8DC", ec="#B0477A"):
    x, y = xy
    ax.add_patch(Polygon([(x - w / 2, y), (x, y + h / 2), (x + w / 2, y),
                          (x, y - h / 2)], closed=True, fc=fc, ec=ec, lw=0.6))
    ax.text(x, y, text, ha="center", va="center", fontsize=6, color=INK)
    return dict(l=(x - w / 2, y), r=(x + w / 2, y), t=(x, y + h / 2),
                b=(x, y - h / 2))


def arrow(ax, p, q, color=INK, lw=0.7, conn="arc3,rad=0", ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=6,
                                 lw=lw, color=color, ls=ls, connectionstyle=conn,
                                 shrinkA=0, shrinkB=0))


def path(ax, pts, color=INK, lw=0.7):
    """Right-angle connector through waypoints, arrowhead on the last leg."""
    xs, ys = zip(*pts)
    ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, solid_capstyle="butt")
    arrow(ax, pts[-2], pts[-1], color=color, lw=lw)


def band(ax, y0, y1, key, title):
    ax.add_patch(FancyBboxPatch((0.006, y0), 0.988, y1 - y0, fc=BAND[key],
                                ec=BAND_EDGE[key], lw=0.6,
                                boxstyle="round,pad=0,rounding_size=0.012"))
    ax.text(0.970, y1 - 0.018, title, ha="right", va="top", fontsize=7.4,
            weight="bold", style="italic", color=INK)


def main():
    fig = plt.figure(figsize=(DOUBLE, 3.05))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    global IC
    IC = Icons(ax)

    band(ax, 0.685, 0.995, "data", "Data and partitioning")
    band(ax, 0.355, 0.675, "train", "Private hierarchical training")
    band(ax, 0.005, 0.345, "eval", "Evaluation and audit")

    # ── data ────────────────────────────────────────────────────────────
    yd = 0.83
    s = pill(ax, (0.05, yd), "START", "#CDE8B5")
    corp = box(ax, (0.203, yd), 0.18, 0.16,
               "three corpora\n" + " · ".join(LABEL[d] for d in DS),
               fc="white", icon="database", isz=0.26)
    tx = 0.203 + ICON_W / 2 + 0.003
    for d, off in zip(DS, (-0.039, 0.008, 0.048)):   # colour key under each name
        ax.plot(tx + off, yd - 0.05, marker=CORPUS[d][1], ms=3.4,
                color=CORPUS[d][0], ls="none", zorder=5)
    split = box(ax, (0.39, yd), 0.15, 0.13,
                "split by individual:\nno person spans\ntwo splits", icon="person",
                isz=0.24)
    pool = box(ax, (0.60, 0.735), 0.17, 0.068, "public pool (disjoint)",
               icon="database", isz=0.15)
    cli = box(ax, (0.60, 0.905), 0.17, 0.068,
              "clients: " + " · ".join(str(META[d]["n_devices"]) for d in DS),
              icon="hospital", isz=0.135)
    vt = box(ax, (0.60, 0.82), 0.17, 0.068, "validation and test cohorts",
             fc="#F4F4F4", ec="#888888")
    arrow(ax, s["r"], corp["l"])
    arrow(ax, corp["r"], split["l"])
    xj = 0.488
    ax.plot([split["r"][0], xj], [yd, yd], color=INK, lw=0.7)
    ys = [t["l"][1] for t in (pool, cli, vt)]
    ax.plot([xj, xj], [min(ys), max(ys)], color=INK, lw=0.7)
    for tgt in (pool, cli, vt):
        arrow(ax, (xj, tgt["l"][1]), tgt["l"])

    # ── training ────────────────────────────────────────────────────────
    yt = 0.52
    # encoder configuration differs by corpus; only eICU is end to end
    cfgs = [("eicu", "eICU: disjoint encoders,\npool-fitted constants\n"
                     "$\\rightarrow$ end to end (one hospital)"),
            ("vitaldb", "VitalDB: oracle encoders\n(disjoint in F2)\n"
                        "$\\rightarrow$ patient-level head"),
            ("wear", "WEAR: oracle encoders,\none person per client\n"
                     "$\\rightarrow$ record-level head")]
    xc, wc, hc = 0.098, 0.168, 0.086
    pres = []
    for (d, t), y in zip(cfgs, (0.613, 0.515, 0.417)):
        b = box(ax, (xc + 0.008, y), wc - 0.016, hc, t, fs=5.4,
                fc="#FFFFFF" if d == "eicu" else "#EFEFEF",
                ec=CORPUS[d][0], lw=0.9 if d == "eicu" else 0.6)
        ax.plot(xc - wc / 2 + 0.003, y, marker=CORPUS[d][1], ms=3.6,
                color=CORPUS[d][0], ls="none", zorder=5)
        pres.append(b)
    dp = box(ax, (0.29, yt), 0.15, 0.16,
             "client $k$: sample\nindividuals at rate $q_k$,\nsum, clip to $C$,\n"
             "add $\\mathcal{N}(0,\\sigma_k^2C^2)$",
             fc=C["indiv"], ec=C["indiv"], color="white", fs=6.0,
             icon=("shield", dict(fc="#FFFFFF")), isz=0.26)
    comp = box(ax, (0.465, yt), 0.13, 0.12,
               f"compress update\ntop-{SPARSITY:.0%} + 8-bit,\nerror feedback")
    edge = box(ax, (0.635, yt), 0.12, 0.12,
               f"edge FedAvg\n$\\tau_e = {TAU_E}$\nrounds", icon="server", isz=0.26)
    cloud = box(ax, (0.79, yt), 0.11, 0.12, "cloud\nFedAvg,\nbroadcast",
                icon="cloud", isz=0.2)
    last = diamond(ax, (0.915, yt), 0.1, 0.17, "last\nround?")
    path(ax, [pool["b"], (pool["b"][0], 0.666), (pres[0]["t"][0], 0.666),
              pres[0]["t"]], color="#777777")
    path(ax, [cli["r"], (0.715, cli["r"][1]), (0.715, 0.635), (dp["t"][0] + 0.03, 0.635),
              (dp["t"][0] + 0.03, dp["t"][1])])
    xb = 0.199                                   # bus from the three configs
    for b in pres:
        ax.plot([b["r"][0], xb], [b["r"][1]] * 2, color="#777777", lw=0.6)
    ax.plot([xb, xb], [pres[-1]["r"][1], pres[0]["r"][1]], color="#777777", lw=0.6)
    arrow(ax, (xb, yt), dp["l"], color="#777777")
    arrow(ax, dp["r"], comp["l"])
    arrow(ax, comp["r"], edge["l"])
    arrow(ax, edge["r"], cloud["l"])
    arrow(ax, cloud["r"], last["l"])
    # loop back: no -> next round at the clients
    yl = 0.395
    path(ax, [last["b"], (last["b"][0], yl), (dp["b"][0], yl), dp["b"]],
         color="#B0477A")
    ax.text(0.60, yl + 0.016, "no: next cloud round", fontsize=5.8,
            color="#B0477A", ha="center", va="bottom", style="italic")

    # ── evaluation ──────────────────────────────────────────────────────
    ye = 0.15
    sel = box(ax, (0.085, ye), 0.135, 0.12,
              "select model\non validation\ncohort")
    path(ax, [last["r"], (0.985, yt), (0.985, 0.272), (sel["t"][0], 0.272), sel["t"]])
    ax.text(0.972, yt + 0.012, "yes", fontsize=5.8, ha="right", va="bottom",
            style="italic")
    evals = [
        ("utility cost\nDP vs non-DP,\npaired seeds, 95% CI", "white", "chart"),
        ("privacy-unit test\ncost vs records\nper individual $k$", "white", "patient"),
        ("system cost\nNS-3 packets,\nCloudSim energy", "white", "server"),
        ("privacy audit\nloss + LiRA,\npositive control", "#D8E9F5", "attacker"),
    ]
    xs = (0.27, 0.45, 0.63, 0.81)
    outs = []
    for x, (t, fc, icn) in zip(xs, evals):
        b = box(ax, (x, ye), 0.155, 0.15, t, fc=fc, fs=5.9, icon=icn, isz=0.28)
        outs.append(b)
    arrow(ax, sel["r"], outs[0]["l"])
    for a, b in zip(outs, outs[1:]):
        arrow(ax, a["r"], b["l"], color="#777777", ls=(0, (2, 1.5)))
    end = pill(ax, (0.945, ye), "END", "#CDE8B5")
    arrow(ax, outs[-1]["r"], end["l"])

    save(fig, "fig00_workflow")


if __name__ == "__main__":
    main()
