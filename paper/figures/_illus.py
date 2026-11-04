"""_illus.py — small 2.5-D vector illustrations for the schematic figures.

Objects are drawn in the same oblique (cabinet) projection as Fig. 1, with
three-tone face shading, so the workflow and the overview share one
illustration style. Everything is matplotlib patches (pure vector, no raster,
no icon font). Coordinates: data units of a full-bleed axes in inches; each
object is placed by its centre (x, y) and sized by s inches.
"""
import numpy as np
from matplotlib.patches import Polygon, Ellipse, Rectangle, Circle, Wedge, FancyBboxPatch

KX, KY = 0.42, 0.30                    # oblique depth direction (as Fig. 1)
EDGE = "#475569"
SLATE3 = ("#A9B8C9", "#6E85A0", "#556B85")          # top, front, right
STONE3 = ("#FFFFFF", "#E9ECEF", "#D3D8DE")
KRAFT3 = ("#E8CFA6", "#D4B07A", "#BC955E")
PRIV = "#D55E00"


def _P(x0, y0, s):
    return lambda u, v, w: (x0 + s * (u + KX * v), y0 + s * (KY * v + w))


def _poly(ax, pts, fc, ec=EDGE, lw=0.4, zo=5):
    ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=zo,
                         joinstyle="round"))


def block(ax, P, u, v, w, du, dv, dw, faces, ec=EDGE, lw=0.4, zo=5):
    top, front, right = faces
    _poly(ax, [P(u + du, v, w), P(u + du, v + dv, w), P(u + du, v + dv, w + dw),
               P(u + du, v, w + dw)], right, ec, lw, zo)
    _poly(ax, [P(u, v, w), P(u + du, v, w), P(u + du, v, w + dw), P(u, v, w + dw)],
          front, ec, lw, zo)
    _poly(ax, [P(u, v, w + dw), P(u + du, v, w + dw), P(u + du, v + dv, w + dw),
               P(u, v + dv, w + dw)], top, ec, lw, zo + 0.01)


def shadow(ax, x, y, w, h, zo=4):
    ax.add_patch(Ellipse((x, y), w, h, fc="#0F172A", alpha=0.10, ec="none", zorder=zo))


# ── objects ────────────────────────────────────────────────────────────
def database(ax, x, y, s, color="#6E85A0", zo=5):
    """Shaded cylinder of three platters; `color` tints the body."""
    from matplotlib.colors import to_rgb
    c = np.array(to_rgb(color))
    light = tuple(np.clip(c + (1 - c) * 0.55, 0, 1))
    dark = tuple(np.clip(c * 0.72, 0, 1))
    w, eh, h = 0.62 * s, 0.20 * s, 0.70 * s
    shadow(ax, x + 0.04 * s, y - h / 2 - 0.02 * s, w * 1.15, eh * 0.9, zo - 1)
    n = 14                                                    # body: graded strips
    for i in range(n):
        f = i / (n - 1)
        col = tuple(np.clip(np.array(light) * (1 - f) + np.array(dark) * f, 0, 1))
        ax.add_patch(Rectangle((x - w / 2 + i * w / n, y - h / 2), w / n * 1.02, h,
                               fc=col, ec="none", zorder=zo))
    ax.add_patch(Ellipse((x, y - h / 2), w, eh, fc=tuple(dark), ec=EDGE, lw=0.4,
                         zorder=zo - 0.1))
    for k in (1, 2):                                          # platter seams
        yy = y - h / 2 + k * h / 3
        t = np.linspace(np.pi, 2 * np.pi, 40)
        ax.plot(x + w / 2 * np.cos(t), yy + eh / 2 * np.sin(t), color="white", lw=0.7,
                alpha=0.85, zorder=zo + 0.1)
    ax.plot([x - w / 2] * 2, [y - h / 2, y + h / 2], color=EDGE, lw=0.4, zorder=zo + 0.1)
    ax.plot([x + w / 2] * 2, [y - h / 2, y + h / 2], color=EDGE, lw=0.4, zorder=zo + 0.1)
    ax.add_patch(Ellipse((x, y + h / 2), w, eh, fc=light, ec=EDGE, lw=0.4,
                         zorder=zo + 0.2))
    ax.add_patch(Ellipse((x - w * 0.12, y + h / 2 + eh * 0.08), w * 0.45, eh * 0.35,
                         fc="white", alpha=0.6, ec="none", zorder=zo + 0.3))


