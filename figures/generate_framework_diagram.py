"""
generate_framework_diagram.py — Fig. 1, HFL-MM framework.

REWRITTEN 2026-08-03. The previous figure advertised a system that was not
built. Each change and its reason:

  * Layer 1 showed UNIMODAL devices ("ECG Patch" vs "X-Ray Unit" in separate
    clusters). The implementation gives EVERY client BOTH modalities for the
    same sample. Federating across unimodal clients is a different, harder
    problem than the one this codebase solves.
  * CMGA cross-modal fusion was drawn at every edge server. It is implemented
    nowhere (clinical_cmga_design.py has zero references) and the code fuses
    ON DEVICE via LateFusionHead, not at the edge.
  * Datasets read "PTB-XL / CheXpert". CheXpert was never used at all, and the
    PTB-XL pipeline is retired because its two modalities were paired by a RULE
    (CXR bucket = f(ECG label)) — not evidence of fusion.
  * Encoder B read "MobileNetV3"; it is a FeatureEncoder MLP for both current
    datasets.
  * Topology read 6 hospitals / 20 devices / 6 edges — three mutually
    inconsistent numbers, none matching any run.
  * Results were 76.4 % / 74.9 % / 99.05 % / eps=0.8, all superseded.
  * Innovations listed CMGA, SADP and pFAL as contributions. CMGA is
    unimplemented, SADP measured WORSE than uniform DP, pFAL measured zero
    effect.

Previous version: generate_framework_diagram_SUPERSEDED_2026-08-03.py.bak
Every number below is traceable to results/phase5/.
"""

import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

C = {
    "bg": "#F4F6FB", "ink": "#1B2631", "mute": "#5D6D7E",
    "dev": "#FFF6E5", "dev_e": "#E8A33D",
    "edge": "#E8F6EF", "edge_e": "#2E9E75",
    "cloud": "#E7F0FD", "cloud_e": "#2E6FD1",
    "priv": "#FDECEC", "priv_e": "#C0392B",
    "meas": "#F3EAFB", "meas_e": "#7D3C98",
    "warn": "#FDF3E3", "warn_e": "#B9770E",
}
W, H = 26.0, 17.4
fig, ax = plt.subplots(figsize=(W, H), dpi=170)
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
fig.patch.set_facecolor(C["bg"])


def box(x, y, w, h, fc, ec, lw=1.6, r=0.16, z=1):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle=f"round,pad=0.02,rounding_size={r}",
                 facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z))


def t(x, y, s, fs=11, bold=False, c=None, ha="center", z=5, style=None, fam=None):
    ax.text(x, y, s, fontsize=fs, ha=ha, va="center", zorder=z,
            color=c or C["ink"], fontweight="bold" if bold else "normal",
            fontstyle=style or "normal", fontfamily=fam)


def arrow(x1, y1, x2, y2, c, lw=1.6):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                 mutation_scale=13, color=c, linewidth=lw, zorder=3,
                 shrinkA=2, shrinkB=2))


# ── title ──────────────────────────────────────────────────────────────────
t(9.4, 16.85, "HFL-MM — Hierarchical Federated Multimodal Learning", fs=23, bold=True)
t(9.4, 16.35, "Privacy-preserving edge–cloud framework  ·  every client is multimodal  ·  "
              "DP applied to the fusion head only", fs=12.5, c=C["mute"], style="italic")

# ════════ LAYER 1 — DEVICES ════════
box(0.4, 0.5, 18.2, 5.5, "#FFFFFF", C["dev_e"], lw=2.0)
t(0.95, 3.25, "LAYER 1\nIoT / IoMT\nDevices", fs=11.5, bold=True, c=C["dev_e"])
t(9.9, 5.62, "Each device holds BOTH modalities for the SAME sample — genuinely paired at capture",
  fs=11.5, bold=True, c=C["dev_e"])

