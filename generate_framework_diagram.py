import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ── canvas ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(40, 26))
fig.patch.set_facecolor('#F0F4FA')
ax.set_facecolor('#F0F4FA')
ax.set_xlim(0, 32)
ax.set_ylim(0, 22)
ax.axis('off')

# ── palette ───────────────────────────────────────────────────────────────────
P = dict(
    dev_band  = '#FFFDE7', dev_bd  = '#F9A825',
    edge_band = '#E8F8F5', edge_bd = '#1E8449',
    cld_band  = '#EBF5FB', cld_bd  = '#1A5276',
    dev_box   = '#FFF8E1', xray_box= '#EDE7F6',
    dp        = '#FDECEA', dp_bd   = '#C0392B',
    topk      = '#F3E5F5', topk_bd = '#7B1FA2',
    cmga      = '#A9DFBF', cmga_bd = '#196F3D',
    eavg      = '#D5F5E3', eavg_bd = '#27AE60',
    kd        = '#EAF2FF', kd_bd   = '#1565C0',
    aswa      = '#BBDEFB', aswa_bd = '#0D47A1',
    gfed      = '#E3F2FD', gfed_bd = '#1565C0',
    pfal      = '#E8D5F0', pfal_bd = '#6A1B9A',
    ns3       = '#FFF3E0', ns3_bd  = '#E65100',
    kres      = '#EDE7F6', kres_bd = '#4A148C',
    cs        = '#F1F8E9', cs_bd   = '#558B2F',
    nov       = '#F8F9FA', nov_bd  = '#ADB5BD',
    arr_up    = '#1A5276',
    arr_dn    = '#145A32',
    arr_h     = '#5D6D7E',
)

# ── helpers ───────────────────────────────────────────────────────────────────
def box(x, y, w, h, fc, ec, lw=2.0, r=0.3, z=3):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle=f'round,pad=0,rounding_size={r}',
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z))

def t(x, y, s, fs=12, bold=False, c='#1B2631',
      ha='center', va='center', z=6, it=False):
    ax.text(x, y, s, fontsize=fs,
            fontweight='bold' if bold else 'normal',
            fontstyle='italic' if it else 'normal',
            color=c, ha=ha, va=va, zorder=z, fontfamily='DejaVu Sans')

def arr(x0, y0, x1, y1, col, lw=2.2):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(arrowstyle='->', color=col, lw=lw,
                        connectionstyle='arc3,rad=0'))

def hl(x0, x1, y, col, lw=1.2, ls='-'):
    ax.plot([x0, x1], [y, y], ls=ls, color=col, lw=lw, zorder=2)

# ── key coordinates ───────────────────────────────────────────────────────────
# Layer bands
L1 = (0.80, 6.10)   # y_bot, y_top  — IoT Devices
L2 = (7.10, 12.50)  # y_bot, y_top  — Edge Servers
L3 = (13.40, 19.00) # y_bot, y_top  — Cloud

# Device / Edge inner boxes
DB = (1.15, 5.85)   # device box  y_bot, y_top
EB = (7.45, 12.20)  # edge box    y_bot, y_top

# 6 cluster centres, evenly spaced
CX = [2.4, 5.9, 9.4, 12.9, 16.4, 19.9]
HW = 1.50            # half-width of each cluster box
BW = HW * 2          # = 3.00

# ─────────────────────────────────────────────────────────────────────────────
#  TITLE
# ─────────────────────────────────────────────────────────────────────────────
t(13.0, 20.75,
  'PHANTOM-FL — Proposed Hierarchical Federated Learning Framework',
  fs=22, bold=True, c='#1B2631')
t(13.0, 20.15,
  'Privacy-Aware, Low-Latency Multimodal IoT System for Healthcare ',
  fs=13, c='#5D6D7E', it=True)

