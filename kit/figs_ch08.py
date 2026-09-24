"""figs_ch08.py -- figures for Chapter 8, OpenMP.

Usage: python3 kit/figs_ch08.py OUTDIR
Figure 8.2 uses the real static assignments recorded by schedule.c;
Figure 8.3 is a MODEL (kit/mmmodel.py) driven by measured one-core rates.
"""
import sys, os, csv, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import mmmodel as mm
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch08")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)
THREAD = [INK, BLUE, ORANGE, TEAL]      # luminance 16/34/49/64: grayscale-safe

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

# ------------------------------------------------ 8.0 banner (Part II)
banner(P("fig-08-00-banner.png"), seed=56, mode="wave")

# ------------------------------------------------ 8.1 fork-join (schematic)
fig, ax = canvas(FIG_W, 1.5)
ym = 1.2
segs = [(0.6, 1.2, "serial"), (1.2, 2.25, "parallel region"), (2.25, 2.8, "serial"),
        (2.8, 3.9, "parallel region"), (3.9, 4.5, "serial")]
for x0, x1, kind in segs:
    if kind == "serial":
        line(ax, [x0, x1], [ym, ym], color=INK, lw=2.5)
    else:
        for k in range(4):
            y = ym - k * 0.26
            line(ax, [x0 + 0.08, x1 - 0.08], [y, y], color=THREAD[k], lw=2.5)
            if k:
                line(ax, [x0, x0 + 0.08], [ym, y], color=GRAY, lw=0.7)
                line(ax, [x1 - 0.08, x1], [y, ym], color=GRAY, lw=0.7)
        ax.text((x0 + x1) / 2, ym + 0.12, kind, ha="center", fontsize=6.8,
                color=INK)
        ax.text(x0, 0.2, "fork", ha="center", fontsize=6.5, color=GRAY)
        ax.text(x1, 0.2, "join", ha="center", fontsize=6.5, color=GRAY)
ax.text(0.55, ym, "master", ha="right", va="center", fontsize=6.8, weight="bold")
for k in range(1, 4):
    ax.text(0.55, ym - k * 0.26, f"thread {k}", ha="right", va="center",
            fontsize=6.8, color=GRAY)
save(fig, P("fig-08-01-fork-join.png"))

# ------------------------------------------------ 8.2 schedules (real assignment)
owner = {}
for r in csv.DictReader(open(os.path.join(DATA, "schedule.csv"))):
    owner.setdefault(r["schedule"], {})[int(r["i"])] = int(r["thread"])
labels = [("static", "schedule(static)"), ("static25", "schedule(static, 25)"),
          ("static1", "schedule(static, 1)")]
fig = plt.figure(figsize=(FIG_W, 2.0))
gs = fig.add_gridspec(3, 2, width_ratios=[2.2, 1], wspace=0.25, hspace=0.55,
                      left=0.02, right=0.98, top=0.9, bottom=0.2)
for r_, (k, lab) in enumerate(labels):
    ax = fig.add_subplot(gs[r_, 0])
    strip = np.array([[owner[k][i] for i in range(400)]])
    from matplotlib.colors import ListedColormap
    ax.imshow(strip, aspect="auto", cmap=ListedColormap(THREAD),
              interpolation="nearest", vmin=0, vmax=3)
    ax.set_yticks([])
    ax.set_xticks([0, 100, 200, 300, 399] if r_ == 2 else [])
    ax.set_title(lab, fontsize=7, loc="left", pad=2, family=MONO)
    for s in ax.spines.values():
        s.set_visible(False)
    bx = fig.add_subplot(gs[r_, 1])
    work = [0] * 4
    for i, t in owner[k].items():
        work[t] += i + 1
    bx.barh(range(4), work, color=THREAD, height=0.7)
    bx.set_xlim(0, 36000)
    bx.set_yticks([])
    bx.set_xticks([])
    bx.axvline(sum(work) / 4, color=INK, lw=0.8, ls=":")
    for s in bx.spines.values():
        s.set_visible(False)
    if r_ == 0:
        bx.set_title("work per thread", fontsize=7, loc="left", pad=2)