for x, lb in zip([2.2, 6.3, 10.4, 14.5], ["Client 1", "Client 2", "Client k", "Client N"]):
    box(x, 1.02, 3.6, 4.25, C["dev"], C["dev_e"], lw=1.5, z=2)
    t(x + 1.8, 4.95, lb, fs=12.5, bold=True)
    box(x + 0.15, 3.75, 1.58, 0.98, "#FFFFFF", C["dev_e"], lw=1.1, z=3)
    t(x + 0.94, 4.45, "Modality A", fs=9.5, bold=True)
    t(x + 0.94, 4.17, "time-series", fs=8.3, c=C["mute"])
    t(x + 0.94, 3.95, "FedMamba enc.", fs=8.3, c="#1A5276")
    box(x + 1.87, 3.75, 1.58, 0.98, "#FFFFFF", C["dev_e"], lw=1.1, z=3)
    t(x + 2.66, 4.45, "Modality B", fs=9.5, bold=True)
    t(x + 2.66, 4.17, "feature vector", fs=8.3, c=C["mute"])
    t(x + 2.66, 3.95, "FeatureEncoder", fs=8.3, c="#1A5276")
    arrow(x + 0.94, 3.73, x + 1.55, 3.25, C["dev_e"], 1.2)
    arrow(x + 2.66, 3.73, x + 2.05, 3.25, C["dev_e"], 1.2)
    box(x + 0.45, 2.45, 2.7, 0.76, "#D6EAF8", "#2874A6", lw=1.3, z=3)
    t(x + 1.8, 3.01, "Late Fusion Head", fs=9.5, bold=True, c="#1A5276")
    t(x + 1.8, 2.71, "256 + 576 → 832 → classes", fs=7.8, c=C["mute"])
    box(x + 0.45, 1.67, 2.7, 0.64, C["priv"], C["priv_e"], lw=1.2, z=3)
    t(x + 1.8, 1.99, "DP-SGD  ε ≤ 1  (HEAD ONLY)", fs=8.4, bold=True, c=C["priv_e"])
    box(x + 0.45, 1.15, 2.7, 0.44, "#EDE7F6", "#5E35B1", lw=1.1, z=3)
    t(x + 1.8, 1.37, "Top-k 20 % + INT8", fs=8.4, c="#4527A0")

t(9.9, 0.68, "encoders are PRE-TRAINED then FROZEN — only the 14–30 % fusion head is "
             "DP-trained and transmitted", fs=10, c=C["priv_e"], style="italic")

for x in [2.2, 6.3, 10.4, 14.5]:
    arrow(x + 1.2, 6.04, x + 1.2, 6.72, "#1F618D", 1.7)
    arrow(x + 2.4, 6.72, x + 2.4, 6.04, C["edge_e"], 1.7)
t(1.05, 6.40, "Δhead ↑", fs=9, c="#1F618D", ha="left")
t(17.35, 6.40, "W ↓", fs=9, c=C["edge_e"], ha="left")

# ════════ LAYER 2 — EDGES ════════
box(0.4, 6.75, 18.2, 3.35, "#FFFFFF", C["edge_e"], lw=2.0)
t(0.95, 8.4, "LAYER 2\nEdge\nServers", fs=11.5, bold=True, c=C["edge_e"])
for x, lb in zip([3.0, 11.1], ["Edge Server 1", "Edge Server 2"]):
    box(x, 7.05, 6.6, 2.68, C["edge"], C["edge_e"], lw=1.5, z=2)
    t(x + 3.3, 9.40, lb, fs=13, bold=True)
    box(x + 0.25, 8.26, 3.0, 0.90, "#FFFFFF", C["edge_e"], lw=1.2, z=3)
    t(x + 1.75, 8.90, "Edge FedAvg", fs=10.5, bold=True, c="#1D8348")
    t(x + 1.75, 8.56, "τ_e = 5 local rounds", fs=8.4, c=C["mute"])
    box(x + 3.40, 8.26, 2.9, 0.90, "#FFFFFF", C["edge_e"], lw=1.2, z=3)
    t(x + 4.85, 8.90, "ASWA", fs=10.5, bold=True, c="#1D8348")
    t(x + 4.85, 8.56, "staleness-weighted", fs=8.4, c=C["mute"])
    box(x + 0.25, 7.26, 6.05, 0.82, C["warn"], C["warn_e"], lw=1.1, z=3)
    t(x + 3.3, 7.85, "FedKD-E — implemented, NOT freeze-aware", fs=9, bold=True, c=C["warn_e"])
    t(x + 3.3, 7.52, "excluded from every reported run (--edge_distill_epochs 0)",
      fs=7.9, c=C["mute"])

arrow(6.3, 10.12, 8.6, 10.86, "#1F618D", 1.9)
arrow(14.4, 10.12, 10.4, 10.86, "#1F618D", 1.9)
arrow(9.0, 10.86, 6.8, 10.12, C["cloud_e"], 1.9)
arrow(10.9, 10.86, 14.9, 10.12, C["cloud_e"], 1.9)