def hospital(ax, x, y, s, highlight=False, zo=5):
    P = _P(x - 0.48 * s, y - 0.50 * s, s)
    shadow(ax, x + 0.10 * s, y - 0.50 * s, 1.15 * s, 0.16 * s, zo - 1)
    block(ax, P, 0, 0, 0, 0.80, 0.55, 0.85, STONE3,
          ec=PRIV if highlight else EDGE, lw=0.8 if highlight else 0.4, zo=zo)
    for i in range(3):
        for j in range(2):
            u0, w0 = 0.09 + i * 0.235, 0.14 + j * 0.27
            _poly(ax, [P(u0, 0, w0), P(u0 + 0.14, 0, w0), P(u0 + 0.14, 0, w0 + 0.15),
                       P(u0, 0, w0 + 0.15)], "#9EC2E3", "none", 0, zo + 0.05)
    _poly(ax, [P(0.32, 0, 0), P(0.48, 0, 0), P(0.48, 0, 0.12), P(0.32, 0, 0.12)],
          "#64748B", "none", 0, zo + 0.05)
    cx, cz = 0.40, 0.70
    for (a, b) in ((0.11, 0.04), (0.04, 0.11)):
        _poly(ax, [P(cx - a, 0, cz - b), P(cx + a, 0, cz - b), P(cx + a, 0, cz + b),
                   P(cx - a, 0, cz + b)], "#D64545", "none", 0, zo + 0.06)


def rack(ax, x, y, s, zo=5):
    P = _P(x - 0.30 * s, y - 0.52 * s, s)
    shadow(ax, x + 0.08 * s, y - 0.52 * s, 0.90 * s, 0.14 * s, zo - 1)
    block(ax, P, 0, 0, 0, 0.55, 0.45, 1.0, SLATE3, ec="#334155", zo=zo)
    for k in range(3):
        h = 0.20 + k * 0.30
        a, b = P(0.06, 0, h), P(0.32, 0, h)
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#E2E8F0", lw=0.8, zorder=zo + 0.1)
        for d, c in ((0.40, "#6EE7A0"), (0.47, "#FBBF24")):
            px, py = P(d, 0, h)
            ax.add_patch(Circle((px, py), 0.022 * s, fc=c, ec="none", zorder=zo + 0.2))


def cloud(ax, x, y, s, zo=5):
    """Puffy cloud: soft drop shadow, base tone, lower shade band, highlights."""
    lumps = ((-0.38, -0.04, 0.42), (-0.12, 0.10, 0.56), (0.20, 0.06, 0.48),
             (0.42, -0.06, 0.34), (0.04, -0.02, 0.44))
    shadow(ax, x + 0.03 * s, y - 0.26 * s, 1.15 * s, 0.14 * s, zo - 1)
    for col, dy, k, z in (("#7F98B5", -0.045, 1.0, zo), ("#B9CAE0", 0.0, 1.0, zo + 0.1),
                          ("#E4ECF6", 0.05, 0.70, zo + 0.2)):
        for dx, ly, d in lumps:
            ax.add_patch(Circle((x + dx * s, y + (ly + dy) * s), d * s / 2 * k, fc=col,
                                ec="none", zorder=z))
        ax.add_patch(FancyBboxPatch((x - 0.52 * s, y + (-0.22 + dy) * s), 1.0 * s,
                                    0.24 * s * k, fc=col, ec="none", zorder=z,
                                    boxstyle=f"round,pad=0,rounding_size={0.11 * s}"))


