"""figs_ch09.py -- figures for Chapter 9, How Processes Communicate.

Usage: python3 kit/figs_ch09.py OUTDIR
Figure 9.4 plots real local ping-pong times with the fitted alpha-beta model.
"""
import sys, os, csv, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch09")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)
VALS = json.load(open(os.path.join(DATA, "values.json")))

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

# ------------------------------------------------ 9.0 banner (Part III)
banner(P("fig-09-00-banner.png"), seed=63, mode="blocks")

# ------------------------------------------------ 9.1 threads vs processes (schematic)
fig, ax = canvas(FIG_W, 1.75)
ax.text(0.05, 1.7, "(a) Threads: one address space", fontsize=7.5,
        weight="bold", va="top")
box(ax, 0.1, 0.25, 2.0, 1.2, fc=PAPER, ec=GRAY, r=0.05, z=0)
box(ax, 0.25, 0.4, 1.7, 0.4, "shared heap and globals", fc=AMBER, ec="none",
    fs=6.8, r=0.03)
for k in range(3):
    box(ax, 0.25 + k * 0.58, 0.95, 0.5, 0.35, f"thread {k + 1}\nstack", fc=BLUE,
        ec="none", tc=WHITE, fs=6.2, r=0.03)
ax.text(0.1, 0.12, "communicate by reading and writing memory", fontsize=6.5,
        color=GRAY)
line(ax, [2.3, 2.3], [0.1, 1.6], color=LIGHT, lw=0.8)
ax.text(2.45, 1.7, "(b) Processes: separate address spaces", fontsize=7.5,
        weight="bold", va="top")
for k, x in enumerate((2.5, 3.6)):
    box(ax, x, 0.25, 0.95, 1.2, fc=PAPER, ec=GRAY, r=0.05, z=0)
    box(ax, x + 0.1, 0.4, 0.75, 0.4, "own heap", fc=AMBER, ec="none", fs=6.5, r=0.03)
    box(ax, x + 0.1, 0.95, 0.75, 0.35, f"process {k + 1}", fc=TEALD, ec="none",
        tc=WHITE, fs=6.5, r=0.03)
arrow(ax, 3.47, 0.85, 3.63, 0.85, color=ORANGE, lw=1.4, style="<|-|>", ms=6)
ax.text(3.55, 0.12, "communicate by sending messages", fontsize=6.5,
        color=ORANGE, ha="center")
save(fig, P("fig-09-01-processes.png"))

# ------------------------------------------------ 9.2 three channels (schematic)
fig, ax = canvas(FIG_W, 1.6)
cols = [(0.05, "(a) Pipe"), (1.6, "(b) Shared memory"), (3.15, "(c) Socket")]
for x, t in cols:
    ax.text(x, 1.57, t, fontsize=7.5, weight="bold", va="top")
    box(ax, x + 0.05, 1.0, 0.55, 0.3, "P1", fc=TEALD, ec="none", tc=WHITE, fs=6.8)
    box(ax, x + 0.8, 1.0, 0.55, 0.3, "P2", fc=TEALD, ec="none", tc=WHITE, fs=6.8)
# pipe: through a kernel buffer
box(ax, 0.3, 0.35, 0.85, 0.32, "kernel buffer\n(64 KB)", fc=LIGHT, ec="none", fs=6.2)
arrow(ax, 0.33, 0.98, 0.5, 0.69, color=GRAY, ms=5)
arrow(ax, 0.95, 0.69, 1.12, 0.98, color=GRAY, ms=5)
ax.text(0.05, 0.12, "copy in, copy out", fontsize=6.4, color=GRAY)
# shared memory: one region mapped into both
box(ax, 1.85, 0.35, 0.85, 0.32, "shared region", fc=AMBER, ec="none", fs=6.4)
line(ax, [1.93, 2.1], [0.99, 0.68], color=GRAY)
line(ax, [2.68, 2.5], [0.99, 0.68], color=GRAY)
ax.text(1.6, 0.12, "no copy; needs synchronization", fontsize=6.4, color=GRAY)
# socket: through the network stack, possibly another machine
box(ax, 3.3, 0.35, 1.1, 0.32, "network stack\n(any machine)", fc=BLUE, ec="none",
    tc=WHITE, fs=6.2)
arrow(ax, 3.48, 0.98, 3.6, 0.69, color=GRAY, ms=5)
arrow(ax, 4.1, 0.69, 4.23, 0.98, color=GRAY, ms=5)
ax.text(3.15, 0.12, "works across a network", fontsize=6.4, color=GRAY)
save(fig, P("fig-09-02-channels.png"))

