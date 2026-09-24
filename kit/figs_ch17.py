"""figs_ch17.py -- figures for Chapter 17, Mutual Exclusion, Deadlock and Failure.

Usage: python3 kit/figs_ch17.py OUTDIR
Figures 17.2 and 17.4 plot REAL runs from the chapter's kit.
"""
import sys, os, csv, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch17")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

banner(P("fig-17-00-banner.png"), seed=119, mode="blocks")

# ------------------------------------------------ 17.1 three algorithms (schematic)
fig, ax = canvas(FIG_W, 1.9)
def node(x, y, t, c=BLUE, tc=WHITE):
    ax.add_patch(Circle((x, y), 0.14, fc=c, ec="none", zorder=3))
    ax.text(x, y, t, ha="center", va="center", fontsize=6.3, color=tc, zorder=4)
ax.text(0.05, 1.85, "(a) Central coordinator", fontsize=7.2, weight="bold", va="top")
node(0.75, 1.15, "C", INK)
for k, (x, y) in enumerate(((0.25, 0.45), (0.75, 0.35), (1.25, 0.45))):
    node(x, y, f"P{k + 1}")
arrow(ax, 0.3, 0.6, 0.63, 1.03, color=ORANGE, ms=5)
ax.text(0.05, 0.8, "request", fontsize=5.8, color=ORANGE, ha="left")
arrow(ax, 0.87, 1.03, 1.2, 0.6, color=TEALD, ms=5)
ax.text(1.12, 0.9, "grant", fontsize=5.8, color=TEALD)
ax.text(0.75, 0.1, "3 messages per entry", fontsize=6.2, color=GRAY, ha="center")
line(ax, [1.6, 1.6], [0.05, 1.8], color=LIGHT, lw=0.8)
ax.text(1.7, 1.85, "(b) Ricart–Agrawala", fontsize=7.2, weight="bold", va="top")
pts = [(2.0, 1.15), (2.85, 1.15), (2.0, 0.45), (2.85, 0.45)]
for k, (x, y) in enumerate(pts):
    node(x, y, f"P{k}")
for k in (1, 2, 3):
    x2, y2 = pts[k]
    arrow(ax, 2.0 + (x2 - 2.0) * 0.18, 1.15 + (y2 - 1.15) * 0.18,
          2.0 + (x2 - 2.0) * 0.8, 1.15 + (y2 - 1.15) * 0.8, color=ORANGE, ms=5)
ax.text(2.42, 0.1, "request to all, wait for all replies:\n2(n − 1) messages", fontsize=6.2,
        color=GRAY, ha="center", linespacing=1.1)
line(ax, [3.2, 3.2], [0.05, 1.8], color=LIGHT, lw=0.8)
ax.text(3.3, 1.85, "(c) Token ring", fontsize=7.2, weight="bold", va="top")
cx, cy, r = 3.95, 0.85, 0.42
for k in range(5):
    th = np.pi / 2 - 2 * np.pi * k / 5
    node(cx + r * np.cos(th), cy + r * np.sin(th), f"P{k}", AMBER if k == 0 else BLUE,
         INK if k == 0 else WHITE)
ax.add_patch(Arc((cx, cy), 2 * r, 2 * r, theta1=-30, theta2=250, color=GRAY, lw=0.8))
ax.text(cx, 0.1, "the token holder\n(amber) may enter", fontsize=6.2, color=GRAY, ha="center",
        linespacing=1.1)
save(fig, P("fig-17-01-algorithms.png"))

# ------------------------------------------------ 17.2 messages per entry (REAL)
mx = list(csv.DictReader(open(os.path.join(DATA, "mutex.csv"))))
ps = [2, 4, 6]
fig, ax = plt.subplots(figsize=(FIG_W, 1.9), layout="constrained")
w = 0.26
for i, (mode, lab, c, h) in enumerate((("central", "central coordinator", INK, None),
                                       ("ra", "Ricart–Agrawala", BLUE, "///"),
                                       ("token", "token ring (busy)", AMBER, None))):
    vals = [float(next(r["msgs_per_entry"] for r in mx if r["mode"] == mode
                       and r["processes"] == str(p))) for p in ps]
    ax.bar(np.arange(3) + (i - 1) * w, vals, width=w - 0.02, color=c, hatch=h,
           edgecolor=WHITE, lw=0.3, label=lab)
ax.scatter(np.arange(3), [2 * (p - 1) for p in ps], marker="_", s=260, color=ORANGE,
           zorder=4, label="2(n − 1)")
