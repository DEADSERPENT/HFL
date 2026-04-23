import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ── canvas ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(38, 26))
fig.patch.set_facecolor('#F0F4FA')
ax.set_facecolor('#F0F4FA')
ax.set_xlim(0, 32)
ax.set_ylim(0, 22)
ax.axis('off')

# ── palette ───────────────────────────────────────────────────────────────────
P = dict(
    dev_band   = '#FFFDE7', dev_bd  = '#F9A825',
    edge_band  = '#E8F8F5', edge_bd = '#1E8449',
    cloud_band = '#EBF5FB', cld_bd  = '#1A5276',
    dev_box    = '#FFF8E1', xray_box= '#EDE7F6',
    dp         = '#FDECEA', dp_bd   = '#C0392B',
    topk       = '#F3E5F5', topk_bd = '#7B1FA2',
    cmga       = '#A9DFBF', cmga_bd = '#196F3D',
    fedavg_e   = '#D5F5E3', fedavg_bd='#27AE60',
    kd         = '#EAF2FF', kd_bd   = '#1565C0',
    aswa       = '#BBDEFB', aswa_bd = '#0D47A1',
    gfed       = '#E3F2FD', gfed_bd = '#1565C0',
    pfal       = '#E8D5F0', pfal_bd = '#6A1B9A',
    cs         = '#F1F8E9', cs_bd   = '#558B2F',
    ns3        = '#FFF3E0', ns3_bd  = '#E65100',
    kres       = '#EDE7F6', kres_bd = '#4A148C',
    arr_up     = '#1A5276',
    arr_dn     = '#145A32',
    arr_h      = '#5D6D7E',
    sync       = '#27AE60',
    txt_dark   = '#1B2631',
    txt_mid    = '#424949',
    txt_light  = '#717D7E',
)

# ── helpers ───────────────────────────────────────────────────────────────────
def box(x, y, w, h, fc, ec, lw=1.6, r=0.3, z=3):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f'round,pad=0,rounding_size={r}',
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z))

def txt(x, y, s, fs=10, bold=False, c='#1B2631',
        ha='center', va='center', z=6, italic=False):
    ax.text(x, y, s, fontsize=fs,
            fontweight='bold' if bold else 'normal',
            fontstyle='italic' if italic else 'normal',
            color=c, ha=ha, va=va, zorder=z,
            fontfamily='DejaVu Sans')

def arr(x0, y0, x1, y1, col, lw=2.0, style='->'):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle=style, color=col,
                                lw=lw, connectionstyle='arc3,rad=0'))

def hline(x0, x1, y, col='#82E0AA', lw=1.3, ls='--'):
    ax.plot([x0, x1], [y, y], ls=ls, color=col, lw=lw, zorder=2)

# ═════════════════════════════════════════════════════════════════════════════
#  COORDINATE MAP  (xlim=32, ylim=22)
#
#  y ranges (bottom → top):
#    0.10–0.70   legend strip
#    0.80–6.20   LAYER 1 band  (IoT devices)
#    6.20–7.20   arrow gap L1→L2
#    7.20–12.60  LAYER 2 band  (edge servers)
#   12.60–13.60  arrow gap L2→L3
#   13.60–19.00  LAYER 3 band  (cloud)
#   19.20–19.90  subtitle
#   20.10–20.90  title
#
#  x ranges:
#    0.30–22.00  main content
#   22.30–25.80  NS-3 / CloudSim / Key Results side panels
#   26.20–31.70  novelty column
#
#  6 cluster centres (Δ=3.5):  2.4, 5.9, 9.4, 12.9, 16.4, 19.9
#  half-width HW=1.55  →  box width BW=3.10
# ═════════════════════════════════════════════════════════════════════════════

CX = [2.4, 5.9, 9.4, 12.9, 16.4, 19.9]
HW = 1.55
BW = HW * 2

L1_Y0, L1_Y1 = 0.80,  6.20
L2_Y0, L2_Y1 = 7.20, 12.60
L3_Y0, L3_Y1 = 13.60, 19.00