# ------------------------------------------------ 9.3 deadlock (schematic)
fig, ax = canvas(FIG_W, 1.45)
box(ax, 0.2, 0.55, 0.9, 0.4, "parent\nblocked in write", fc=TEALD, ec="none",
    tc=WHITE, fs=6.6)
box(ax, 3.5, 0.55, 0.9, 0.4, "child\nblocked in write", fc=TEALD, ec="none",
    tc=WHITE, fs=6.6)
for y, lab, a1, a2 in [(1.12, "pipe to child: full (64 KB)", 1.1, 3.5),
                        (0.2, "pipe to parent: full (64 KB)", 3.5, 1.1)]:
    box(ax, 1.55, y - 0.1, 1.5, 0.22, lab, fc=ORANGE, ec="none", tc=WHITE, fs=6.2)
    arrow(ax, a1, 0.75 + (0.2 if y > 1 else -0.2), 1.53 if a1 < 2 else 3.07, y,
          color=GRAY, ms=5)
ax.text(2.3, 0.72, "each waits for the other\nto read: neither ever will",
        ha="center", fontsize=6.6, color=ORANGE, linespacing=1.1)
save(fig, P("fig-09-03-deadlock.png"))

# ------------------------------------------------ 9.4 ping-pong + alpha-beta fit (measured)
d = {}
for r in csv.DictReader(open(os.path.join(DATA, "pingpong.csv"))):
    d.setdefault((r["kind"], int(r["bytes"])), []).append(float(r["microseconds"]))
fig, ax = plt.subplots(figsize=(FIG_W, 2.35), layout="constrained")
xs = np.logspace(np.log10(6), np.log10(3e6), 100)
for k, lab, c, mk in [("pipe", "pipe", BLUE, "o"), ("unix", "Unix socket", TEALD, "s"),
                      ("tcp", "TCP loopback", ORANGE, "^")]:
    n = sorted(b for (kk, b) in d if kk == k)
    t = [st.median(d[(k, b)]) for b in n]
    ax.scatter(n, t, color=c, marker=mk, s=16, zorder=3, label=lab)
    al, be = float(VALS[f"a_{k}"]), float(VALS[f"b_{k}"]) * 1000
    ax.plot(xs, al + xs / be, color=c, lw=0.9, ls="--", zorder=2)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Message size (bytes, log scale)")
ax.set_ylabel("One-way time (µs, log scale)")
ax.grid(True, which="major")
ax.legend(loc="upper left", frameon=False, fontsize=7)
ax.text(0.99, 0.03, "points: measured; dashed: fitted model α + n/β",
        transform=ax.transAxes, ha="right", fontsize=6.6, color=GRAY)
clean(ax)
save(fig, P("fig-09-04-pingpong.png"))

# ------------------------------------------------ 9.5 collective patterns (schematic)
fig, ax = canvas(FIG_W, 1.65)
pats = [("Broadcast", ["A", "", "", ""], ["A", "A", "A", "A"]),
        ("Scatter", ["ABCD", "", "", ""], ["A", "B", "C", "D"]),
        ("Gather", ["A", "B", "C", "D"], ["ABCD", "", "", ""]),
        ("Reduce (+)", ["1", "2", "3", "4"], ["10", "", "", ""])]
for k, (name, before, after) in enumerate(pats):
    x0 = 0.05 + k * 1.14
    ax.text(x0 + 0.5, 1.6, name, ha="center", fontsize=7.5, weight="bold", va="top")
    for r in range(4):
        y = 1.2 - r * 0.28
        box(ax, x0, y, 0.42, 0.22, before[r], fc=BLUE if before[r] else PAPER,
            ec="none" if before[r] else LIGHT, tc=WHITE, fs=6.3, r=0.02)
        box(ax, x0 + 0.62, y, 0.42, 0.22, after[r], fc=ORANGE if after[r] else PAPER,
            ec="none" if after[r] else LIGHT, tc=WHITE, fs=6.3, r=0.02)
    arrow(ax, x0 + 0.45, 0.68, x0 + 0.6, 0.68, color=GRAY, ms=5)
ax.text(0.05, 0.05, "Rows are processes 0–3; left: before, right: after.",
        fontsize=6.5, color=GRAY)
save(fig, P("fig-09-05-collectives.png"))
print("figures written to", OUT)