def parcel(ax, x, y, s, zo=5):
    """Compressed package: kraft box with tape."""
    P = _P(x - 0.42 * s, y - 0.36 * s, s)
    shadow(ax, x + 0.08 * s, y - 0.36 * s, 1.0 * s, 0.14 * s, zo - 1)
    block(ax, P, 0, 0, 0, 0.72, 0.55, 0.55, KRAFT3, ec="#8A6A3C", zo=zo)
    _poly(ax, [P(0.31, 0, 0.55), P(0.41, 0, 0.55), P(0.41, 0.55, 0.55),
               P(0.31, 0.55, 0.55)], "#F3E3C6", "none", 0, zo + 0.05)
    _poly(ax, [P(0.31, 0, 0.30), P(0.41, 0, 0.30), P(0.41, 0, 0.55), P(0.31, 0, 0.55)],
          "#F3E3C6", "none", 0, zo + 0.05)


def bars(ax, x, y, s, zo=5):
    """Small 3-D bar chart on a base plate."""
    P = _P(x - 0.48 * s, y - 0.42 * s, s)
    shadow(ax, x + 0.06 * s, y - 0.42 * s, 1.1 * s, 0.12 * s, zo - 1)
    block(ax, P, 0, 0, 0, 0.96, 0.40, 0.05, STONE3, zo=zo)
    for u, h, faces in ((0.10, 0.45, SLATE3), (0.40, 0.75, SLATE3),
                        (0.70, 0.30, ("#F7B98A", "#E07B39", "#C4651F"))):
        block(ax, P, u, 0.10, 0.05, 0.18, 0.18, h, faces, zo=zo + 0.1 + u)


def records(ax, x, y, s, zo=5):
    """Stack of record cards (windows of one individual)."""
    P = _P(x - 0.42 * s, y - 0.40 * s, s)
    shadow(ax, x + 0.06 * s, y - 0.40 * s, 1.0 * s, 0.13 * s, zo - 1)
    for k in range(5):
        block(ax, P, 0.02 * k, 0, 0.16 * k, 0.70, 0.50, 0.10, STONE3, zo=zo + 0.1 * k)
        a, b = P(0.10 + 0.02 * k, 0, 0.16 * k + 0.05), P(0.45 + 0.02 * k, 0, 0.16 * k + 0.05)
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#94A3B8", lw=0.6, zorder=zo + 0.1 * k + 0.05)


def magnifier(ax, x, y, s, zo=5):
    """Magnifying glass over a record: the audit."""
    shadow(ax, x + 0.05 * s, y - 0.42 * s, 0.9 * s, 0.12 * s, zo - 1)
    ax.add_patch(FancyBboxPatch((x - 0.40 * s, y - 0.38 * s), 0.52 * s, 0.66 * s,
                                fc="white", ec=EDGE, lw=0.4, zorder=zo,
                                boxstyle=f"round,pad=0,rounding_size={0.04 * s}"))
    for k in range(4):
        ax.plot([x - 0.32 * s, x + 0.02 * s], [y + (0.16 - 0.12 * k) * s] * 2,
                color="#94A3B8", lw=0.6, zorder=zo + 0.1)
    hx, hy = x + 0.10 * s, y + 0.02 * s
    t = np.radians(-45)
    L, Wd = 0.42 * s, 0.09 * s
    c, sn = np.cos(t), np.sin(t)
    base = np.array((hx + 0.20 * s * c, hy + 0.20 * s * sn))
    perp = np.array((-sn, c)) * Wd / 2
    along = np.array((c, sn)) * L
    _poly(ax, [base + perp, base + along + perp, base + along - perp, base - perp],
          "#334155", "#1E293B", 0.4, zo + 0.3)
    ax.add_patch(Circle((hx, hy), 0.24 * s, fc="#DCEBFA", alpha=0.85, ec="#334155",
                        lw=1.6 * s / 0.3 * 0.5 + 0.6, zorder=zo + 0.4))
    ax.add_patch(Wedge((hx, hy), 0.17 * s, 110, 170, width=0.035 * s, fc="white",
                       ec="none", zorder=zo + 0.5))
    ax.add_patch(Circle((hx + 0.02 * s, hy - 0.01 * s), 0.07 * s, fc=PRIV, alpha=0.85,
                        ec="none", zorder=zo + 0.45))