ax.set_xticks(range(3), [f"{p} processes" for p in ps])
ax.set_ylabel("Messages per entry")
ax.grid(True, axis="y")
ax.legend(loc="upper left", frameon=False, fontsize=6.6)
clean(ax)
save(fig, P("fig-17-02-messages.png"))

# ------------------------------------------------ 17.3 wait-for graph (schematic)
fig, ax = canvas(FIG_W, 1.55)
pos = {0: (1.4, 1.2), 1: (2.3, 1.2), 2: (1.85, 0.45), 3: (3.9, 1.2), 4: (3.1, 1.2), 5: (3.5, 0.45)}
edges = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 1)]
for a_, b_ in edges:
    (x1, y1), (x2, y2) = pos[a_], pos[b_]
    d = np.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    incycle = (a_, b_) in ((0, 1), (1, 2), (2, 0))
    arrow(ax, x1 + ux * 0.16, y1 + uy * 0.16, x2 - ux * 0.17, y2 - uy * 0.17,
          color=ORANGE if incycle else GRAY, ms=6)
for k, (x, y) in pos.items():
    node(x, y, f"P{k}", ORANGE if k in (0, 1, 2) else (LIGHT if k == 5 else BLUE),
         WHITE if k != 5 else INK)
ax.text(0.05, 1.45, "An arrow means \"waits for\".", fontsize=6.6, va="top")
ax.text(0.05, 1.28, "Orange: the cycle (deadlock).", fontsize=6.6, va="top", color=ORANGE)
ax.text(0.05, 1.11, "P3 and P4 wait on it but are\nnot in it; P5 isn't waiting.", fontsize=6.6,
        va="top", color=GRAY, linespacing=1.1)
save(fig, P("fig-17-03-waitfor.png"))

# ------------------------------------------------ 17.4 detector trade-off (REAL)
hb = open(os.path.join(DATA, "heartbeat.txt")).read()
pts_ = [(int(m.group(1)), int(m.group(2)), float(m.group(3)))
        for m in re.finditer(r"^(\d+),(\d+),([\d.]+)$", hb, flags=re.M)]
fig, ax = plt.subplots(figsize=(FIG_W, 1.95), layout="constrained")
ax.plot([p[2] for p in pts_], [p[1] for p in pts_], color=BLUE, marker="o", ms=4, lw=1.2)
for to, fa, det in pts_:
    ax.annotate(f"{to} ms", (det, fa), textcoords="offset points", xytext=(4, 4),
                fontsize=6.3, color=GRAY)
ax.set_xlabel("Time to detect the real crash (ms)")
ax.set_ylabel("False suspicions\n(400 heartbeats)")
ax.set_ylim(-0.5, 11)
ax.grid(True)
ax.text(0.99, 0.95, "labels: timeout", transform=ax.transAxes, ha="right", va="top",
        fontsize=6.5, color=GRAY, style="italic")
clean(ax)
save(fig, P("fig-17-04-detector.png"))

# ------------------------------------------------ 17.5 lease and fencing (schematic)
fig, ax = canvas(FIG_W, 1.75)
rows_ = {"lock service": 1.5, "client A": 1.1, "client B": 0.7, "storage": 0.3}
for lab, y in rows_.items():
    ax.text(0.05, y, lab, fontsize=6.6, va="center")
    line(ax, [0.8, 4.55], [y, y], color=LIGHT, lw=0.8)
ax.add_patch(Rectangle((0.9, 1.44), 1.2, 0.12, fc=BLUE, ec="none"))
ax.text(1.5, 1.62, "A's lease (token 33)", fontsize=6, ha="center", color=BLUE)
ax.add_patch(Rectangle((2.15, 1.44), 1.3, 0.12, fc=TEALD, ec="none"))
ax.text(2.8, 1.62, "B's lease (token 34)", fontsize=6, ha="center", color=TEALD)
ax.add_patch(Rectangle((1.05, 1.04), 2.2, 0.12, fc=LIGHT, ec=GRAY, lw=0.5, hatch="///"))
ax.text(2.15, 0.93, "A pauses (garbage collection)", fontsize=6, ha="center", color=GRAY)
arrow(ax, 2.3, 0.7, 2.45, 0.35, color=TEALD, ms=5)
ax.text(2.55, 0.5, "write, token 34: ok", fontsize=6, color=TEALD)
arrow(ax, 3.3, 1.1, 3.55, 0.35, color=ORANGE, ms=5)
ax.text(3.62, 0.5, "write, token 33:\nrejected", fontsize=6, color=ORANGE, linespacing=1.05)
ax.text(0.8, 0.05, "Without the token check, the storage would accept A's stale write.",
        fontsize=6.4, color=INK)
save(fig, P("fig-17-05-fencing.png"))
print("figures written to", OUT)