# ─────────────────────────────────────────────────────────────────────────────
#  LAYER BANDS
# ─────────────────────────────────────────────────────────────────────────────
box(0.30, L1[0], 21.70, L1[1]-L1[0], P['dev_band'],  P['dev_bd'],  lw=2.8, r=0.5, z=1)
box(0.30, L2[0], 21.70, L2[1]-L2[0], P['edge_band'], P['edge_bd'], lw=2.8, r=0.5, z=1)
box(0.30, L3[0], 21.70, L3[1]-L3[0], P['cld_band'],  P['cld_bd'],  lw=2.8, r=0.5, z=1)

# rotated layer labels (left rail)
for yc, lbl, col in [
    ((L1[0]+L1[1])/2, 'LAYER 1\nIoT Devices',  '#795548'),
    ((L2[0]+L2[1])/2, 'LAYER 2\nEdge Servers',  '#145A32'),
    ((L3[0]+L3[1])/2, 'LAYER 3\nCloud Server',  '#1A5276'),
]:
    ax.text(0.58, yc, lbl, fontsize=13, fontweight='bold', color=col,
            ha='center', va='center', rotation=90, zorder=6,
            fontfamily='DejaVu Sans')

# ─────────────────────────────────────────────────────────────────────────────
#  LAYER 1 — IoT DEVICE NODES
#
#  Device box height = DB[1]-DB[0] = 4.70
#  y slots (bottom → top):
#    1.35  Cluster label
#    1.90–2.40  Top-k badge
#    2.60–3.10  DP-SGD badge
#    3.30  Separator
#    3.65  Encoder value
#    4.05  "Encoder" label
#    4.45  Separator
#    4.80  Dataset name
#    5.25  Device name
# ─────────────────────────────────────────────────────────────────────────────
dev_data = [
    ('ECG Patch',  'PTB-XL',   '1D-CNN + GRU', P['dev_box'],  'Wearable'),
    ('X-Ray Unit', 'CheXpert', 'MobileNetV3',  P['xray_box'], 'Imaging'),
] * 3   # repeat for 6 clusters

for i, (cx, (dname, dset, enc, dfc, dtype)) in enumerate(zip(CX, dev_data)):
    bx = cx - HW

    # outer box
    box(bx, DB[0], BW, DB[1]-DB[0], dfc, P['dev_bd'], lw=1.8, r=0.25, z=3)

    # device type + name (top)
    t(cx, 5.52, dname, fs=14, bold=True, c='#4A235A')
    t(cx, 5.20, dset,  fs=12, c='#6C3483')

    hl(bx+0.1, bx+BW-0.1, 4.92, '#BDBDBD', lw=0.9)

    # encoder
    t(cx, 4.60, 'Encoder',  fs=11, bold=True, c='#1B2631')
    t(cx, 4.28, enc,        fs=12, c='#1565C0', bold=True)

    hl(bx+0.1, bx+BW-0.1, 4.00, '#BDBDBD', lw=0.9)

    # DP-SGD badge
    box(bx+0.18, 3.45, BW-0.36, 0.48, P['dp'],   P['dp_bd'],   lw=1.1, r=0.15, z=4)
    t(cx, 3.69, 'DP-SGD  ε ≤ 1.0', fs=11, bold=True, c='#922B21', z=5)

    # Top-k badge
    box(bx+0.18, 2.82, BW-0.36, 0.48, P['topk'], P['topk_bd'], lw=1.1, r=0.15, z=4)
    t(cx, 3.06, 'Top-k  Sparse  k=10%', fs=11, bold=True, c='#6A1B9A', z=5)

    hl(bx+0.1, bx+BW-0.1, 2.60, '#BDBDBD', lw=0.9)

    # cluster label
    t(cx, 2.28, f'Cluster {i+1}  —  {dtype}', fs=12, bold=True, c='#7B241C')

    # arrows (device → edge)
    arr(cx-0.20, DB[1]+0.05, cx-0.20, EB[0]-0.08, P['arr_up'], lw=2.0)
    t(cx-0.55, 6.60, 'grad ↑', fs=10, c=P['arr_up'], it=True)

    arr(cx+0.20, EB[0]-0.08, cx+0.20, DB[1]+0.05, P['arr_dn'], lw=2.0)
    t(cx+0.57, 6.60, 'W ↓',   fs=10, c=P['arr_dn'], it=True)