DB_Y0, DB_Y1 = 1.20, 5.90    # device box
EB_Y0, EB_Y1 = 7.55, 12.30   # edge box

# ─────────────────────────────────────────────────────────────────────────────
#  TITLE
# ─────────────────────────────────────────────────────────────────────────────
txt(13.0, 20.65,
    'PHANTOM-FL — Proposed Hierarchical Federated Learning Framework',
    fs=26, bold=True, c='#1B2631')
txt(13.0, 20.10,
    'Privacy-Aware, Low-Latency Multimodal IoT System for Healthcare',
    fs=16, c='#5D6D7E', italic=True)

# ─────────────────────────────────────────────────────────────────────────────
#  LAYER BANDS
# ─────────────────────────────────────────────────────────────────────────────
box(0.30, L1_Y0, 21.70, L1_Y1 - L1_Y0, P['dev_band'],  P['dev_bd'],  lw=2.5, r=0.5, z=1)
box(0.30, L2_Y0, 21.70, L2_Y1 - L2_Y0, P['edge_band'], P['edge_bd'], lw=2.5, r=0.5, z=1)
box(0.30, L3_Y0, 21.70, L3_Y1 - L3_Y0, P['cloud_band'],P['cld_bd'],  lw=2.5, r=0.5, z=1)

# ─────────────────────────────────────────────────────────────────────────────
#  LAYER LABELS  (rotated left-rail)
# ─────────────────────────────────────────────────────────────────────────────
for (yc, lbl, col) in [
    ((L1_Y0+L1_Y1)/2, 'LAYER 1\nIoT / End Devices', '#795548'),
    ((L2_Y0+L2_Y1)/2, 'LAYER 2\nEdge Servers',       '#145A32'),
    ((L3_Y0+L3_Y1)/2, 'LAYER 3\nCloud Server',        '#1A5276'),
]:
    ax.text(0.55, yc, lbl, fontsize=10.5, fontweight='bold', color=col,
            ha='center', va='center', rotation=90, zorder=6,
            fontfamily='DejaVu Sans')

# ─────────────────────────────────────────────────────────────────────────────
#  LAYER 1 — DEVICE NODES
# ─────────────────────────────────────────────────────────────────────────────
dev_info = [
    ('ECG Patch', '(PTB-XL)', '1D-CNN + GRU',    P['dev_box'],  'Wearable / Sensor'),
    ('X-Ray Unit', '(CheXpert)', 'MobileNetV3',   P['xray_box'], 'Imaging Device'),
    ('ECG Patch', '(PTB-XL)', '1D-CNN + GRU',    P['dev_box'],  'Wearable / Sensor'),
    ('X-Ray Unit', '(CheXpert)', 'MobileNetV3',   P['xray_box'], 'Imaging Device'),
    ('ECG Patch', '(PTB-XL)', '1D-CNN + GRU',    P['dev_box'],  'Wearable / Sensor'),
    ('X-Ray Unit', '(CheXpert)', 'MobileNetV3',   P['xray_box'], 'Imaging Device'),
]

