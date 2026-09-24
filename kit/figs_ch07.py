"""figs_ch07.py -- figures for Chapter 7, Threads with Pthreads.

Usage: python3 kit/figs_ch07.py OUTDIR
Figure 7.4 is a MODEL (kit/heatmodel.py) driven by measured one-core rates.
"""
import sys, os, csv, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import heatmodel as hm
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch07")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

# ------------------------------------------------ 7.0 banner (Part II)
banner(P("fig-07-00-banner.png"), seed=49, mode="wave")

# ------------------------------------------------ 7.1 create and join (schematic)
fig, ax = canvas(FIG_W, 1.55)
y_main = 1.25
line(ax, [0.5, 4.4], [y_main, y_main], color=INK, lw=2)
ax.text(0.45, y_main, "main", ha="right", va="center", fontsize=7, weight="bold")
for k, (start, end, c) in enumerate([(0.9, 3.1, BLUE), (1.05, 2.6, TEALD),
                                     (1.2, 3.5, ORANGE)]):
    y = 0.95 - k * 0.3
    ax.text(0.45, y, f"thread {k + 1}", ha="right", va="center", fontsize=7)
    arrow(ax, start, y_main - 0.03, start, y + 0.05, color=GRAY, lw=0.8, ms=5)
    line(ax, [start, end], [y, y], color=c, lw=3)
    arrow(ax, end, y + 0.05, 3.62, y_main - 0.03, color=GRAY, lw=0.7, ms=5)
ax.text(1.05, 1.42, "pthread_create × 3", ha="center", fontsize=6.8,
        color=GRAY, family=MONO)
ax.text(3.62, 1.42, "pthread_join × 3", ha="center", fontsize=6.8,
        color=GRAY, family=MONO)
ax.add_patch(Rectangle((1.3, y_main - 0.05), 2.3, 0.1, fc=PAPER, ec="none", zorder=3))
ax.text(2.45, y_main, "main waits", ha="center", va="center", fontsize=6.5,
        color=GRAY, zorder=4)
ax.text(4.35, 0.05, "time →", ha="right", fontsize=6.8, color=GRAY)
save(fig, P("fig-07-01-create-join.png"))

# ------------------------------------------------ 7.2 lost update (schematic)
fig, ax = canvas(FIG_W, 1.6)
steps = [("A", "load: 41", 0), ("B", "load: 41", 1),
         ("A", "add: 42", 2), ("B", "add: 42", 3),
         ("A", "store 42", 4), ("B", "store 42", 5)]
for who, txt, t in steps:
    y = 1.05 if who == "A" else 0.55
    box(ax, 0.75 + t * 0.62, y, 0.58, 0.3, txt, fc=BLUE if who == "A" else ORANGE,
        ec="none", tc=WHITE, fs=6, r=0.03)
ax.text(0.65, 1.2, "thread A", ha="right", va="center", fontsize=7, weight="bold")
ax.text(0.65, 0.7, "thread B", ha="right", va="center", fontsize=7, weight="bold")
ax.text(0.75, 0.25, "Two increments, but the counter went from 41 to 42: "
        "B's update overwrote A's.", fontsize=6.8, color=INK)
ax.text(0.75, 0.08, "time →", fontsize=6.5, color=GRAY)
save(fig, P("fig-07-02-race.png"))

# ------------------------------------------------ 7.3 decomposition + barrier (schematic)
fig, ax = canvas(FIG_W, 1.95)
cols = [BLUE, TEALD, ORANGE, AMBER]
gx, gy, gw, gh = 0.15, 0.3, 1.25, 1.4
ax.add_patch(Rectangle((gx, gy + gh - 0.06), gw, 0.06, fc=INK, ec="none"))
ax.add_patch(Rectangle((gx, gy), gw, 0.06, fc=LIGHT, ec="none"))
band = (gh - 0.12) / 4
for k in range(4):
    y = gy + gh - 0.06 - (k + 1) * band
    ax.add_patch(Rectangle((gx, y), gw, band - 0.02, fc=cols[k], ec="none", alpha=0.85))
    ax.text(gx + gw / 2, y + band / 2, f"thread {k + 1}: rows", ha="center",
            va="center", fontsize=6.5, color=WHITE if k < 3 else INK, weight="bold")
ax.text(gx + gw / 2, gy - 0.08, "grid (edges fixed)", ha="center", va="top",
        fontsize=6.5, color=GRAY)
tx = 1.9
work = [[0.55, 0.62, 0.5, 0.58], [0.6, 0.5, 0.57, 0.52]]
x = tx
for s_, w in enumerate(work):
    for k in range(4):
        y = 1.45 - k * 0.3
        ax.add_patch(Rectangle((x, y), w[k], 0.2, fc=cols[k], ec="none"))
        ax.add_patch(Rectangle((x + w[k], y), max(w) - w[k], 0.2, fc=PAPER,
                               ec=LIGHT, lw=0.5, hatch="////"))
    x += max(w)
    line(ax, [x + 0.03, x + 0.03], [0.4, 1.72], color=INK, lw=1.2, ls="--")
    ax.text(x + 0.03, 1.78, "barrier", ha="center", fontsize=6.5, color=INK)
    ax.text(x - max(w) / 2, 0.3, f"step {s_ + 1}", ha="center", fontsize=6.5,
            color=GRAY)
    x += 0.08
ax.text(tx, 0.12, "hatched: waiting at the barrier for the slowest thread",
        fontsize=6.5, color=GRAY)
save(fig, P("fig-07-03-decomposition.png"))