# ════════ LAYER 3 — CLOUD ════════
box(0.4, 10.9, 18.2, 4.9, "#FFFFFF", C["cloud_e"], lw=2.0)
t(0.95, 13.3, "LAYER 3\nCloud\nServer", fs=11.5, bold=True, c=C["cloud_e"])

box(2.1, 11.15, 7.5, 4.35, C["cloud"], C["cloud_e"], lw=1.6, z=2)
t(5.85, 15.10, "Global FedAvg", fs=15, bold=True, c=C["cloud_e"])
t(5.85, 14.62, "W_global = Σ (n_k / N) · W_k", fs=12, fam="monospace")
t(5.85, 14.14, "only the fusion head is aggregated —", fs=9.8, c=C["mute"])
t(5.85, 13.86, "frozen encoders give a zero delta", fs=9.8, c=C["mute"])
box(2.45, 11.45, 6.8, 2.12, "#FFFFFF", C["cloud_e"], lw=1.1, z=3)
t(5.85, 13.34, "M E A S U R E D", fs=9.5, bold=True, c=C["mute"])
t(5.85, 12.98, "Uplink reduction    93.7 % / 94.4 %", fs=10.8, bold=True, c="#1E8449")
t(5.85, 12.62, "Energy saving       72.3 % / 76.8 %", fs=10.8, bold=True, c="#1E8449")
t(5.85, 12.26, "Update reliability        99.80 %", fs=10.8, bold=True, c=C["cloud_e"])
t(5.85, 11.90, "Inference P95      3.07 / 1.22 ms", fs=10.8, bold=True, c=C["cloud_e"])
t(5.85, 11.60, "vitaldb / wear", fs=8.4, c=C["mute"], style="italic")

box(10.0, 11.15, 8.2, 4.35, C["priv"], C["priv_e"], lw=1.6, z=2)
t(14.1, 15.10, "Privacy Accounting", fs=15, bold=True, c=C["priv_e"])
t(14.1, 14.64, "head-only DP fine-tuning", fs=11.5, bold=True)
t(14.1, 14.28, "σ = 11.33    C = 1.0    δ = 1e-5", fs=11, fam="monospace")
box(10.35, 12.12, 7.5, 2.02, "#FFFFFF", C["priv_e"], lw=1.1, z=3)
t(14.1, 13.84, "ε  training            0.99", fs=11, bold=True, fam="monospace")
t(14.1, 13.48, "ε  conformal           0.50", fs=11, bold=True, fam="monospace")
t(14.1, 13.08, "ε  TOTAL               1.49", fs=12.5, bold=True, c=C["priv_e"], fam="monospace")
t(14.1, 12.74, "basic composition — the conformal budget", fs=8.4, c=C["mute"])
t(14.1, 12.48, "is spent on private validation data", fs=8.4, c=C["mute"])
t(14.1, 12.24, "and MUST be counted", fs=8.4, c=C["mute"], style="italic")
t(14.1, 11.76, "no measurable utility cost at ε = 1", fs=10.5, bold=True, c="#1E8449")
t(14.1, 11.44, "ΔAUC −0.0014,  95 % CI [−0.020, +0.018]", fs=8.8, c=C["mute"])

# ════════ RIGHT — ABLATION ════════
box(19.0, 8.3, 6.6, 7.5, "#FFFFFF", C["meas_e"], lw=2.0)
t(22.3, 15.42, "MODALITY ABLATION", fs=14, bold=True, c=C["meas_e"])
t(22.3, 15.05, "retrained unimodal arms · 2 seeds", fs=9, c=C["mute"], style="italic")

box(19.35, 11.95, 5.9, 2.85, C["meas"], C["meas_e"], lw=1.3, z=2)
t(22.3, 14.52, "VitalDB — clinical IoMT", fs=12, bold=True)
t(22.3, 14.18, "6,257 surgeries · ICU admission", fs=8.4, c=C["mute"])
t(19.75, 13.80, "arm", fs=9.3, bold=True, ha="left")
t(23.35, 13.80, "AUROC", fs=9.3, bold=True)
t(24.70, 13.80, "AUPRC", fs=9.3, bold=True)
for i, (nm, a, p) in enumerate([("signals only", "0.8283", "0.5281"),
                                ("clinical only", "0.7700", "0.5022")]):
    t(19.75, 13.46 - i * 0.31, nm, fs=9.3, ha="left")
    t(23.35, 13.46 - i * 0.31, a, fs=9.3, fam="monospace")
    t(24.70, 13.46 - i * 0.31, p, fs=9.3, fam="monospace")