def padlock(ax, x, y, s, color="#334155", zo=5):
    ax.add_patch(Wedge((x, y + 0.08 * s), 0.20 * s, 0, 180, width=0.07 * s, fc="#94A3B8",
                       ec=color, lw=0.4, zorder=zo))
    ax.add_patch(FancyBboxPatch((x - 0.30 * s, y - 0.32 * s), 0.60 * s, 0.42 * s,
                                fc="#F59E0B", ec="#92400E", lw=0.4, zorder=zo + 0.1,
                                boxstyle=f"round,pad=0,rounding_size={0.06 * s}"))
    ax.add_patch(Rectangle((x - 0.30 * s, y - 0.32 * s), 0.60 * s, 0.10 * s,
                           fc="#D97706", ec="none", zorder=zo + 0.15))
    ax.add_patch(Circle((x, y - 0.08 * s), 0.05 * s, fc="#78350F", ec="none",
                        zorder=zo + 0.2))


def funnel(ax, x, y, s, zo=5):
    """Selection funnel with a highlighted pick."""
    shadow(ax, x + 0.04 * s, y - 0.45 * s, 0.7 * s, 0.10 * s, zo - 1)
    ax.add_patch(Ellipse((x, y + 0.30 * s), 0.80 * s, 0.18 * s, fc="#CBD5E1", ec=EDGE,
                         lw=0.4, zorder=zo + 0.2))
    _poly(ax, [(x - 0.40 * s, y + 0.30 * s), (x + 0.40 * s, y + 0.30 * s),
               (x + 0.08 * s, y - 0.10 * s), (x + 0.08 * s, y - 0.38 * s),
               (x - 0.08 * s, y - 0.38 * s), (x - 0.08 * s, y - 0.10 * s)],
          "#8EA3B8", EDGE, 0.4, zo)
    _poly(ax, [(x, y + 0.30 * s), (x + 0.40 * s, y + 0.30 * s),
               (x + 0.08 * s, y - 0.10 * s), (x + 0.08 * s, y - 0.38 * s),
               (x, y - 0.38 * s)], "#6E85A0", "none", 0, zo + 0.05)
    for dx, col in ((-0.18, "#E2E8F0"), (0.0, PRIV), (0.17, "#E2E8F0")):
        ax.add_patch(Circle((x + dx * s, y + 0.36 * s), 0.07 * s, fc=col, ec=EDGE,
                            lw=0.3, zorder=zo + 0.3))