for i, (cx, (dn1, dn2, enc, dfc, note)) in enumerate(zip(CX, dev_info)):
    bx = cx - HW

    # outer device box
    box(bx, DB_Y0, BW, DB_Y1 - DB_Y0, dfc, P['dev_bd'], lw=1.8, r=0.25, z=3)

    # device name
    txt(cx, 5.65, dn1, fs=10.5, bold=True, c='#4A235A')
    txt(cx, 5.35, dn2, fs=9.5,  c='#6C3483')

    # separator
    hline(bx+0.15, cx+HW-0.15, 5.08, col='#BDBDBD', lw=0.9, ls='-')

    # encoder
    txt(cx, 4.80, 'Encoder', fs=9.0, bold=True, c=P['txt_dark'])
    txt(cx, 4.48, enc, fs=9.0, c='#1565C0')

    # separator
    hline(bx+0.15, cx+HW-0.15, 4.20, col='#BDBDBD', lw=0.9, ls='-')

    # DP-SGD badge  (y = 3.55–4.10)
    box(bx+0.20, 3.55, BW-0.40, 0.55, P['dp'], P['dp_bd'], lw=1.1, r=0.15, z=4)
    txt(cx, 3.83, 'DP-SGD   ε ≤ 1.0', fs=9.0, bold=True, c='#922B21', z=5)

    # Top-k badge  (y = 2.80–3.35)
    box(bx+0.20, 2.80, BW-0.40, 0.55, P['topk'], P['topk_bd'], lw=1.1, r=0.15, z=4)
    txt(cx, 3.08, 'Top-k  Sparse  k = 10%', fs=9.0, bold=True, c='#6A1B9A', z=5)

    # separator
    hline(bx+0.15, cx+HW-0.15, 2.58, col='#BDBDBD', lw=0.9, ls='-')

    # cluster label + note
    txt(cx, 2.25, f'Device Cluster {i+1}', fs=9.5, bold=True, c='#7B241C')
    txt(cx, 1.62, note, fs=8.0, c=P['txt_light'], italic=True)

    # uplink arrow
    arr(cx - 0.18, DB_Y1 + 0.05, cx - 0.18, EB_Y0 - 0.08, P['arr_up'], lw=1.8)
    txt(cx - 0.52, 6.70, 'grad ↑', fs=8.0, c=P['arr_up'], italic=True)

    # downlink arrow
    arr(cx + 0.18, EB_Y0 - 0.08, cx + 0.18, DB_Y1 + 0.05, P['arr_dn'], lw=1.8)
    txt(cx + 0.54, 6.70, 'W ↓', fs=8.0, c=P['arr_dn'], italic=True)

# ─────────────────────────────────────────────────────────────────────────────
#  LAYER 2 — EDGE SERVER NODES
# ─────────────────────────────────────────────────────────────────────────────
edge_labels = ['Hospital\nCluster A', 'Hospital\nCluster B', 'Hospital\nCluster C',
               'Hospital\nCluster D', 'Hospital\nCluster E', 'Hospital\nCluster F']

for i, (cx, elbl) in enumerate(zip(CX, edge_labels)):
    bx = cx - HW

    # outer edge box
    box(bx, EB_Y0, BW, EB_Y1 - EB_Y0, P['edge_band'], P['edge_bd'], lw=1.8, r=0.25, z=3)

    # hospital label
    txt(cx, 12.05, elbl, fs=10.0, bold=True, c='#145A32')

    # separator
    hline(bx+0.10, cx+HW-0.10, 11.75, col='#7DCEA0', lw=1.0, ls='-')

    # CMGA block  (10.90–11.65)
    box(bx+0.15, 10.90, BW-0.30, 0.75, P['cmga'], P['cmga_bd'], lw=1.2, r=0.18, z=4)
    txt(cx, 11.36, 'CMGA  Fusion', fs=9.5, bold=True, c='#0B5345', z=5)
    txt(cx, 11.06, 'Cross-Modal Gated Attn', fs=8.0, c='#196F3D', z=5)

    # Edge FedAvg block  (10.00–10.75)
    box(bx+0.15, 10.00, BW-0.30, 0.75, P['fedavg_e'], P['fedavg_bd'], lw=1.2, r=0.18, z=4)
    txt(cx, 10.46, 'Edge  FedAvg', fs=9.5, bold=True, c='#1D8348', z=5)
    txt(cx, 10.16, 'Local Aggregation', fs=8.0, c='#196F3D', z=5)

    # FedKD-E block  (9.10–9.85)
    box(bx+0.15, 9.10, BW-0.30, 0.75, P['kd'], P['kd_bd'], lw=1.2, r=0.18, z=4)
    txt(cx, 9.56, 'FedKD-E', fs=9.5, bold=True, c='#0D47A1', z=5)
    txt(cx, 9.26, 'Knowledge Distil → Device', fs=8.0, c='#1565C0', z=5)

    # separator
    hline(bx+0.10, cx+HW-0.10, 8.85, col='#7DCEA0', lw=1.0, ls='-')

    # micro notes
    txt(cx, 8.52, '4G/5G channel  (NS-3)', fs=8.0, c='#E65100', italic=True)
    txt(cx, 8.10, 'Privacy relay  ε ≤ 1', fs=8.0, c='#922B21', italic=True)

