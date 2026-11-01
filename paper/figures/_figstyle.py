"""_figstyle.py — house style shared by every fig*_*.py script (paper/figs.md §0).

IEEE two-column geometry, 8 pt Times-compatible text, embedded TrueType
fonts, Okabe-Ito colours paired with a marker so every figure survives
greyscale. Result paths resolve from this file; nothing is typed in.
"""
from pathlib import Path
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

HERE = Path(__file__).resolve().parent
RES = HERE.parents[1] / "SIMULATORS" / "results"

SINGLE, DOUBLE = 3.5, 7.16           # inches (IEEE column / page width)

C = dict(indiv="#D55E00", record="#0072B2", ctrl="#7F7F7F", pre="#009E73",
         rand="#E69F00", fused="#CC79A7", ref="#000000", purple="#CC79A7")
CORPUS = dict(vitaldb=("#0072B2", "o"), wear=("#E69F00", "s"),
              eicu=("#009E73", "^"))
NAME = dict(vitaldb="VitalDB (clinical)", wear="WEAR (wearable)",
            eicu="eICU (external)")

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "STIXGeneral",
                   "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.direction": "out", "ytick.direction": "out",
    "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 1.2, "lines.markersize": 4,
    "errorbar.capsize": 2, "legend.frameon": False,
    "pdf.fonttype": 42, "ps.fonttype": 42,          # embed TrueType
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})


def tci(xs, level=0.95):
    """Mean and Student-t half-width (0 for n < 2)."""
    xs = list(xs)
    n = len(xs)
    m = sum(xs) / n
    if n < 2:
        return m, 0.0
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return m, stats.t.ppf(0.5 + level / 2, n - 1) * sd / math.sqrt(n)


def panel(ax, letter, x=-0.16, y=1.04):
    ax.text(x, y, f"({letter})", transform=ax.transAxes, fontsize=9,
            fontweight="bold", va="bottom", ha="left")


def ygrid(ax):
    ax.yaxis.grid(True, lw=0.3, color="#DDDDDD")
    ax.set_axisbelow(True)


def save(fig, name):
    out = HERE / f"{name}.pdf"
    fig.savefig(out)
    fig.savefig(HERE / f"{name}.png", dpi=300)
    plt.close(fig)
    print(f"wrote {out}")