# ------------------------------------------------ 7.4 predicted speedup (MODEL)
rate = {}
for r in csv.DictReader(open(os.path.join(DATA, "rates.csv"))):
    rate.setdefault((r["version"], int(r["n"])), []).append(float(r["mlups"]))
rate = {k: st.median(x) * 1e6 for k, x in rate.items()}
R = {"l2": rate[("v4", 256)], "l3": rate[("v4", 1024)], "mem": rate[("v4", 4096)]}
ps = np.arange(1, 17)
fig, ax = plt.subplots(figsize=(FIG_W, 2.1), layout="constrained")
ax.plot(ps, ps, color=GRAY, lw=0.9, ls=":", label="ideal: speedup = p")
for n, c, mk, ls in [(1024, TEALD, "s", "-"), (256, BLUE, "o", "--"),
                     (4096, ORANGE, "^", "-.")]:
    ax.plot(ps, [hm.speedup(n, int(p), R, rate[("v1", n)]) for p in ps], color=c,
            marker=mk, ms=3.5, lw=1.2, ls=ls, label=f"{n:,} × {n:,} grid")
ax.set_xlim(0.5, 16.5)
ax.set_xticks([1, 2, 4, 8, 12, 16])
ax.set_ylim(0, 34)
ax.set_xlabel("Cores p, one thread per core")
ax.set_ylabel("Predicted speedup over v1")
ax.grid(True, axis="y")
ax.legend(loc="upper left", frameon=False, fontsize=7)
ax.text(0.99, 0.02, "model, not measured", transform=ax.transAxes, ha="right",
        fontsize=7, color=GRAY, style="italic")
clean(ax)
save(fig, P("fig-07-04-model.png"))

# ------------------------------------------------ 7.5 false sharing (schematic)
fig, ax = canvas(FIG_W, 1.7)
def core_cache(x, label, line_cells, highlight):
    box(ax, x, 1.3, 0.9, 0.26, label, fc=INK, ec="none", tc=WHITE, fs=7,
        weight="bold", r=0.03)
    for k in range(8):
        fc = ORANGE if k == highlight else (BLUE if k in line_cells else LIGHT)
        ax.add_patch(Rectangle((x + k * 0.112, 0.95), 0.1, 0.2, fc=fc, ec="none"))
    ax.text(x + 0.45, 0.88, "one 64-byte line in its cache", ha="center",
            va="top", fontsize=6.2, color=GRAY)
ax.text(0.05, 1.68, "(a) Packed counters: one line, two cores", fontsize=7.5,
        weight="bold", va="top")
core_cache(0.1, "core 1", [0, 1], 0)
core_cache(1.2, "core 2", [0, 1], 1)
arrow(ax, 1.02, 1.05, 1.18, 1.05, color=ORANGE, lw=1.3, style="<|-|>", ms=6)
ax.text(1.1, 0.55, "each write invalidates the\nother core's copy: the line\n"
        "ping-pongs between caches", ha="center", fontsize=6.4, color=ORANGE,
        va="top", linespacing=1.1)
line(ax, [2.3, 2.3], [0.1, 1.62], color=LIGHT, lw=0.8)
ax.text(2.45, 1.68, "(b) Padded counters: a line each", fontsize=7.5,
        weight="bold", va="top")
core_cache(2.5, "core 1", [0], 0)
core_cache(3.6, "core 2", [0], 0)
ax.text(3.55, 0.55, "each core keeps its own line;\nno invalidations", ha="center",
        fontsize=6.4, color=TEALD, va="top", linespacing=1.1)
save(fig, P("fig-07-05-false-sharing.png"))
# ------------------------------------------------ 7.6 bounded queue (schematic)
fig, ax = canvas(FIG_W, 1.5)
box(ax, 0.05, 0.62, 0.78, 0.36, "producer", fc=BLUE, ec="none", tc=WHITE, fs=7,
    weight="bold")
cells, cx0, cw_ = 10, 1.1, 0.2
filled = {3, 4, 5, 6, 7}                   # items waiting; the oldest is at the right
for k in range(cells):
    ax.add_patch(Rectangle((cx0 + k * cw_, 0.65), cw_ - 0.02, 0.3,
                 fc=AMBER if k in filled else PAPER, ec=GRAY, lw=0.5))
arrow(ax, 0.85, 0.8, cx0 + 3 * cw_ - 0.03, 0.8, color=BLUE, lw=1.0, ms=6)
ax.text(cx0 + 2 * cw_ + cw_ / 2, 1.0, "tail", ha="center", fontsize=6.3, color=BLUE)
ax.text(cx0 + 7 * cw_ + cw_ / 2, 1.0, "head", ha="center", fontsize=6.3, color=TEALD)
ax.text(0.05, 0.42, "put: waits while the queue\nis full (not_full)", fontsize=6.3,
        color=BLUE, linespacing=1.05)
ax.text(cx0 + 5 * cw_, 0.5, "5 of 10 slots in use", ha="center", fontsize=6.3,
        color=GRAY)
for k in range(3):
    y = 1.1 - k * 0.42
    box(ax, 3.75, y, 0.8, 0.3, f"consumer {k + 1}", fc=TEALD, ec="none", tc=WHITE,
        fs=6.6, r=0.03)
    arrow(ax, cx0 + 8 * cw_, 0.8, 3.73, y + 0.15, color=TEALD, lw=0.8, ms=5)
ax.text(3.75, 0.1, "take: waits while empty\n(not_empty)", fontsize=6.3,
        color=TEALD, linespacing=1.05)
ax.text(1.1, 0.2, "one mutex guards the slots and counts", fontsize=6.3, color=GRAY)
save(fig, P("fig-07-06-queue.png"))

print("figures written to", OUT)
