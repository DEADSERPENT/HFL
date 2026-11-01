"""_icons.py — flat 2-D vector icons for the schematic figures (fig00, fig01).

Drawn from matplotlib patches, so they stay vector, need no external artwork
and follow the house palette. Every icon is placed by its centre (x, y) in
data units of a full-bleed axes and sized by its height in inches, so it keeps
its proportions whatever the figure aspect.

    ic = Icons(ax)            # after the axes limits are set
    ic.hospital(0.1, 0.5, 0.35)
"""
import numpy as np
from matplotlib.patches import Arc, Ellipse, FancyBboxPatch, Polygon, Rectangle

INK = "#2B2B2B"
SKIN = "#F2C9A0"


class Icons:
    def __init__(self, ax):
        self.ax = ax
        fig = ax.figure
        bb = ax.get_position()
        x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
        self.ix = fig.get_figwidth() * bb.width / (x1 - x0)    # inches per x unit
        self.iy = fig.get_figheight() * bb.height / (y1 - y0)  # inches per y unit

    # inches -> data units
    def _w(self, inch): return inch / self.ix
    def _h(self, inch): return inch / self.iy

    def _rbox(self, cx, cy, w_in, h_in, fc, ec=INK, lw=0.5, r_in=0.02, z=3):
        w, h = self._w(w_in), self._h(h_in)
        rs = min(self._w(r_in), self._h(r_in))
        self.ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, fc=fc, ec=ec,
                                         lw=lw, zorder=z,
                                         boxstyle=f"round,pad=0,rounding_size={rs}",
                                         mutation_aspect=self.ix / self.iy))

    def _ell(self, cx, cy, d_in_w, d_in_h, fc, ec=INK, lw=0.5, z=3):
        self.ax.add_patch(Ellipse((cx, cy), self._w(d_in_w), self._h(d_in_h), fc=fc,
                                  ec=ec, lw=lw, zorder=z))

    # ── people ─────────────────────────────────────────────────────────
    def person(self, x, y, s, shirt="#5B8DB8"):
        """Bust: head and shoulders, height s inches, centred at (x, y)."""
        self._ell(x, y + self._h(0.20 * s), 0.36 * s, 0.36 * s, SKIN)
        self._half(x, y - self._h(0.50 * s), 0.70 * s, 0.50 * s, shirt)

    def _half(self, cx, base, w_in, h_in, fc, z=2.9):
        """Upper half-ellipse standing on y = base (a torso)."""
        t = np.linspace(0, np.pi, 40)
        pts = np.c_[cx + self._w(w_in / 2) * np.cos(t), base + self._h(h_in) * np.sin(t)]
        self.ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=INK, lw=0.5, zorder=z))

    def patient(self, x, y, s):
        """Patient in a bed (side view)."""
        ax = self.ax
        bw, bh = self._w(0.95 * s), self._h(0.12 * s)
        ax.add_patch(Rectangle((x - bw / 2, y - self._h(0.12 * s)), bw, bh, fc="#D9E4EC",
                               ec=INK, lw=0.5, zorder=3))
        for fx in (-0.45, 0.45):                         # legs
            ax.add_patch(Rectangle((x + self._w(fx * s) - self._w(0.02 * s),
                                    y - self._h(0.30 * s)), self._w(0.04 * s),
                                   self._h(0.18 * s), fc=INK, ec="none", zorder=3))
        ax.add_patch(Rectangle((x - bw / 2 - self._w(0.03 * s), y - self._h(0.12 * s)),
                               self._w(0.05 * s), self._h(0.36 * s), fc="#9DB4C6",
                               ec=INK, lw=0.5, zorder=3))  # headboard
        self._ell(x - self._w(0.30 * s), y + self._h(0.07 * s), 0.22 * s, 0.22 * s, SKIN,
                  z=3.2)
        self._rbox(x + self._w(0.10 * s), y + self._h(0.05 * s), 0.62 * s, 0.14 * s,
                   "#8FB9DD", r_in=0.04 * s, z=3.1)        # blanket

    # ── devices ────────────────────────────────────────────────────────
    def monitor(self, x, y, s, trace="#2BB673"):
        """Bedside monitor with a waveform."""
        self._rbox(x, y + self._h(0.05 * s), 0.95 * s, 0.68 * s, "#3A4A5A", r_in=0.06 * s)
        self._rbox(x, y + self._h(0.07 * s), 0.80 * s, 0.50 * s, "#10202C", ec="none",
                   r_in=0.03 * s, z=3.1)
        px = [-0.36, -0.20, -0.14, -0.08, -0.02, 0.06, 0.16, 0.36]
        py = [0.05, 0.05, 0.22, -0.12, 0.05, 0.05, 0.12, 0.05]
        self.ax.plot([x + self._w(a * s) for a in px], [y + self._h(b * s) for b in py],
                     color=trace, lw=0.7, zorder=3.3, solid_joinstyle="round")
        self.ax.add_patch(Rectangle((x - self._w(0.05 * s), y - self._h(0.42 * s)),
                                    self._w(0.10 * s), self._h(0.14 * s), fc="#3A4A5A",
                                    ec=INK, lw=0.4, zorder=3))

    def watch(self, x, y, s):
        """Wrist-worn sensor."""
        self._rbox(x, y, 0.22 * s, 0.95 * s, "#4F5D6B", r_in=0.05 * s)       # strap
        self._rbox(x, y, 0.46 * s, 0.50 * s, "#2B3A47", r_in=0.10 * s, z=3.1)
        self._rbox(x, y, 0.34 * s, 0.38 * s, "#7FD1AE", ec="none", r_in=0.06 * s, z=3.2)

    # ── infrastructure ─────────────────────────────────────────────────
    def hospital(self, x, y, s, wall="#FFFFFF", cross="#D64545"):
        ax = self.ax
        w, h = self._w(0.95 * s), self._h(0.70 * s)
        ax.add_patch(Rectangle((x - w / 2, y - self._h(0.40 * s)), w, h, fc=wall, ec=INK,
                               lw=0.5, zorder=3))
        tw, th = self._w(0.42 * s), self._h(0.30 * s)
        ax.add_patch(Rectangle((x - tw / 2, y + self._h(0.30 * s)), tw, th, fc=wall,
                               ec=INK, lw=0.5, zorder=3))
        cw, ch = self._w(0.06 * s), self._h(0.20 * s)
        cy = y + self._h(0.45 * s)
        ax.add_patch(Rectangle((x - cw / 2, cy - ch / 2), cw, ch, fc=cross, ec="none",
                               zorder=3.2))
        ax.add_patch(Rectangle((x - self._w(0.10 * s), cy - self._h(0.03 * s)),
                               self._w(0.20 * s), self._h(0.06 * s), fc=cross,
                               ec="none", zorder=3.2))
        for i in (-1, 0, 1):
            for j in (0, 1):
                ax.add_patch(Rectangle((x + self._w((i * 0.27 - 0.06) * s),
                                        y + self._h((j * 0.22 - 0.06) * s)),
                                       self._w(0.12 * s), self._h(0.12 * s),
                                       fc="#9CC3E6", ec="none", zorder=3.1))
        ax.add_patch(Rectangle((x - self._w(0.07 * s), y - self._h(0.40 * s)),
                               self._w(0.14 * s), self._h(0.20 * s), fc="#7A8C9C",
                               ec="none", zorder=3.1))

    def server(self, x, y, s, fc="#5B7C99"):
        """Rack of three units with status lights."""
        for k in (-1, 0, 1):
            cy = y + self._h(0.30 * s * k)
            self._rbox(x, cy, 0.80 * s, 0.26 * s, fc, r_in=0.03 * s)
            for d, c in ((0.26, "#7CE07C"), (0.17, "#F5C542")):
                self._ell(x + self._w(d * s), cy, 0.06 * s, 0.06 * s, c, ec="none", z=3.2)
            self.ax.plot([x - self._w(0.32 * s), x - self._w(0.02 * s)], [cy, cy],
                         color="#DDE6EE", lw=0.6, zorder=3.2)

    def cloud(self, x, y, s, fc="#FFFFFF", lw=0.6):
        """Outlined cloud: shapes drawn twice, outlined underneath and fill-only on
        top, so only the outer contour shows."""
        lumps = ((-0.38, -0.05, 0.50), (-0.12, 0.12, 0.66), (0.20, 0.08, 0.58),
                 (0.42, -0.06, 0.42))
        for z, ec, k in ((3.0, INK, lw), (3.1, "none", 0)):
            for dx, dy, d in lumps:
                self._ell(x + self._w(dx * s), y + self._h(dy * s), d * s, d * s, fc,
                          ec=ec, lw=k, z=z)
            self._rbox(x + self._w(0.02 * s), y - self._h(0.14 * s), 1.18 * s, 0.28 * s,
                       fc, ec=ec, lw=k, r_in=0.13 * s, z=z)

    def database(self, x, y, s, fc="#8FB9DD"):
        w, h = 0.70 * s, 0.75 * s
        self.ax.add_patch(Rectangle((x - self._w(w / 2), y - self._h(h / 2)),
                                    self._w(w), self._h(h), fc=fc, ec="none", zorder=3))
        for t in (-h / 2, 0.0):
            self._ell(x, y + self._h(t), w, 0.24 * s, fc, z=3.05)
        self.ax.plot([x - self._w(w / 2)] * 2, [y - self._h(h / 2), y + self._h(h / 2)],
                     color=INK, lw=0.5, zorder=3.1)
        self.ax.plot([x + self._w(w / 2)] * 2, [y - self._h(h / 2), y + self._h(h / 2)],
                     color=INK, lw=0.5, zorder=3.1)
        self._ell(x, y + self._h(h / 2), w, 0.24 * s, "#CFE2F3", z=3.2)

    def shield(self, x, y, s, fc="#D55E00"):
        w, h = self._w(0.70 * s), self._h(0.85 * s)
        pts = [(x - w / 2, y + h * 0.35), (x, y + h / 2), (x + w / 2, y + h * 0.35),
               (x + w * 0.40, y - h * 0.10), (x, y - h / 2), (x - w * 0.40, y - h * 0.10)]
        self.ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=INK, lw=0.5, zorder=3))
        self.ax.plot([x - w * 0.18, x - w * 0.02, x + w * 0.22],
                     [y + h * 0.02, y - h * 0.15, y + h * 0.20], color="white", lw=1.0,
                     zorder=3.2, solid_capstyle="round")

    def attacker(self, x, y, s):
        """Hooded figure with a magnifier: the membership-inference adversary."""
        self._ell(x, y + self._h(0.12 * s), 0.46 * s, 0.50 * s, "#3B3B3B")
        self._ell(x, y + self._h(0.10 * s), 0.28 * s, 0.30 * s, "#1C1C1C", ec="none",
                  z=3.1)
        for dx in (-0.06, 0.06):
            self._ell(x + self._w(dx * s), y + self._h(0.12 * s), 0.05 * s, 0.03 * s,
                      "#FFFFFF", ec="none", z=3.2)
        self._half(x, y - self._h(0.52 * s), 0.72 * s, 0.46 * s, "#3B3B3B")
        self._ell(x + self._w(0.33 * s), y - self._h(0.10 * s), 0.26 * s, 0.26 * s,
                  "#CFE8F7", z=3.3)
        self.ax.plot([x + self._w(0.41 * s), x + self._w(0.52 * s)],
                     [y - self._h(0.19 * s), y - self._h(0.32 * s)], color=INK, lw=1.0,
                     zorder=3.3)

    def chart(self, x, y, s, colors=("#0072B2", "#D55E00", "#009E73")):
        """Small bar chart: an evaluation result."""
        self._rbox(x, y, 0.95 * s, 0.75 * s, "#FFFFFF", r_in=0.04 * s)
        for i, (hh, c) in enumerate(zip((0.40, 0.25, 0.52), colors)):
            self.ax.add_patch(Rectangle((x + self._w((-0.30 + 0.22 * i) * s),
                                         y - self._h(0.27 * s)), self._w(0.15 * s),
                                        self._h(hh * s), fc=c, ec="none", zorder=3.2))

    def antenna(self, x, y, s, color="#5B7C99"):
        """Wireless access point (edge radio)."""
        top = y + self._h(0.10 * s)
        self.ax.plot([x, x], [y - self._h(0.35 * s), top], color=INK, lw=0.8, zorder=3)
        for r in (0.22, 0.38):
            for a0 in (-50, 130):
                self.ax.add_patch(Arc((x, top), self._w(2 * r * s), self._h(2 * r * s),
                                      theta1=a0, theta2=a0 + 100, color=color, lw=0.8,
                                      zorder=3))
        self._ell(x, top, 0.10 * s, 0.10 * s, color)
