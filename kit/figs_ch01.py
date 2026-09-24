"""figs_ch01.py -- figures for Chapter 1, Why Parallel Computing?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
HEAT = sys.argv[2] if len(sys.argv) > 2 else "."
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)

# ------------------------------------------------ 1.0 chapter banner
banner(P("fig-01-00-banner.png"), seed=7, mode="rise")

# ------------------------------------------------ 1.1 trend data
def load(name):
    d = np.loadtxt(os.path.join(DATA, name + ".dat"))
    return d[:, 0], d[:, 1]

fig, ax = plt.subplots(figsize=(FIG_W, 2.75), layout="constrained")
series = [
    ("transistors", "Transistors (thousands)", ORANGE, "^"),
    ("specint", "Single-thread performance\n(SPECint $\\times 10^3$)", BLUE, "o"),
    ("frequency", "Clock frequency (MHz)", TEALD, "s"),
    ("watts", "Typical power (watts)", AMBER, "D"),
    ("cores", "Number of logical cores", INK, "v"),
]
for key, label, color, marker in series:
    x, y = load(key)
    ax.scatter(x, y, s=9, marker=marker, color=color, edgecolors="none",
               label=label, zorder=3, alpha=0.9)
ax.set_yscale("log")
ax.set_xlim(1970, 2023)
ax.set_ylim(0.1, 3e8)
ax.axvspan(2004, 2007, color=LIGHT, alpha=0.6, zorder=0, lw=0)
ax.text(2005.5, 1.2e8, "clock speeds\nstall", ha="center", va="top",
        fontsize=7, color=GRAY)
ax.grid(True, which="major", axis="y")
ax.set_xlabel("Year")
ax.set_ylabel("Value (log scale)")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
leg = ax.legend(loc="upper left", frameon=False, handletextpad=0.3,
                borderaxespad=0.2, labelspacing=0.35, markerscale=1.4)
save(fig, P("fig-01-01-trends.png"))

# ------------------------------------------------ 1.2 parallelism at every scale
fig, ax = canvas(FIG_W, 1.5)
cx = [0.46, 1.38, 2.3, 3.22, 4.14]
base = 0.66
# phone
box(ax, cx[0] - 0.14, base, 0.28, 0.5, fc=BLUE, ec=BLUE, r=0.05)
box(ax, cx[0] - 0.11, base + 0.1, 0.22, 0.35, fc=WHITE, ec=WHITE, r=0.02)
ax.add_patch(Circle((cx[0], base + 0.05), 0.025, fc=WHITE, ec="none", zorder=4))
# laptop
box(ax, cx[1] - 0.25, base + 0.12, 0.5, 0.34, fc=BLUE, ec=BLUE, r=0.03)
box(ax, cx[1] - 0.21, base + 0.16, 0.42, 0.26, fc=WHITE, ec=WHITE, r=0.01)
ax.add_patch(Polygon([(cx[1] - 0.32, base + 0.02), (cx[1] + 0.32, base + 0.02),
                      (cx[1] + 0.26, base + 0.12), (cx[1] - 0.26, base + 0.12)],
                     fc=INK, ec="none"))
# GPU card
box(ax, cx[2] - 0.32, base + 0.12, 0.64, 0.26, fc=TEALD, ec=TEALD, r=0.03)
for dx in (-0.15, 0.15):
    ax.add_patch(Circle((cx[2] + dx, base + 0.25), 0.1, fc=WHITE, ec="none", zorder=4))
    ax.add_patch(Circle((cx[2] + dx, base + 0.25), 0.035, fc=TEALD, ec="none", zorder=5))
ax.add_patch(Rectangle((cx[2] - 0.2, base + 0.05), 0.4, 0.07, fc=AMBER, ec="none", zorder=4))
# server rack
box(ax, cx[3] - 0.17, base, 0.34, 0.55, fc=INK, ec=INK, r=0.02)
for k in range(6):
    ax.add_patch(Rectangle((cx[3] - 0.13, base + 0.05 + k * 0.08), 0.26, 0.05,
                           fc=ORANGE if k % 2 else AMBER, ec="none", zorder=4))
# supercomputer: row of racks
for k in range(5):
    x0 = cx[4] - 0.4 + k * 0.165
    box(ax, x0, base, 0.14, 0.55, fc=INK, ec=INK, r=0.015)
    for m in range(6):
        ax.add_patch(Rectangle((x0 + 0.025, base + 0.05 + m * 0.08), 0.09,
                               0.045, fc=ORANGE if (m + k) % 2 else AMBER,
                               ec="none", zorder=4))
names = ["Smartphone", "Laptop", "Graphics card", "Server", "Supercomputer"]
descs = ["6–8 CPU cores\n+ GPU + NPU", "8–24 CPU cores\n+ GPU (+ NPU)",
         "10,000+ simple\narithmetic units", "Hundreds of cores",
         "Millions of cores\nacross thousands\nof nodes"]
for x, nm, ds in zip(cx, names, descs):
    ax.text(x, base - 0.1, nm, ha="center", va="top", fontsize=8,
            weight="bold", color=INK)
    ax.text(x, base - 0.27, ds, ha="center", va="top", fontsize=7,
            color=GRAY, linespacing=1.15)
arrow(ax, 0.1, 1.34, 4.5, 1.34, color=ORANGE, lw=1.4, ms=9)
ax.text(2.3, 1.4, "more parallel hardware", ha="center", va="bottom",
        fontsize=7.5, color=ORANGE, weight="bold")
save(fig, P("fig-01-02-scales.png"))

# ------------------------------------------------ 1.3 concurrency vs parallelism
fig, ax = canvas(FIG_W, 2.05)
x0, unit, lh = 0.8, 0.46, 0.2
colors = {"A": BLUE, "B": ORANGE, "C": TEAL}
def seg(lane_y, t0, t1, name):
    box(ax, x0 + t0 * unit, lane_y, (t1 - t0) * unit - 0.02, lh, name,
        fc=colors[name], ec="none", tc=WHITE if name != "C" else INK, fs=7.5,
        r=0.03, weight="bold")
ax.text(0.02, 1.9, "Concurrency: one core, tasks take turns", fontsize=8,
        weight="bold", va="center")
yc = 1.55
ax.text(x0 - 0.08, yc + lh / 2, "Core 1", ha="right", va="center", fontsize=7.5)
for t0, t1, nm in [(0, 1, "A"), (1, 2, "B"), (2, 3, "C"), (3, 4, "A"),
                   (4, 5, "B"), (5, 6, "C"), (6, 7, "A")]:
    seg(yc, t0, t1, nm)
ax.text(0.02, 1.2, "Parallelism: three cores, tasks run at the same instant",
        fontsize=8, weight="bold", va="center")
for k, (nm, dur) in enumerate([("A", 3), ("B", 2), ("C", 2)]):
    y = 0.85 - k * 0.26
    ax.text(x0 - 0.08, y + lh / 2, f"Core {k + 1}", ha="right", va="center",
            fontsize=7.5)
    ax.add_patch(Rectangle((x0, y), 7 * unit, lh, fc=PAPER, ec="none", zorder=0))
    for t in range(dur):
        seg(y, t, t + 1, nm)
ax.add_patch(Rectangle((x0, yc), 7 * unit, lh, fc=PAPER, ec="none", zorder=0))
arrow(ax, x0, 0.12, x0 + 7 * unit + 0.1, 0.12, color=GRAY, ms=7)
ax.text(x0 + 7 * unit + 0.15, 0.12, "time", va="center", fontsize=7.5,
        color=GRAY)
line(ax, [x0 + 3 * unit - 0.01] * 2, [0.18, 1.08], color=ORANGE, lw=0.9, ls="--")
ax.text(x0 + 3 * unit + 0.04, 1.02, "all done", fontsize=7, color=ORANGE,
        va="center")
line(ax, [x0 + 7 * unit - 0.01] * 2, [1.5, 1.8], color=ORANGE, lw=0.9, ls="--")
ax.text(x0 + 7 * unit + 0.04, 1.68, "all\ndone", fontsize=7, color=ORANGE,
        va="center")
save(fig, P("fig-01-03-concurrency.png"))

# ------------------------------------------------ 1.4 serial fraction
fig, ax = canvas(FIG_W, 1.9)
x0, sx = 0.72, 2.75 / 100         # 100 s spans 2.75 in
rows = [("1 core", 1), ("4 cores", 4), ("16 cores", 16), ("∞ cores", None)]
for k, (label, p) in enumerate(rows):
    y = 1.5 - k * 0.42
    ax.text(x0 - 0.08, y + 0.14, label, ha="right", va="center", fontsize=7.5,
            weight="bold")
    box(ax, x0, y, 20 * sx, 0.28, "serial\n20 s", fc=INK, ec="none", tc=WHITE,
        fs=6.5, r=0.02)
    if p == 1:
        box(ax, x0 + 20 * sx + 0.01, y, 80 * sx, 0.28, "parallel part: 80 s",
            fc=BLUE, ec="none", tc=WHITE, fs=7, r=0.02)
        total = 100
    elif p == 4:
        for m in range(4):
            box(ax, x0 + 20 * sx + 0.01, y + m * 0.07, 20 * sx, 0.062,
                fc=BLUE, ec="none", r=0.01)
        ax.text(x0 + 40 * sx + 0.06, y + 0.14, "80 ÷ 4 = 20 s", va="center",
                fontsize=7, color=BLUE)
        total = 40
    elif p == 16:
        for m in range(16):
            ax.add_patch(Rectangle((x0 + 20 * sx + 0.01, y + m * 0.0175),
                                   5 * sx, 0.014, fc=BLUE, ec="none"))
        ax.text(x0 + 25 * sx + 0.06, y + 0.14, "80 ÷ 16 = 5 s", va="center",
                fontsize=7, color=BLUE)
        total = 25
    else:
        ax.text(x0 + 20 * sx + 0.06, y + 0.14, "parallel part → 0 s",
                va="center", fontsize=7, color=BLUE)
        total = 20
    ax.text(x0 + 2.75 + 0.1, y + 0.14, f"{total} s   speedup {100 / total:.1f}×",
            va="center", fontsize=7.5, color=ORANGE if p is None else INK,
            weight="bold" if p is None else "normal")
save(fig, P("fig-01-04-serial.png"))

# ------------------------------------------------ 1.5 three ways to divide work
fig, ax = canvas(FIG_W, 1.85)
# (a) data parallelism: an "image" split into four regions
qc = [BLUE, ORANGE, TEALD, AMBER]
gx, gy, qs = 0.25, 0.5, 0.5
for q, (dx, dy) in enumerate([(0, 1), (1, 1), (0, 0), (1, 0)]):
    x, y = gx + dx * (qs + 0.04), gy + dy * (qs + 0.04)
    ax.add_patch(Rectangle((x, y), qs, qs, fc=qc[q], ec="none"))
    for t in (1, 2, 3):                      # faint pixel grid
        line(ax, [x + t * qs / 4] * 2, [y, y + qs], color=WHITE, lw=0.3, z=2)
        line(ax, [x, x + qs], [y + t * qs / 4] * 2, color=WHITE, lw=0.3, z=2)
    ax.text(x + qs / 2, y + qs / 2, f"C{q + 1}", ha="center", va="center",
            fontsize=8, weight="bold", color=WHITE if q < 3 else INK, zorder=3)
cs = (2 * qs + 0.04) / 4
ax.text(gx + 2 * cs, 0.3, "(a) Data parallelism", ha="center", fontsize=7.5,
        weight="bold")
ax.text(gx + 2 * cs, 0.14, "same operation, different data", ha="center",
        fontsize=7, color=GRAY)
# (b) task parallelism
tx = 1.72
for k, (nm, c) in enumerate([("Physics", BLUE), ("Audio", ORANGE),
                             ("Enemy AI", TEALD), ("Rendering", AMBER)]):
    box(ax, tx, 1.37 - k * 0.24, 0.95, 0.2, f"C{k + 1}:  {nm}", fc=c,
        ec="none", tc=WHITE if k < 3 else INK, fs=7, r=0.03)
ax.text(tx + 0.475, 0.3, "(b) Task parallelism", ha="center", fontsize=7.5,
        weight="bold")
ax.text(tx + 0.475, 0.14, "different operations at once", ha="center",
        fontsize=7, color=GRAY)
# (c) pipeline parallelism
px, cw_, ch_ = 3.42, 0.17, 0.2
stages = ["Read", "Filter", "Write"]
for s, nm in enumerate(stages):
    y = 1.3 - s * 0.26
    ax.text(px - 0.05, y + ch_ / 2, nm, ha="right", va="center", fontsize=7)
    for item in range(4):
        t = item + s
        ax.add_patch(Rectangle((px + t * cw_, y), cw_ - 0.02, ch_,
                               fc=qc[item], ec="none"))
        ax.text(px + t * cw_ + cw_ / 2 - 0.01, y + ch_ / 2, str(item + 1),
                ha="center", va="center", fontsize=7,
                color=WHITE if item < 3 else INK, weight="bold")
arrow(ax, px, 0.5, px + 6 * cw_ + 0.05, 0.5, color=GRAY, ms=6)
ax.text(px + 6 * cw_ + 0.02, 0.4, "time", va="center", ha="right", fontsize=7, color=GRAY)
ax.text(3.72, 0.3, "(c) Pipeline parallelism", ha="center", fontsize=7.5,
        weight="bold")
ax.text(3.72, 0.14, "stages overlap like an assembly line",
        ha="center", fontsize=7, color=GRAY)
save(fig, P("fig-01-05-three-ways.png"))

# ------------------------------------------------ 1.6 Flynn's taxonomy
fig, ax = canvas(FIG_W, 3.3)
L, B, CW, CH = 0.62, 0.15, 1.95, 1.4
ax.text(L + CW / 2, 3.18, "Single data stream", ha="center", fontsize=7.5,
        weight="bold", color=GRAY)
ax.text(L + CW * 1.5 + 0.08, 3.18, "Multiple data streams", ha="center",
        fontsize=7.5, weight="bold", color=GRAY)
ax.text(0.28, B + CH * 1.5 + 0.08, "Single\ninstruction\nstream", ha="center",
        va="center", fontsize=7.5, weight="bold", color=GRAY, rotation=90)
ax.text(0.28, B + CH / 2, "Multiple\ninstruction\nstreams", ha="center",
        va="center", fontsize=7.5, weight="bold", color=GRAY, rotation=90)
cells = {
    "SISD": (0, 1, 1, 1, "Classic single-core CPU", INK),
    "SIMD": (1, 1, 1, 4, "Vector units, GPUs", BLUE),
    "MISD": (0, 0, 3, 1, "Rare; debated examples", GRAY),
    "MIMD": (1, 0, 3, 3, "Multicore CPUs, clusters", ORANGE),
}
for name, (col, row, nI, nD, ex, c) in cells.items():
    x = L + col * (CW + 0.16)
    y = B + row * (CH + 0.12)
    box(ax, x, y, CW, CH, fc=PAPER, ec=LIGHT, r=0.06, z=0)
    ax.text(x + 0.1, y + CH - 0.13, name, fontsize=11, weight="bold", color=c,
            va="center")
    ax.text(x + CW - 0.08, y + CH - 0.13, ex, fontsize=6.8, color=GRAY,
            va="center", ha="right")
    nP = max(nI, nD)
    def xs(n):
        return [x + CW / 2 + (k - (n - 1) / 2) * 0.42 for k in range(n)]
    yI, yP, yD = y + 0.83, y + 0.5, y + 0.15
    for xi in xs(nI):
        box(ax, xi - 0.16, yI, 0.32, 0.18, "I", fc=c, ec="none", tc=WHITE,
            fs=7, r=0.03, weight="bold")
    for k, xp in enumerate(xs(nP)):
        box(ax, xp - 0.16, yP, 0.32, 0.18, "P", fc=WHITE, ec=c, tc=c, fs=7,
            r=0.03, weight="bold", lw=1)
        xi = xs(nI)[k if nI > 1 else 0]
        line(ax, [xi, xp], [yI, yP + 0.18], color=c, lw=0.8)
        xd = xs(nD)[k if nD > 1 else 0]
        line(ax, [xp, xd], [yP, yD + 0.16], color=GRAY, lw=0.8)
    for xd in xs(nD):
        box(ax, xd - 0.16, yD, 0.32, 0.16, "D", fc=LIGHT, ec="none", tc=INK,
            fs=6.5, r=0.02)
save(fig, P("fig-01-06-flynn.png"))

# ------------------------------------------------ 1.7 memory architectures
fig, ax = canvas(FIG_W, 3.05)
def core(x, y, c=BLUE, w=0.3, lab="C"):
    box(ax, x, y, w, 0.2, lab, fc=c, ec="none", tc=WHITE, fs=6.5, r=0.03,
        weight="bold")
def mem(x, y, w, lab="Memory", c=AMBER):
    box(ax, x, y, w, 0.22, lab, fc=c, ec="none", tc=INK, fs=6.8, r=0.03)
def title(x, y, t):
    ax.text(x, y, t, fontsize=7.5, weight="bold", va="center")
# (a) UMA
ox, oy = 0.05, 1.62
box(ax, ox, oy, 2.2, 1.35, fc=PAPER, ec=LIGHT, r=0.05, z=0)
title(ox + 0.08, oy + 1.2, "(a) Shared memory (UMA)")
for k in range(4):
    core(ox + 0.2 + k * 0.48, oy + 0.8)
    line(ax, [ox + 0.35 + k * 0.48] * 2, [oy + 0.8, oy + 0.58], color=INK)
line(ax, [ox + 0.2, ox + 1.95], [oy + 0.58, oy + 0.58], color=INK, lw=1.6)
ax.text(ox + 2.0, oy + 0.58, "bus", fontsize=6.5, color=GRAY, va="center")
line(ax, [ox + 1.08] * 2, [oy + 0.58, oy + 0.4], color=INK)
mem(ox + 0.35, oy + 0.18, 1.45)
# (b) NUMA
ox = 2.35
box(ax, ox, oy, 2.2, 1.35, fc=PAPER, ec=LIGHT, r=0.05, z=0)
title(ox + 0.08, oy + 1.2, "(b) Shared memory (NUMA)")
for s in range(2):
    sx0 = ox + 0.12 + s * 1.07
    box(ax, sx0, oy + 0.12, 0.93, 0.95, fc=WHITE, ec=LIGHT, r=0.04, z=0)
    core(sx0 + 0.1, oy + 0.75)
    core(sx0 + 0.53, oy + 0.75)
    mem(sx0 + 0.1, oy + 0.22, 0.73, lab="Local memory")
    for cxx in (sx0 + 0.25, sx0 + 0.68):
        line(ax, [cxx] * 2, [oy + 0.75, oy + 0.62], color=INK)
    line(ax, [sx0 + 0.25, sx0 + 0.68], [oy + 0.62, oy + 0.62], color=INK)
    line(ax, [sx0 + 0.465] * 2, [oy + 0.62, oy + 0.44], color=INK)
arrow(ax, ox + 1.02, oy + 0.85, ox + 1.22, oy + 0.85, color=ORANGE, lw=1.4,
      style="<|-|>", ms=6)
ax.text(ox + 1.12, oy + 1.0, "slower", fontsize=6.3, color=ORANGE, ha="center")
# (c) distributed
ox, oy = 0.05, 0.1
box(ax, ox, oy, 2.2, 1.42, fc=PAPER, ec=LIGHT, r=0.05, z=0)
title(ox + 0.08, oy + 1.27, "(c) Distributed memory")
ax.add_patch(matplotlib.patches.Ellipse((ox + 1.1, oy + 0.62), 0.8, 0.34,
                                        fc=WHITE, ec=GRAY, lw=0.8, zorder=2))
ax.text(ox + 1.1, oy + 0.62, "network", fontsize=6.8, ha="center",
        va="center", color=GRAY, zorder=3)
for nx, ny in [(0.12, 0.74), (1.58, 0.74), (0.12, 0.1), (1.58, 0.1)]:
    core(ox + nx, oy + ny + 0.22, w=0.5, lab="CPU")
    mem(ox + nx, oy + ny, 0.5, lab="Mem")
    ex = ox + 1.1 + (0.3 if nx > 1 else -0.3)
    ey = oy + 0.62 + (0.1 if ny > 0.5 else -0.1)
    nxp = ox + nx + (0 if nx > 1 else 0.5)
    line(ax, [nxp, ex], [oy + ny + 0.21, ey], color=GRAY, lw=0.8)
# (d) hybrid
ox = 2.35
box(ax, ox, oy, 2.2, 1.42, fc=PAPER, ec=LIGHT, r=0.05, z=0)
title(ox + 0.08, oy + 1.27, "(d) Hybrid cluster")
for s in range(2):
    nx = ox + 0.1 + s * 1.07
    box(ax, nx, oy + 0.42, 0.93, 0.7, fc=WHITE, ec=LIGHT, r=0.04, z=0)
    for k in range(3):
        core(nx + 0.06 + k * 0.29, oy + 0.85, w=0.23)
    mem(nx + 0.06, oy + 0.52, 0.52, lab="Memory")
    box(ax, nx + 0.62, oy + 0.52, 0.25, 0.22, "GPU", fc=TEALD, ec="none",
        tc=WHITE, fs=6.3, r=0.03, weight="bold")
    line(ax, [nx + 0.465] * 2, [oy + 0.42, oy + 0.25], color=GRAY)
line(ax, [ox + 0.57, ox + 1.64], [oy + 0.25, oy + 0.25], color=GRAY, lw=1.4)
ax.text(ox + 1.1, oy + 0.12, "network", fontsize=6.8, ha="center",
        color=GRAY)
save(fig, P("fig-01-07-memory.png"))

# ------------------------------------------------ 1.8 HeatSim snapshots (real output)
steps = [0, 200, 2000, 20000]
fig, axs = plt.subplots(1, 4, figsize=(FIG_W, 1.42),
                        gridspec_kw=dict(wspace=0.08))
for a, s in zip(axs, steps):
    g = np.fromfile(os.path.join(HEAT, f"snap_{s}.bin")).reshape(128, 128)
    im = a.imshow(g, cmap=HEAT_CMAP, vmin=0, vmax=100, interpolation="nearest")
    a.set_xticks([])
    a.set_yticks([])
    for sp in a.spines.values():
        sp.set_visible(False)
    a.set_title(f"Step {s:,}", fontsize=7.5, pad=3)
cb = fig.colorbar(im, ax=axs, fraction=0.025, pad=0.02)
cb.set_label("°C", fontsize=7)
cb.ax.tick_params(labelsize=6.5, length=2)
cb.outline.set_visible(False)
save(fig, P("fig-01-08-heatsim.png"))

# ------------------------------------------------ 1.9 HeatSim roadmap
fig, ax = canvas(FIG_W, 1.75)
items = [("v1", "Sequential", "Ch 3", INK), ("v2", "Cache-friendly", "Ch 5", BLUE),
         ("v3", "Vectorized", "Ch 6", BLUE), ("v4", "Pthreads", "Ch 7", BLUE),
         ("v5", "OpenMP", "Ch 8", BLUE), ("v6", "MPI", "Ch 10", ORANGE),
         ("v7", "MPI + OpenMP", "Ch 12", ORANGE), ("v8", "GPU (CUDA)", "Ch 14", TEALD)]
bw, bh, gap = 0.95, 0.46, 0.2
for k, (v, nm, ch, c) in enumerate(items):
    r, cidx = divmod(k, 4)
    cidx = cidx if r == 0 else 3 - cidx          # snake layout
    x = 0.1 + cidx * (bw + gap)
    y = 1.05 - r * 0.72
    box(ax, x, y, bw, bh, fc=c, ec="none", r=0.06)
    ax.text(x + 0.08, y + bh - 0.12, v, fontsize=7, color=WHITE, weight="bold",
            va="center")
    ax.text(x + bw - 0.08, y + bh - 0.12, ch, fontsize=6.5, color=WHITE,
            va="center", ha="right")
    ax.text(x + bw / 2, y + 0.15, nm, fontsize=7.5, color=WHITE,
            weight="bold", ha="center", va="center")
    if k < 7:
        if k == 3:
            arrow(ax, x + bw / 2, y - 0.02, x + bw / 2, y - 0.24, color=GRAY,
                  ms=7)
        elif r == 0:
            arrow(ax, x + bw + 0.02, y + bh / 2, x + bw + gap - 0.02,
                  y + bh / 2, color=GRAY, ms=7)
        else:
            arrow(ax, x - 0.02, y + bh / 2, x - gap + 0.02, y + bh / 2,
                  color=GRAY, ms=7)
for k, (nm, c) in enumerate([("Part I", INK), ("Part II: one machine", BLUE),
                             ("Part III: many machines", ORANGE),
                             ("Part IV: accelerators", TEALD)]):
    ax.add_patch(Rectangle((0.12 + k * 1.12, 0.07), 0.1, 0.1, fc=c, ec="none"))
    ax.text(0.26 + k * 1.12, 0.12, nm, fontsize=6.8, va="center", color=GRAY)
save(fig, P("fig-01-09-roadmap.png"))

print("figures written to", OUT)