def bed_patient(ax, x, y, s, zo=5):
    """Patient lying in a hospital bed (side-on oblique)."""
    P = _P(x - 0.55 * s, y - 0.30 * s, s)
    shadow(ax, x + 0.06 * s, y - 0.30 * s, 1.30 * s, 0.14 * s, zo - 1)
    for u in (0.04, 0.98):                                     # legs
        block(ax, P, u, 0.05, 0.0, 0.06, 0.06, 0.20, SLATE3, lw=0.3, zo=zo)
    block(ax, P, 0.0, 0.0, 0.20, 1.10, 0.45, 0.08, SLATE3, lw=0.3, zo=zo + 0.1)  # frame
    block(ax, P, 0.02, 0.02, 0.28, 1.06, 0.41, 0.10, ("#FFFFFF", "#EEF2F7", "#D9E2EC"),
          lw=0.3, zo=zo + 0.2)                                  # mattress
    block(ax, P, 0.0, 0.0, 0.20, 0.07, 0.45, 0.40, SLATE3, lw=0.3, zo=zo + 0.15)  # headboard
    block(ax, P, 0.08, 0.08, 0.38, 0.22, 0.28, 0.07, ("#FFFFFF", "#F1F5F9", "#E2E8F0"),
          lw=0.3, zo=zo + 0.3)                                  # pillow
    hx, hy = P(0.20, 0.22, 0.56)
    ax.add_patch(Circle((hx, hy), 0.085 * s, fc="#F2C9A0", ec="#9A6B45", lw=0.3,
                        zorder=zo + 0.45))
    ax.add_patch(Wedge((hx, hy + 0.01 * s), 0.088 * s, 20, 200, fc="#4B3A2E", ec="none",
                       zorder=zo + 0.46))                        # hair
    block(ax, P, 0.30, 0.03, 0.38, 0.74, 0.39, 0.11, ("#9CC3E6", "#6FA3D2", "#5A8DBB"),
          lw=0.3, zo=zo + 0.4)                                  # blanket


def monitor(ax, x, y, s, zo=5):
    """Bedside vital-signs monitor with an ECG trace."""
    P = _P(x - 0.42 * s, y - 0.40 * s, s)
    shadow(ax, x + 0.05 * s, y - 0.40 * s, 0.9 * s, 0.12 * s, zo - 1)
    block(ax, P, 0.32, 0.10, 0.0, 0.18, 0.12, 0.25, SLATE3, lw=0.3, zo=zo)   # stand
    block(ax, P, 0.0, 0.0, 0.25, 0.82, 0.14, 0.60, ("#94A3B8", "#334155", "#1E293B"),
          ec="#0F172A", lw=0.4, zo=zo + 0.1)
    _poly(ax, [P(0.06, 0, 0.31), P(0.76, 0, 0.31), P(0.76, 0, 0.79), P(0.06, 0, 0.79)],
          "#0B1F17", "none", 0, zo + 0.2)
    t = np.linspace(0, 1, 60)
    ecg = np.where((t % 0.33) < 0.04, 0.22, 0.0) - np.where(((t - 0.03) % 0.33) < 0.02, 0.08, 0)
    pts = [P(0.08 + 0.66 * tt, 0, 0.50 + e) for tt, e in zip(t, ecg)]
    ax.plot(*zip(*pts), color="#34D399", lw=0.7, zorder=zo + 0.3, solid_joinstyle="round")


def shield(ax, x, y, s, zo=5):
    """Bevelled privacy shield with a keyhole."""
    def outline(k, dy=0.0):
        w, h = 0.70 * s * k, 0.86 * s * k
        yy = y + dy
        return [(x - w / 2, yy + h * 0.32), (x, yy + h / 2), (x + w / 2, yy + h * 0.32),
                (x + w * 0.42, yy - h * 0.10), (x, yy - h / 2), (x - w * 0.42, yy - h * 0.10)]
    shadow(ax, x + 0.03 * s, y - 0.47 * s, 0.6 * s, 0.10 * s, zo - 1)
    _poly(ax, outline(1.0), "#A84A00", "#7C3500", 0.4, zo)
    o = outline(0.80)
    _poly(ax, o, "#E7782E", "none", 0, zo + 0.1)
    _poly(ax, [o[0], o[1], o[4], o[5]], "#F49A5C", "none", 0, zo + 0.15)   # lit half
    ax.add_patch(Circle((x, y + 0.05 * s), 0.07 * s, fc="white", ec="none", zorder=zo + 0.3))
    _poly(ax, [(x - 0.035 * s, y + 0.03 * s), (x + 0.035 * s, y + 0.03 * s),
               (x + 0.05 * s, y - 0.16 * s), (x - 0.05 * s, y - 0.16 * s)], "white", "none",
          0, zo + 0.3)
