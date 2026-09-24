"""figs_ch14.py -- figures for Chapter 14, GPU Programming.

Usage: python3 kit/figs_ch14.py OUTDIR
Figure 14.4 is a MODEL (gpumodel.py) with measured one-core CPU points.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import gpumodel as gm
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

banner(P("fig-14-00-banner.png"), seed=98, mode="wave")

# ------------------------------------------------ 14.1 CPU vs GPU (schematic)
fig, ax = canvas(FIG_W, 1.9)
ax.text(0.05, 1.85, "(a) CPU: a few large cores", fontsize=7.5, weight="bold", va="top")
for k in range(4):
    x, y = 0.1 + (k % 2) * 0.95, 0.9 - (k // 2) * 0.55
    box(ax, x, y + 0.2, 0.55, 0.3, "control +\nprediction", fc=LIGHT, ec="none", fs=5.8)
    box(ax, x + 0.58, y + 0.2, 0.3, 0.3, "ALU", fc=BLUE, ec="none", tc=WHITE, fs=6)
    box(ax, x, y, 0.88, 0.16, "cache", fc=AMBER, ec="none", fs=6)
box(ax, 0.1, 0.05, 1.83, 0.22, "large shared cache", fc=AMBER, ec="none", fs=6.4)
line(ax, [2.2, 2.2], [0.05, 1.8], color=LIGHT, lw=0.8)
ax.text(2.35, 1.85, "(b) GPU: many simple processors", fontsize=7.5, weight="bold", va="top")
for s_ in range(6):
    x, y = 2.4 + (s_ % 3) * 0.72, 0.95 - (s_ // 3) * 0.6
    ax.add_patch(Rectangle((x, y), 0.66, 0.52, fc=PAPER, ec=GRAY, lw=0.5))
    for r in range(4):
        for c in range(8):
            ax.add_patch(Rectangle((x + 0.03 + c * 0.078, y + 0.2 + r * 0.075), 0.065, 0.06,
                         fc=TEALD, ec="none"))
    box(ax, x + 0.03, y + 0.03, 0.6, 0.13, "shared memory", fc=AMBER, ec="none", fs=5.2, r=0.01)
ax.text(3.45, 0.18, "each box: a streaming multiprocessor (SM)", fontsize=6.3, color=GRAY,
        ha="center")
save(fig, P("fig-14-01-cpu-gpu.png"))

# ------------------------------------------------ 14.2 thread hierarchy (schematic)
fig, ax = canvas(FIG_W, 1.85)
ax.text(0.05, 1.8, "(a) A grid of blocks covers the plate", fontsize=7.5, weight="bold", va="top")
gx0, gy0, bw, bh = 0.15, 0.25, 0.4, 0.2
for by in range(5):
    for bx in range(4):
        hl = (bx, by) == (1, 2)
        ax.add_patch(Rectangle((gx0 + bx * bw, gy0 + (4 - by) * bh), bw - 0.02, bh - 0.02,
                     fc=ORANGE if hl else LIGHT, ec="none"))
ax.text(gx0 + 1.5 * bw, gy0 + 2.5 * bh + 0.02, "block\n(1, 2)", ha="center", va="center",
        fontsize=5.6, color=WHITE, linespacing=1.0)
ax.text(gx0, 0.1, "each block: a 32 × 8 patch of cells", fontsize=6.3, color=GRAY)
line(ax, [1.95, 1.95], [0.05, 1.75], color=LIGHT, lw=0.8)
ax.text(2.1, 1.8, "(b) A block of 32 × 8 threads = 8 warps", fontsize=7.5, weight="bold",
        va="top")
for ty in range(8):
    for tx in range(32):
        ax.add_patch(Rectangle((2.15 + tx * 0.07, 0.3 + (7 - ty) * 0.15), 0.06, 0.12,
                     fc=[BLUE, TEALD][ty % 2], ec="none"))
ax.text(2.15, 0.12, "one thread per cell; each row of 32 threads is one warp",
        fontsize=6.3, color=GRAY)
arrow(ax, gx0 + 2 * bw, gy0 + 2.5 * bh, 2.12, 0.9, color=GRAY, ms=6)
save(fig, P("fig-14-02-hierarchy.png"))

# ------------------------------------------------ 14.3 shared tile with halo
fig, ax = canvas(FIG_W, 1.35)
cw = 0.115
for r in range(10):
    for c in range(34):
        halo = r in (0, 9) or c in (0, 33)
        corner = r in (0, 9) and c in (0, 33)
        ax.add_patch(Rectangle((0.2 + c * cw, 0.2 + (9 - r) * cw), cw - 0.012, cw - 0.012,
                     fc=PAPER if corner else (AMBER if halo else BLUE), ec="none"))
ax.text(0.2, 0.08, "10 × 34 tile in shared memory: 32 × 8 cells the block updates (blue) "
        "plus a one-cell halo (amber); 2,720 bytes", fontsize=6.3, color=GRAY)
save(fig, P("fig-14-03-tile.png"))

# ------------------------------------------------ 14.4 throughput model
c10 = json.load(open(os.path.join(ROOT, "data", "ch10", "values.json")))
ns = 2 ** np.arange(7, 15)
fig, ax = plt.subplots(figsize=(FIG_W, 2.3), layout="constrained")
ax.plot(ns, [gm.rate(int(n), gpu="H100") / 1e9 for n in ns], color=INK, lw=1.2, ls="-.",
        marker="D", ms=3, label="H100, tiled kernel (model)")
ax.plot(ns, [gm.rate(int(n)) / 1e9 for n in ns], color=TEALD, lw=1.2, marker="o", ms=3,
        label="A100, tiled kernel (model)")
ax.plot(ns, [gm.rate(int(n), copy_each_step=True) / 1e9 for n in ns], color=ORANGE, lw=1.2,
        ls="--", marker="^", ms=3, label="A100, copying the grid every step (model)")
cp = [(n, float(c10[f"r_v1_{n}"].replace(",", "")) / 1e3) for n in (256, 1024, 4096)]
ax.scatter([n for n, _ in cp], [r for _, r in cp], color=BLUE, marker="s", s=22, zorder=4,
           label="one CPU core, HeatSim v1 (measured)")
ax.set_xscale("log", base=2); ax.set_yscale("log")
ax.set_xticks([128, 512, 2048, 8192], ["128", "512", "2,048", "8,192"])
ax.set_ylim(0.3, 4000)
ax.set_xlabel("Grid width n (log scale)")
ax.set_ylabel("Billion cell updates\nper second (log scale)")
ax.grid(True, which="major")
ax.legend(loc="upper left", frameon=False, fontsize=6.5)
clean(ax)
save(fig, P("fig-14-04-model.png"))
print("figures written to", OUT)