# ─────────────────────────────────────────────────────────────────────────────
#  LAYER 2 — EDGE SERVER NODES
#
#  Edge box height = EB[1]-EB[0] = 4.75
#  y slots (bottom → top):
#    7.70  bottom margin
#    8.05–8.70  FedKD-E block
#    8.90–9.55  Edge FedAvg block
#    9.75–10.40 CMGA Fusion block
#    10.60 separator
#    10.95 Hospital label
# ─────────────────────────────────────────────────────────────────────────────
eclbls = ['Hospital A', 'Hospital B', 'Hospital C',
          'Hospital D', 'Hospital E', 'Hospital F']

for i, (cx, elbl) in enumerate(zip(CX, eclbls)):
    bx = cx - HW

    # outer box
    box(bx, EB[0], BW, EB[1]-EB[0], P['edge_band'], P['edge_bd'], lw=1.8, r=0.25, z=3)

    # hospital label
    t(cx, 11.95, elbl, fs=13, bold=True, c='#145A32')
    hl(bx+0.1, bx+BW-0.1, 11.65, '#7DCEA0', lw=1.0)

    # CMGA block
    box(bx+0.12, 10.55, BW-0.24, 0.95, P['cmga'], P['cmga_bd'], lw=1.2, r=0.2, z=4)
    t(cx, 11.18, 'CMGA',         fs=13, bold=True, c='#0B5345', z=5)
    t(cx, 10.82, 'Cross-Modal Fusion', fs=10, c='#196F3D', z=5)

    # Edge FedAvg block
    box(bx+0.12, 9.42, BW-0.24, 0.95, P['eavg'], P['eavg_bd'], lw=1.2, r=0.2, z=4)
    t(cx, 10.04, 'Edge FedAvg',   fs=13, bold=True, c='#1D8348', z=5)
    t(cx, 9.70,  'Local Aggregation', fs=10, c='#196F3D', z=5)

    # FedKD-E block
    box(bx+0.12, 8.28, BW-0.24, 0.95, P['kd'], P['kd_bd'], lw=1.2, r=0.2, z=4)
    t(cx, 8.90, 'FedKD-E',         fs=13, bold=True, c='#0D47A1', z=5)
    t(cx, 8.56, 'Knowledge Distil', fs=10, c='#1565C0', z=5)

    hl(bx+0.1, bx+BW-0.1, 8.05, '#7DCEA0', lw=1.0)
    t(cx, 7.78, '4G/5G · NS-3', fs=10, c='#E65100', it=True)

# dashed sync line across all edge nodes
hl(CX[0]-HW+0.15, CX[-1]+HW-0.15, 9.94, P['arr_dn'], lw=1.5, ls='--')

# edge → cloud arrows
for cx in CX:
    arr(cx-0.20, EB[1]+0.05, cx-0.20, 13.45, P['arr_up'], lw=2.0)
    t(cx-0.55, 12.98, 'agg ↑', fs=10, c=P['arr_up'], it=True)
    arr(cx+0.20, 13.45, cx+0.20, EB[1]+0.05, P['arr_dn'], lw=2.0)
    t(cx+0.57, 12.98, 'W ↓',   fs=10, c=P['arr_dn'], it=True)