# dashed sync line between edge nodes
for i in range(len(CX) - 1):
    hline(CX[i] + HW + 0.05, CX[i+1] - HW - 0.05, 10.375,
          col=P['sync'], lw=1.5, ls='--')

# edge → cloud arrows
for cx in CX:
    arr(cx - 0.18, EB_Y1 + 0.05, cx - 0.18, 13.65, P['arr_up'], lw=1.8)
    txt(cx - 0.54, 13.08, 'agg ↑', fs=8.0, c=P['arr_up'], italic=True)
    arr(cx + 0.18, 13.65, cx + 0.18, EB_Y1 + 0.05, P['arr_dn'], lw=1.8)
    txt(cx + 0.56, 13.08, 'W ↓', fs=8.0, c=P['arr_dn'], italic=True)

# ─────────────────────────────────────────────────────────────────────────────
#  LAYER 3 — CLOUD SERVER
# ─────────────────────────────────────────────────────────────────────────────
CLD_X0, CLD_X1 = 1.00, 21.60
CLD_Y0, CLD_Y1 = 14.00, 18.60

# outer cloud box
box(CLD_X0, CLD_Y0, CLD_X1-CLD_X0, CLD_Y1-CLD_Y0,
    '#DDEEFF', '#1A5276', lw=2.2, r=0.45, z=3)

# cloud title
txt(11.30, 18.35,
    'CLOUD SERVER  —  Global Aggregation  +  Personalisation',
    fs=13, bold=True, c='#1A5276', z=6)

# ── ASWA block  x=1.30–6.20 ──
box(1.30, 14.40, 4.90, 3.40, P['aswa'], P['aswa_bd'], lw=1.5, r=0.3, z=4)
txt(3.75, 17.45, 'ASWA', fs=15, bold=True, c='#0D47A1', z=5)
txt(3.75, 17.00, 'Adaptive Self-Weighted', fs=10, c='#1A5276', z=5)
txt(3.75, 16.68, 'Aggregation', fs=10, c='#1A5276', z=5)
hline(1.50, 6.10, 16.42, col='#90CAF9', lw=0.9, ls='-')
txt(3.75, 16.08, 'Re-weights edge clusters by', fs=9.0, c='#1B4F72', z=5)
txt(3.75, 15.76, 'data quality + network state', fs=9.0, c='#1B4F72', z=5)
txt(3.75, 15.30, 'Prevents stragglers biasing', fs=8.5, c='#1B4F72', z=5, italic=True)
txt(3.75, 14.98, 'global model convergence', fs=8.5, c='#1B4F72', z=5, italic=True)
txt(3.75, 14.58, 'σ=1.1  |  C=1.0  |  δ=1e-5', fs=9.0, bold=True, c='#0D47A1', z=5)

# arrow ASWA → Global FedAvg
arr(6.22, 16.10, 6.88, 16.10, P['arr_h'], lw=2.0)