t(19.75, 12.78, "FUSED", fs=10.3, bold=True, ha="left", c="#1E8449")
t(23.35, 12.78, "0.8694", fs=10.3, bold=True, c="#1E8449", fam="monospace")
t(24.70, 12.78, "0.6343", fs=10.3, bold=True, c="#1E8449", fam="monospace")
t(22.3, 12.40, "gain   AUROC +0.041   AUPRC +0.106", fs=9.8, bold=True, c="#1E8449")
t(22.3, 12.12, "beats BOTH arms → Gap #1 demonstrated", fs=8.4, c="#1E8449", style="italic")

box(19.35, 9.50, 5.9, 2.25, C["warn"], C["warn_e"], lw=1.3, z=2)
t(22.3, 11.45, "WEAR — wearable IoT", fs=12, bold=True)
t(22.3, 11.14, "22 subjects · 18 activities", fs=8.4, c=C["mute"])
for i, (nm, a, p) in enumerate([("inertial only", "0.9976", "0.9761"),
                                ("video only", "0.9957", "0.9629"),
                                ("FUSED", "0.9980", "0.9831")]):
    b = nm == "FUSED"
    t(19.75, 10.78 - i * 0.30, nm, fs=9.3, bold=b, ha="left")
    t(23.35, 10.78 - i * 0.30, a, fs=9.3, bold=b, fam="monospace")
    t(24.70, 10.78 - i * 0.30, p, fs=9.3, bold=b, fam="monospace")
t(22.3, 9.76, "gain +0.0004 / +0.007 — AT CEILING", fs=9.3, bold=True, c=C["warn_e"])

t(22.3, 8.94, "The multimodal claim rests on VitalDB.", fs=10, bold=True)
t(22.3, 8.62, "WEAR is solved by one modality alone and", fs=8.8, c=C["mute"])
t(22.3, 8.40, "cannot evidence fusion — reported as such.", fs=8.8, c=C["mute"])

# ════════ RIGHT — STATUS ════════
box(19.0, 0.5, 6.6, 7.4, "#FFFFFF", C["mute"], lw=1.8)
t(22.3, 7.50, "COMPONENT STATUS", fs=13, bold=True)
t(22.3, 7.17, "claimed  vs.  measured", fs=9, c=C["mute"], style="italic")

rows = [
    ("Head-only DP fine-tuning", "VALIDATED", "#1E8449", "fixes ε=1 collapse, 0.56 → 0.87 AUC"),
    ("Gradient compression",     "VALIDATED", "#1E8449", "93.7 % uplink reduction, measured"),
    ("Multimodal late fusion",   "VALIDATED", "#1E8449", "+0.106 AUPRC on VitalDB"),
    ("ASWA aggregation",         "UNABLATED", "#B9770E", "wired and running, effect unknown"),
    ("FedKD-E distillation",     "EXCLUDED",  "#B9770E", "not freeze-aware; off in every run"),
    ("SADP adaptive DP",         "NEGATIVE",  "#C0392B", "worse than uniform (composition tax)"),
    ("pFAL personalisation",     "NO EFFECT", "#C0392B", "0.5397 vs 0.5407 AUC"),
    ("CMGA cross-modal attn.",   "NOT BUILT", "#C0392B", "zero references in the codebase"),
]
y = 6.60
for name, st, col, note in rows:
    t(19.35, y, name, fs=9.8, bold=True, ha="left")
    t(25.25, y, st, fs=8.8, bold=True, c=col, ha="right")
    t(19.35, y - 0.25, note, fs=8.0, c=C["mute"], ha="left")
    y -= 0.77

t(22.3, 0.70, "every figure traceable to results/phase5/", fs=8.4,
  c=C["mute"], style="italic")

# ── footer ─────────────────────────────────────────────────────────────────
box(0.4, 0.02, 18.2, 0.42, "#FFFFFF", "#D5D8DC", lw=1.0, r=0.08)
t(3.2, 0.23, "→  head delta (DP-noised, compressed)", fs=9, c="#1F618D")
t(9.6, 0.23, "→  global model download", fs=9, c=C["edge_e"])
t(15.4, 0.23, "VitalDB: 9 clients · WEAR: 22 clients · 2 edges", fs=9, c=C["mute"])

out = str(pathlib.Path(__file__).parent / "Fig1_HFL_MM_Framework.png")
plt.savefig(out, dpi=170, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"[SAVED] {out}")