# ─────────────────────────────────────────────────────────────────────────────
#  LAYER 3 — CLOUD SERVER
#
#  Main cloud box: x=1.0–21.6, y=13.70–18.70
#  Three sub-blocks at y=14.10–18.25
#    ASWA      x=1.20–6.50   (w=5.30)
#    Global FedAvg x=7.00–15.00  (w=8.00)
#    pFAL      x=15.60–21.00 (w=5.40)
# ─────────────────────────────────────────────────────────────────────────────
box(1.00, 13.70, 20.60, 5.00, '#DDEEFF', '#1A5276', lw=2.4, r=0.45, z=3)
t(11.30, 18.48, 'CLOUD SERVER  —  Global Aggregation  +  Personalisation',
  fs=16, bold=True, c='#1A5276', z=6)

# ── ASWA ──
box(1.20, 14.10, 5.30, 4.00, P['aswa'], P['aswa_bd'], lw=1.6, r=0.3, z=4)
t(3.85, 17.72, 'ASWA',                  fs=20, bold=True, c='#0D47A1', z=5)
t(3.85, 17.20, 'Adaptive Self-Weighted', fs=13, c='#1A5276', z=5)
t(3.85, 16.82, 'Aggregation',            fs=13, c='#1A5276', z=5)
hl(1.38, 6.32, 16.52, '#90CAF9', lw=0.9)
t(3.85, 16.10, 'Re-weights clusters',    fs=12, c='#1B4F72', z=5)
t(3.85, 15.72, 'by data quality',        fs=12, c='#1B4F72', z=5)
t(3.85, 15.22, 'σ=1.1 · C=1.0 · δ=1e-5', fs=11, bold=True, c='#0D47A1', z=5)
t(3.85, 14.58, 'ε ≤ 1.0',                fs=14, bold=True, c='#C62828', z=5)

# arrow ASWA → FedAvg
arr(6.52, 16.10, 6.98, 16.10, P['arr_h'], lw=2.2)

# ── Global FedAvg ──
box(7.00, 14.10, 8.00, 4.00, P['gfed'], P['gfed_bd'], lw=1.6, r=0.3, z=4)
t(11.00, 17.72, 'Global  FedAvg',          fs=20, bold=True, c='#1565C0', z=5)
hl(7.18, 14.82, 17.40, '#90CAF9', lw=0.9)
t(11.00, 17.00, 'W_global = Σ (nₖ/N) · Wₖ', fs=13, bold=True, c='#154360', z=5)
hl(7.18, 14.82, 16.65, '#90CAF9', lw=0.9)
t(11.00, 16.22, '▲ Comm. Reduction :  76.4 %', fs=13, bold=True, c='#1E8449', z=5)
t(11.00, 15.78, '▲ Energy Saving   :  74.9 %', fs=13, bold=True, c='#1E8449', z=5)
t(11.00, 15.34, '   Reliability    :  99.05 %', fs=13, bold=True, c='#0D47A1', z=5)
t(11.00, 14.70, 'Privacy:  ε = 0.8  ≤  1.0',  fs=13, bold=True, c='#C62828', z=5)

# arrow FedAvg → pFAL
arr(15.02, 16.10, 15.58, 16.10, P['arr_h'], lw=2.2)

# ── pFAL ──
box(15.60, 14.10, 5.40, 4.00, P['pfal'], P['pfal_bd'], lw=1.6, r=0.3, z=4)
t(18.30, 17.72, 'pFAL',                     fs=20, bold=True, c='#6A1B9A', z=5)
t(18.30, 17.20, 'Personalised FL Adapters',  fs=13, c='#6A1B9A', z=5)
t(18.30, 16.82, 'per hospital cluster',       fs=12, c='#7B1FA2', z=5, it=True)
hl(15.78, 20.82, 16.52, '#CE93D8', lw=0.9)
t(18.30, 16.10, 'Non-IID personalisation',   fs=12, c='#4A148C', z=5)
t(18.30, 15.72, 'without label exposure',    fs=12, c='#4A148C', z=5)
t(18.30, 15.22, 'Adapts W_global to',        fs=12, c='#4A148C', z=5)
t(18.30, 14.84, 'local patient data',        fs=12, c='#4A148C', z=5)
t(18.30, 14.40, 'ε-DP  preserved',           fs=13, bold=True, c='#6A1B9A', z=5)