# ── Global FedAvg block  x=6.90–14.80 ──
box(6.90, 14.40, 7.90, 3.40, P['gfed'], P['gfed_bd'], lw=1.5, r=0.3, z=4)
txt(10.85, 17.45, 'Global  FedAvg', fs=15, bold=True, c='#1565C0', z=5)
hline(7.10, 14.60, 17.12, col='#90CAF9', lw=0.9, ls='-')
txt(10.85, 16.75, 'W_global = Σ ( nₖ / N ) · Wₖ', fs=11, bold=True, c='#154360', z=5)
hline(7.10, 14.60, 16.42, col='#90CAF9', lw=0.9, ls='-')
txt(10.85, 16.08, 'Privacy Budget  ε ≤ 1.0  (Rényi)', fs=9.5, c='#922B21', z=5)
txt(10.85, 15.72, 'Gradient indistinguishability', fs=9.0, c='#1B4F72', z=5, italic=True)
txt(10.85, 15.28, 'Comm. reduction :  76.4 %', fs=9.5, bold=True, c='#1E8449', z=5)
txt(10.85, 14.94, 'Energy saving   :  74.9 %', fs=9.5, bold=True, c='#1E8449', z=5)
txt(10.85, 14.58, 'Reliability     :  99.05 %', fs=9.5, bold=True, c='#0D47A1', z=5)

# arrow Global FedAvg → pFAL
arr(14.82, 16.10, 15.48, 16.10, P['arr_h'], lw=2.0)

# ── pFAL block  x=15.50–20.50 ──
box(15.50, 14.40, 5.00, 3.40, P['pfal'], P['pfal_bd'], lw=1.5, r=0.3, z=4)
txt(18.00, 17.45, 'pFAL', fs=15, bold=True, c='#6A1B9A', z=5)
txt(18.00, 17.00, 'Personalised FL Adapters', fs=10, c='#6A1B9A', z=5)
txt(18.00, 16.68, 'per hospital cluster', fs=9.0, c='#7B1FA2', z=5, italic=True)
hline(15.70, 20.30, 16.42, col='#CE93D8', lw=0.9, ls='-')
txt(18.00, 16.08, 'Non-IID personalisation', fs=9.0, c='#4A148C', z=5)
txt(18.00, 15.76, 'without label exposure', fs=9.0, c='#4A148C', z=5)
txt(18.00, 15.30, 'Adapts W_global to local', fs=8.5, c='#4A148C', z=5, italic=True)
txt(18.00, 14.98, 'patient distribution', fs=8.5, c='#4A148C', z=5, italic=True)
txt(18.00, 14.58, 'ε-DP preserved per cluster', fs=9.0, bold=True, c='#6A1B9A', z=5)

# CloudSim badge (right tab inside cloud)
box(20.70, 14.40, 0.75, 3.40, P['cs'], P['cs_bd'], lw=1.2, r=0.2, z=4)
ax.text(21.07, 16.10, 'Cloud\nSim\nPlus\nv8.5.6', fontsize=7.5,
        fontweight='bold', color='#558B2F',
        ha='center', va='center', zorder=5, fontfamily='DejaVu Sans')

# ─────────────────────────────────────────────────────────────────────────────
#  RIGHT SIDE PANELS  (x = 22.30–25.80)
# ─────────────────────────────────────────────────────────────────────────────

# ── NS-3 panel  (edge band height) ──
box(22.30, L2_Y0, 3.50, L2_Y1 - L2_Y0, P['ns3'], P['ns3_bd'], lw=1.8, r=0.4, z=3)
txt(24.05, 12.22, 'NS-3  Simulator', fs=11.5, bold=True, c='#E65100')
txt(24.05, 11.82, 'v 3.46.1', fs=10.0, c='#BF360C')
hline(22.50, 25.60, 11.55, col='#FFCC80', lw=1.0, ls='-')
txt(24.05, 11.18, 'Network Layer', fs=10.0, bold=True, c='#BF360C')
txt(24.05, 10.80, '4G / 5G  Channel', fs=9.5, c='#E65100')
txt(24.05, 10.42, 'Packet Loss + Fading', fs=9.5, c='#E65100')
txt(24.05, 10.04, 'Heterogeneous BW', fs=9.5, c='#E65100')
hline(22.50, 25.60, 9.75, col='#FFCC80', lw=1.0, ls='-')
txt(24.05, 9.35,  'Latency  <  100 ms', fs=10.5, bold=True, c='#C62828')
txt(24.05, 8.92,  'Delivery ratio', fs=9.5, c='#E65100')
txt(24.05, 8.52,  '> 99.05 %', fs=11.0, bold=True, c='#1E8449')
hline(22.50, 25.60, 8.22, col='#FFCC80', lw=1.0, ls='-')
txt(24.05, 7.85,  '20 IoT Devices', fs=9.5, c='#BF360C')
txt(24.05, 7.48,  '6 Edge Servers', fs=9.5, c='#BF360C')
txt(24.05, 7.25,  '1 Cloud Node',   fs=9.5, c='#BF360C')

