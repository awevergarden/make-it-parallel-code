"""bookstyle.py -- shared figure style for *Make It Parallel* (6 x 9 in edition).

Every figure in the book is drawn with these colors, fonts, and helpers so
that chapters written weeks apart look identical. Figures are rendered at
their final printed size (max width FIG_W inches) at 300 DPI.

Grayscale rule: the SERIES colors have clearly different luminance, and charts
also use distinct markers/line styles, so figures survive black-ink printing.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (FancyBboxPatch, Circle, Polygon, Rectangle,
                                Wedge, Arc, FancyArrowPatch)
import numpy as np

# ---------------------------------------------------------------- palette
INK    = "#1B2A41"   # near-black navy: text, outlines        (L ~16%)
BLUE   = "#1565C0"   # primary                                 (L ~34%)
ORANGE = "#E4572E"   # accent / "hot"                          (L ~49%)
TEAL   = "#56C8B8"   # secondary fill                          (L ~64%)
AMBER  = "#F5B841"   # highlight fill                          (L ~74%)
TEALD  = "#0F7C74"   # teal dark enough for text/lines
GRAY   = "#6B7785"   # secondary text, axes
LIGHT  = "#D9DEE4"   # idle / background shapes
PAPER  = "#F4F6F8"   # panel backgrounds
PURPLE = "#6C4AB6"
GREEN  = "#2E8540"
RED    = "#C0392B"
WHITE  = "#FFFFFF"
SERIES = [BLUE, ORANGE, TEALD, AMBER, INK]
HEAT_CMAP = "inferno"      # perceptually uniform, monotonic in grayscale

# Callout colors (must match the Word template in make_reference.py)
CALLOUTS = {
    "predict":   ("#0F7C74", "PREDICT, THEN MEASURE"),
    "bughunt":   ("#C0392B", "BUG HUNT"),
    "deepdive":  ("#6C4AB6", "DEEP DIVE"),
    "history":   ("#9A6B12", "HISTORICAL NOTE"),
    "exam":      ("#1565C0", "EXAM CORNER"),
    "tryit":     ("#2E8540", "TRY IT"),
    "takeaways": ("#1B2A41", "KEY TAKEAWAYS"),
    "mistake":   ("#D35400", "COMMON MISTAKE"),
}

FIG_W = 4.6          # max figure width in inches (text block is 4.65 in)
DPI = 300
SANS = "Carlito"     # metric twin of Calibri (the book's heading font)
MONO = "DejaVu Sans Mono"

plt.rcParams.update({
    "font.family": SANS, "font.size": 8,
    "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.edgecolor": GRAY, "axes.linewidth": 0.6, "axes.labelcolor": INK,
    "xtick.color": GRAY, "ytick.color": GRAY, "text.color": INK,
    "grid.color": LIGHT, "grid.linewidth": 0.5,
    "savefig.dpi": DPI, "figure.dpi": 100,
    "mathtext.fontset": "dejavusans",
})


def canvas(w, h):
    """Figure with one axes spanning it, coordinates in inches."""
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def save(fig, path, pad=0.03):
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=pad,
                facecolor="white")
    plt.close(fig)


def box(ax, x, y, w, h, text="", fc=PAPER, ec=GRAY, tc=INK, fs=7.5,
        lw=0.8, r=0.05, weight="normal", z=2, ls="-"):
    """Rounded box with lower-left corner (x, y) and centered text."""
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                       fc=fc, ec=ec, lw=lw, zorder=z, ls=ls)
    ax.add_patch(p)
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=tc, weight=weight, zorder=z + 1,
                linespacing=1.15)
    return p


def arrow(ax, x1, y1, x2, y2, color=GRAY, lw=0.9, style="-|>", ms=6, z=1,
          shrink=0):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                        mutation_scale=ms, color=color, lw=lw, zorder=z,
                        shrinkA=shrink, shrinkB=shrink)
    ax.add_patch(a)
    return a


def line(ax, xs, ys, color=GRAY, lw=0.9, z=1, ls="-"):
    ax.plot(xs, ys, color=color, lw=lw, zorder=z, ls=ls,
            solid_capstyle="round")


# ------------------------------------------------------------------ icons
def _icon_canvas():
    fig = plt.figure(figsize=(0.25, 0.25))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def _badge(ax, color):
    ax.add_patch(Circle((0, 0), 0.98, fc=color, ec="none"))


def _glyph(kind, ax):
    w = WHITE
    if kind == "predict":            # gauge
        ax.add_patch(Arc((0, -0.2), 1.2, 1.2, theta1=0, theta2=180,
                         color=w, lw=2.2))
        ax.plot([0, 0.36], [-0.2, 0.28], color=w, lw=2.2,
                solid_capstyle="round")
        ax.add_patch(Circle((0, -0.2), 0.12, fc=w, ec="none"))
    elif kind == "bughunt":          # beetle
        ax.add_patch(matplotlib.patches.Ellipse((0, -0.1), 0.62, 0.86,
                                                fc=w, ec="none"))
        ax.add_patch(Circle((0, 0.45), 0.2, fc=w, ec="none"))
        for yy in (0.15, -0.1, -0.35):
            ax.plot([-0.62, -0.3], [yy + 0.08, yy], color=w, lw=1.6)
            ax.plot([0.3, 0.62], [yy, yy + 0.08], color=w, lw=1.6)
    elif kind == "deepdive":         # stacked layers
        for k, yy in enumerate((0.3, 0.0, -0.3)):
            ax.add_patch(Polygon([(-0.55, yy), (0, yy + 0.22), (0.55, yy),
                                  (0, yy - 0.22)], closed=True,
                                 fc=w if k == 0 else "none", ec=w, lw=1.4))
    elif kind == "history":          # hourglass
        ax.add_patch(Polygon([(-0.42, 0.55), (0.42, 0.55), (0, 0)],
                             fc=w, ec="none"))
        ax.add_patch(Polygon([(-0.42, -0.55), (0.42, -0.55), (0, 0)],
                             fc=w, ec="none"))
        ax.plot([-0.5, 0.5], [0.6, 0.6], color=w, lw=1.6)
        ax.plot([-0.5, 0.5], [-0.6, -0.6], color=w, lw=1.6)
    elif kind == "exam":             # check mark
        ax.plot([-0.48, -0.12, 0.52], [0.0, -0.38, 0.42], color=w, lw=2.8,
                solid_capstyle="round", solid_joinstyle="round")
    elif kind == "tryit":            # terminal prompt
        ax.text(0.02, -0.04, ">_", ha="center", va="center", color=w,
                fontsize=7.5, family=MONO, weight="bold")
    elif kind == "takeaways":        # key
        ax.add_patch(Circle((-0.3, 0.12), 0.26, fc="none", ec=w, lw=1.8))
        ax.plot([-0.05, 0.55], [0.12, 0.12], color=w, lw=1.8)
        ax.plot([0.3, 0.3], [0.12, -0.12], color=w, lw=1.8)
        ax.plot([0.48, 0.48], [0.12, -0.08], color=w, lw=1.8)
    elif kind == "mistake":          # exclamation
        ax.text(0, -0.02, "!", ha="center", va="center", color=w,
                fontsize=10, weight="bold")


def make_icons(outdir):
    """Callout badges plus shape-coded track markers (grayscale safe)."""
    for kind, (color, _) in CALLOUTS.items():
        fig, ax = _icon_canvas()
        _badge(ax, color)
        _glyph(kind, ax)
        fig.savefig(f"{outdir}/{kind}.png", dpi=600, transparent=True)
        plt.close(fig)
    tracks = {"core": (INK, "circle"), "practice": (ORANGE, "triangle"),
              "deep": (PURPLE, "diamond")}
    for name, (color, shape) in tracks.items():
        fig, ax = _icon_canvas()
        if shape == "circle":
            ax.add_patch(Circle((0, 0), 0.8, fc=color, ec="none"))
        elif shape == "triangle":
            ax.add_patch(Polygon([(-0.85, -0.7), (0.85, -0.7), (0, 0.85)],
                                 fc=color, ec="none"))
        else:
            ax.add_patch(Polygon([(0, 0.95), (0.8, 0), (0, -0.95),
                                  (-0.8, 0)], fc=color, ec="none"))
        fig.savefig(f"{outdir}/track-{name}.png", dpi=600, transparent=True)
        plt.close(fig)


# ----------------------------------------------------------------- banner
def banner(path, seed=1, mode="rise", w=4.65, h=1.1):
    """Chapter-opener art: a field of 'cores' lighting up.

    mode: 'rise'  -- activity grows left to right (Chapter 1)
          'wave'  -- a traveling wave of activity
          'blocks'-- rectangular domains (decomposition chapters)
    Change seed/mode per chapter; keep everything else fixed.
    """
    rng = np.random.default_rng(seed)
    cols, rows = 46, 9
    fig, ax = canvas(w, h)
    cw, ch = w / cols, h / rows
    lit = [BLUE, TEALD, TEAL, AMBER, ORANGE]
    for c in range(cols):
        for r in range(rows):
            u = c / (cols - 1)
            if mode == "rise":
                p = u ** 1.6
            elif mode == "wave":
                p = 0.5 + 0.5 * np.sin(2 * np.pi * (u * 1.5 - r / rows * 0.3))
            else:
                p = 1.0 if (c // 8 + r // 3) % 2 == 0 else 0.25
            on = rng.random() < p
            if on:
                idx = min(len(lit) - 1,
                          int((u * 0.75 + rng.random() * 0.35) * len(lit)))
                fc = lit[idx]
            else:
                fc = LIGHT if rng.random() < 0.75 else PAPER
            ax.add_patch(FancyBboxPatch(
                (c * cw + cw * 0.12, r * ch + ch * 0.12), cw * 0.76, ch * 0.76,
                boxstyle=f"round,pad=0,rounding_size={cw * 0.18}",
                fc=fc, ec="none"))
    save(fig, path, pad=0)