# ─────────────────────────────────────────────────────────────────────────────
#  RIGHT SIDE PANELS  (x=22.20–25.80)
# ─────────────────────────────────────────────────────────────────────────────

# ── NS-3  (aligned with edge band) ──
box(22.20, L2[0], 3.60, L2[1]-L2[0], P['ns3'], P['ns3_bd'], lw=2.0, r=0.4, z=3)
t(24.00, 12.15, 'NS-3',          fs=16, bold=True, c='#E65100')
t(24.00, 11.68, 'v 3.46.1',      fs=12, c='#BF360C')
hl(22.40, 25.60, 11.38, '#FFCC80', lw=1.0)
t(24.00, 10.95, 'Network Sim',   fs=13, bold=True, c='#BF360C')
t(24.00, 10.50, '4G / 5G',       fs=12, c='#E65100')
t(24.00, 10.08, 'Packet Fading', fs=12, c='#E65100')
hl(22.40, 25.60, 9.75, '#FFCC80', lw=1.0)
t(24.00, 9.28,  '< 100 ms',      fs=16, bold=True, c='#C62828')
t(24.00, 8.80,  'Latency',        fs=12, c='#E65100')
hl(22.40, 25.60, 8.48, '#FFCC80', lw=1.0)
t(24.00, 8.05, '20 Devices',     fs=12, c='#BF360C', bold=True)
t(24.00, 7.62, '6 Edge Servers', fs=12, c='#BF360C', bold=True)
t(24.00, 7.28, '1 Cloud Node',   fs=12, c='#BF360C', bold=True)

# ── Key Results  (aligned with cloud band) ──
box(22.20, L3[0], 3.60, L3[1]-L3[0], P['kres'], P['kres_bd'], lw=2.0, r=0.4, z=3)
t(24.00, 18.62, 'Results',        fs=14, bold=True, c='#4A148C')
hl(22.40, 25.60, 17.88, '#CE93D8', lw=1.0)
t(24.00, 17.38, '76.4 %',         fs=20, bold=True, c='#1E8449')
t(24.00, 16.88, 'Comm. Saved',    fs=11, c='#145A32')
hl(22.40, 25.60, 16.55, '#CE93D8', lw=1.0)
t(24.00, 16.05, '74.9 %',         fs=20, bold=True, c='#1E8449')
t(24.00, 15.55, 'Energy Saved',   fs=11, c='#145A32')
hl(22.40, 25.60, 15.22, '#CE93D8', lw=1.0)
t(24.00, 14.72, '99.05 %',        fs=20, bold=True, c='#0D47A1')
t(24.00, 14.22, 'Reliability',    fs=11, c='#154360')
hl(22.40, 25.60, 13.90, '#CE93D8', lw=1.0)
t(24.00, 13.66, 'ε = 0.8',        fs=18, bold=True, c='#C62828')

# ── CloudSim  (aligned with device band) ──
box(22.20, L1[0], 3.60, L1[1]-L1[0], P['cs'], P['cs_bd'], lw=2.0, r=0.4, z=3)
t(24.00, 5.85,  'CloudSim',       fs=14, bold=True, c='#2E7D32')
t(24.00, 5.38,  'Plus v8.5.6',    fs=12, c='#388E3C')
hl(22.40, 25.60, 5.05, '#A5D6A7', lw=1.0)
t(24.00, 4.60,  'Cloud Sim',      fs=13, bold=True, c='#2E7D32')
t(24.00, 4.15,  'Task Schedule',  fs=12, c='#388E3C')
t(24.00, 3.72,  'Energy Model',   fs=12, c='#388E3C')
hl(22.40, 25.60, 3.42, '#A5D6A7', lw=1.0)
t(24.00, 3.00,  'PTB-XL',         fs=13, bold=True, c='#1B5E20')
t(24.00, 2.58,  'CheXpert',       fs=13, bold=True, c='#1B5E20')
hl(22.40, 25.60, 2.28, '#A5D6A7', lw=1.0)
t(24.00, 1.82,  'RTX A2000',      fs=13, bold=True, c='#2E7D32')
t(24.00, 1.38,  '12 GB VRAM',     fs=12, c='#388E3C')