# ── Key Results panel  (cloud band height) ──
box(22.30, L3_Y0, 3.50, L3_Y1 - L3_Y0, P['kres'], P['kres_bd'], lw=1.8, r=0.4, z=3)
txt(24.05, 18.65, 'Phase 4  Results', fs=11.5, bold=True, c='#4A148C')
hline(22.50, 25.60, 18.35, col='#CE93D8', lw=1.0, ls='-')
txt(24.05, 17.90, '▲ 76.4 %', fs=14, bold=True, c='#1E8449')
txt(24.05, 17.45, 'Comm. Reduction', fs=9.5, c='#145A32')
txt(24.05, 17.08, 'vs. centralised FL', fs=8.5, c='#145A32', italic=True)
hline(22.50, 25.60, 16.80, col='#CE93D8', lw=1.0, ls='-')
txt(24.05, 16.35, '▲ 74.9 %', fs=14, bold=True, c='#1E8449')
txt(24.05, 15.90, 'Energy Saving', fs=9.5, c='#145A32')
txt(24.05, 15.52, 'per FL round', fs=8.5, c='#145A32', italic=True)
hline(22.50, 25.60, 15.22, col='#CE93D8', lw=1.0, ls='-')
txt(24.05, 14.82, '99.05 %', fs=14, bold=True, c='#0D47A1')
txt(24.05, 14.40, 'Update Reliability', fs=9.5, c='#154360')
hline(22.50, 25.60, 14.10, col='#CE93D8', lw=1.0, ls='-')
txt(24.05, 13.85, 'ε = 0.8  ≤  1.0', fs=12, bold=True, c='#C62828')
txt(24.05, 13.68, 'Privacy Budget',   fs=9.0, c='#922B21')

# ── CloudSim panel  (device band height) ──
box(22.30, L1_Y0, 3.50, L1_Y1 - L1_Y0, P['cs'], P['cs_bd'], lw=1.8, r=0.4, z=3)
txt(24.05,  5.90, 'CloudSim Plus', fs=11.5, bold=True, c='#2E7D32')
txt(24.05,  5.50, 'v 8.5.6', fs=10.0, c='#388E3C')
hline(22.50, 25.60, 5.22, col='#A5D6A7', lw=1.0, ls='-')
txt(24.05,  4.85, 'Cloud Layer Sim', fs=10.0, bold=True, c='#2E7D32')
txt(24.05,  4.45, 'Task Scheduling', fs=9.5, c='#388E3C')
txt(24.05,  4.08, 'VM Provisioning', fs=9.5, c='#388E3C')
txt(24.05,  3.70, 'Energy Modelling', fs=9.5, c='#388E3C')
hline(22.50, 25.60, 3.42, col='#A5D6A7', lw=1.0, ls='-')
txt(24.05,  3.05, 'Validated against', fs=9.5, c='#2E7D32')
txt(24.05,  2.65, 'PTB-XL  +  CheXpert', fs=9.5, bold=True, c='#1B5E20')
hline(22.50, 25.60, 2.38, col='#A5D6A7', lw=1.0, ls='-')
txt(24.05,  2.00, 'Co-sim with NS-3', fs=9.5, c='#2E7D32')
txt(24.05,  1.60, 'time-step sync', fs=8.5, c='#388E3C', italic=True)
txt(24.05,  1.20, 'NVIDIA RTX A2000', fs=9.5, bold=True, c='#1B5E20')
txt(24.05,  0.88, '12 GB VRAM', fs=8.5, c='#2E7D32', italic=True)