fig.text(0.02, 0.01, "iteration i; threads 0–3: navy, blue, orange, teal",
         fontsize=6.5, color=GRAY)
fig.text(0.72, 0.01, "dotted: perfect balance", fontsize=6.5, color=GRAY)
save(fig, P("fig-08-02-schedules.png"))

# ------------------------------------------------ 8.3 matmul model
g = {}
for r in csv.DictReader(open(os.path.join(DATA, "matmul.csv"))):
    g.setdefault((r["variant"], int(r["n"])), []).append(float(r["GFLOPs"]))
g = {k: st.median(x) for k, x in g.items()}
ps = np.arange(1, 17)
fig, ax = plt.subplots(figsize=(FIG_W, 2.2), layout="constrained")
for ver, lab, c, mk, ls in [("tiled", "tiled (64 × 64)", BLUE, "o", "-"),
                             ("ikj", "ikj", ORANGE, "^", "--")]:
    r1 = g[(ver, 2048)] * 1e9
    ax.plot(ps, [mm.rate(ver, int(p), r1) / 1e9 for p in ps], color=c, marker=mk,
            ms=3.5, lw=1.2, ls=ls, label=lab)
cap = mm.BETA * mm.BW_ONE_CORE / mm.BYTES_PER_FLOP["ikj"] / 1e9
ax.axhline(cap, color=GRAY, lw=0.7, ls=":")
ax.text(16.3, cap + 1.5, "ikj: shared bandwidth\nlimit", fontsize=6.6, color=GRAY,
        ha="right", va="bottom", linespacing=1.1)
ax.set_xlim(0.5, 16.5)
ax.set_xticks([1, 2, 4, 8, 12, 16])
ax.set_xlabel("Cores p, one thread per core")
ax.set_ylabel("Predicted GFLOP/s")
ax.grid(True, axis="y")
ax.legend(loc="upper left", frameon=False, fontsize=7)
ax.text(0.99, 0.02, "model, not measured", transform=ax.transAxes, ha="right",
        fontsize=7, color=GRAY, style="italic")
clean(ax)
save(fig, P("fig-08-03-matmul-model.png"))
# ------------------------------------------------ 8.4 parallel scan (schematic)
fig, ax = canvas(FIG_W, 1.9)
vals = [3, 1, 2, 4, 1, 1, 5, 2, 2, 3, 1, 4]
def row(y, nums, label, colors=None):
    ax.text(0.05, y + 0.1, label, fontsize=6.6, va="center", color=INK)
    for k, n_ in enumerate(nums):
        t = k // 3
        box(ax, 1.35 + k * 0.26, y, 0.23, 0.2, str(n_),
            fc=THREAD[t] if colors is None else colors[k], ec="none",
            tc=WHITE if (colors is None and t < 3) else INK, fs=6.3, r=0.02)
row(1.6, vals, "input")
loc, s_ = [], 0
for k, n_ in enumerate(vals):
    s_ = n_ if k % 3 == 0 else s_ + n_
    loc.append(s_)
row(1.15, loc, "1: each thread scans\n    its own block")
tot = [loc[2], loc[5], loc[8], loc[11]]
offs = [0, tot[0], tot[0] + tot[1], tot[0] + tot[1] + tot[2]]
for t in range(4):
    box(ax, 1.35 + (3 * t + 1) * 0.26, 0.72, 0.23, 0.2, str(offs[t]), fc=AMBER,
        ec="none", tc=INK, fs=6.3, r=0.02)
ax.text(0.05, 0.82, "2: one thread scans\n    the block totals", fontsize=6.6,
        va="center", color=INK)
fin = [loc[k] + offs[k // 3] for k in range(12)]
row(0.25, fin, "3: each thread adds\n    its offset")
for k in range(12):
    pass
save(fig, P("fig-08-04-scan.png"))

print("figures written to", OUT)