# ─────────────────────────────────────────────────────────────────────────────
#  NOVELTY COLUMN  (x=26.10–31.60)
# ─────────────────────────────────────────────────────────────────────────────
box(26.10, 0.80, 5.60, 18.20, P['nov'], P['nov_bd'], lw=1.8, r=0.5, z=2)
t(28.90, 19.38, 'Innovations', fs=16, bold=True, c='#1B2631')
hl(26.30, 31.60, 19.08, '#ADB5BD', lw=1.2)

cards = [
    ('#E3F2FD', '#0D47A1',  'IP-1',  'CMGA',
     'Cross-Modal\nGated Attention'),
    ('#FFF3E0', '#E65100',  'IP-2',  'SADP',
     'Self-Adaptive\nDiff. Privacy'),
    ('#E8F5E9', '#2E7D32',  'IP-3',  'ASWA',
     'Adaptive Self-\nWeighted Aggr.'),
    ('#F3E5F5', '#6A1B9A',  'IP-4',  'FedKD-E',
     'Edge Knowledge\nDistillation'),
    ('#FCE4EC', '#880E4F',  'IP-5',  'pFAL',
     'Personalised\nFL Adapters'),
]

cy = 18.60
gap = 3.52
for fc, ec, ip, acr, desc in cards:
    cy -= gap
    box(26.30, cy, 5.20, gap-0.25, fc, ec, lw=1.4, r=0.28, z=4)
    t(28.90, cy+gap-0.62, f'{ip} — {acr}',  fs=14, bold=True, c=ec, z=5)
    hl(26.48, 31.32, cy+gap-0.92, ec, lw=0.9)
    lines = desc.split('\n')
    for j, ln in enumerate(lines):
        t(28.90, cy+gap-1.42-j*0.50, ln, fs=12, c='#2C3E50', z=5)

# ─────────────────────────────────────────────────────────────────────────────
#  LEGEND STRIP  (y=0.08–0.70)
# ─────────────────────────────────────────────────────────────────────────────
box(0.30, 0.08, 21.70, 0.66, '#ECF0F1', '#BDC3C7', lw=1.1, r=0.15, z=3)

arr(0.85, 0.41, 1.65, 0.41, P['arr_up'], lw=2.0)
t(2.90, 0.41, 'Gradient Upload (encrypted)', fs=11, c=P['arr_up'])

arr(6.20, 0.41, 7.00, 0.41, P['arr_dn'], lw=2.0)
t(8.30, 0.41, 'Model Download (distilled)', fs=11, c=P['arr_dn'])

hl(11.50, 12.40, 0.41, P['arr_dn'], lw=1.8, ls='--')
t(13.60, 0.41, 'Edge–Edge Sync', fs=11, c='#196F3D')

box(15.20, 0.20, 2.00, 0.40, P['dp'],   P['dp_bd'],   lw=1.0, r=0.08, z=4)
t(16.20, 0.41, 'DP-SGD ε≤1',   fs=10.5, c='#922B21', z=5)

box(18.10, 0.20, 2.00, 0.40, P['topk'], P['topk_bd'], lw=1.0, r=0.08, z=4)
t(19.10, 0.41, 'Top-k Sparse', fs=10.5, c='#6A1B9A', z=5)

# ─────────────────────────────────────────────────────────────────────────────
#  SAVE
# ─────────────────────────────────────────────────────────────────────────────
plt.tight_layout(pad=0.2)
out = '/home/deadserpent/HFL/Fig1_PHANTOM_FL_Framework.png'
plt.savefig(out, dpi=220, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f'Saved → {out}')