# ─────────────────────────────────────────────────────────────────────────────
#  NOVELTY COLUMN  (x = 26.20–31.50)
# ─────────────────────────────────────────────────────────────────────────────
box(26.20, 0.80, 5.20, 18.20, '#F8F9FA', '#ADB5BD', lw=1.6, r=0.5, z=2)
txt(28.80, 18.62, 'Novel Contributions', fs=12.5, bold=True, c='#1B2631')
hline(26.40, 31.30, 18.35, col='#ADB5BD', lw=1.0, ls='-')

innovations = [
    ('#E3F2FD', '#1565C0', 'IP-1  CMGA',
     'Cross-Modal Gated Attention\nFuses ECG + X-ray at edge tier\nbefore cloud aggregation'),
    ('#FFF3E0', '#E65100', 'IP-2  SADP',
     'Self-Adaptive DP\nCalibrates ε per round\n≤ 2% accuracy loss at ε=1'),
    ('#E8F5E9', '#2E7D32', 'IP-3  ASWA',
     'Adaptive Self-Weighted Agg.\nRe-weights clusters by quality\n& network state dynamically'),
    ('#F3E5F5', '#6A1B9A', 'IP-4  FedKD-E',
     'Edge Knowledge Distillation\nCompresses global model\nfor <512 MB device inference'),
    ('#FCE4EC', '#880E4F', 'IP-5  pFAL',
     'Personalised FL Adapters\nNon-IID per cluster\nwithout label exposure'),
]

y_start = 17.90
for (bfc, bec, title, body) in innovations:
    box(26.40, y_start - 2.50, 4.80, 2.42, bfc, bec, lw=1.2, r=0.25, z=4)
    txt(28.80, y_start - 0.32, title, fs=10.5, bold=True, c=bec, z=5)
    hline(26.58, 31.02, y_start - 0.65, col=bec, lw=0.8, ls='-')
    lines = body.split('\n')
    for j, line in enumerate(lines):
        txt(28.80, y_start - 1.10 - j*0.46, line, fs=9.0, c='#2C3E50', z=5)
    y_start -= 3.18

# ─────────────────────────────────────────────────────────────────────────────
#  LEGEND STRIP  (y = 0.10–0.70)
# ─────────────────────────────────────────────────────────────────────────────
box(0.30, 0.10, 21.70, 0.62, '#ECF0F1', '#BDC3C7', lw=1.0, r=0.15, z=3)

arr(0.90, 0.41, 1.65, 0.41, P['arr_up'], lw=1.8)
txt(2.65, 0.41, 'Gradient Upload (encrypted)', fs=9.0, c=P['arr_up'])

arr(6.10, 0.41, 6.85, 0.41, P['arr_dn'], lw=1.8)
txt(7.95, 0.41, 'Model Download (distilled)', fs=9.0, c=P['arr_dn'])

hline(11.40, 12.20, 0.41, col=P['sync'], lw=1.5, ls='--')
txt(13.25, 0.41, 'Edge–Edge Sync', fs=9.0, c='#196F3D')

box(15.10, 0.22, 1.65, 0.38, P['dp'],   P['dp_bd'],   lw=0.9, r=0.08, z=4)
txt(15.93, 0.41, 'DP-SGD  ε ≤ 1', fs=8.5, c='#922B21', z=5)

box(17.60, 0.22, 1.65, 0.38, P['topk'], P['topk_bd'], lw=0.9, r=0.08, z=4)
txt(18.43, 0.41, 'Top-k  Sparse', fs=8.5, c='#6A1B9A', z=5)

# ─────────────────────────────────────────────────────────────────────────────
#  SAVE
# ─────────────────────────────────────────────────────────────────────────────
plt.tight_layout(pad=0.2)
out = '/home/deadserpent/HFL/Fig1_PHANTOM_FL_Framework.png'
plt.savefig(out, dpi=220, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f'Saved → {out}')
