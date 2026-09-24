"""figs_ch19.py -- figures for Chapter 19, Choosing the Right Tool.

Usage: python3 kit/figs_ch19.py OUTDIR
Figure 19.1 draws the costs collected in data/ch19/costs.json: measured on
the book's test machine, published, or assumed in an earlier model.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

banner(P("fig-19-00-banner.png"), seed=133, mode="rise")

# ------------------------------------------------ 19.2 decision guide (schematic)
fig, ax = canvas(FIG_W, 3.1)
def q(x, y, w, t):
    box(ax, x, y, w, 0.34, t, fc=PAPER, ec=GRAY, fs=6.0, r=0.03)
def a_(x, y, w, t, c=BLUE, tc=WHITE):
    box(ax, x, y, w, 0.34, t, fc=c, ec="none", tc=tc, fs=6.0, r=0.03)
def right(y, lab):
    arrow(ax, 1.77, y, 2.13, y, color=GRAY, ms=5)
    ax.text(1.95, y + 0.04, lab, fontsize=5.6, color=GRAY, ha="center", va="bottom")
def down(y, lab):
    arrow(ax, 0.85, y, 0.85, y - 0.16, color=GRAY, ms=5)
    ax.text(0.9, y - 0.09, lab, fontsize=5.6, color=GRAY, va="center")
ys = [2.7, 2.18, 1.66, 1.14, 0.62]
q(0.05, ys[0], 1.7, "Have you profiled it?")
a_(2.15, ys[0], 2.4, "Measure first: where, and bound by what? (Ch. 3, 5)", INK)
right(ys[0] + 0.17, "no"); down(ys[0], "yes")
q(0.05, ys[1], 1.7, "Is there a better algorithm\nor a tuned library?")
a_(2.15, ys[1], 2.4, "Use it: BLAS, cuBLAS, etcd... (Ch. 13–15, 18)", TEALD)
right(ys[1] + 0.17, "yes"); down(ys[1], "no")
q(0.05, ys[2], 1.7, "Is one core's SIMD or\ncache use poor?")
a_(2.15, ys[2], 2.4, "Vectorize; fix layout and tiling (Ch. 5–6)")
right(ys[2] + 0.17, "yes"); down(ys[2], "no, or fixed")
q(0.05, ys[3], 1.7, "Is one machine's memory\nand speed enough?")
a_(2.15, ys[3], 1.15, "threads, OpenMP\n(Ch. 7–8)")
a_(3.4, ys[3], 1.15, "or a GPU, if data-\nparallel (Ch. 14)", ORANGE)
right(ys[3] + 0.17, "yes"); down(ys[3], "no")
q(0.05, ys[4], 1.7, "Must the pieces communicate\noften (tightly coupled)?")
a_(2.15, ys[4], 1.15, "yes: cluster, MPI\n+ OpenMP (Ch. 10–12)")
a_(3.4, ys[4], 1.15, "no: task queue,\ncloud (Ch. 11, 16–18)", AMBER, INK)
right(ys[4] + 0.17, "")
ax.text(0.05, 0.22, "And if several machines must agree despite failures,", fontsize=6.2, color=INK)
ax.text(0.05, 0.08, "use a consensus service rather than your own (Ch. 16–18).", fontsize=6.2, color=INK)
save(fig, P("fig-19-02-guide.png"))

# ------------------------------------------------ 19.1 cost ladder (collected)
rows = json.load(open(os.path.join(ROOT, "data", "ch19", "costs.json")))
fig, ax = plt.subplots(figsize=(FIG_W, 2.9), layout="constrained")
col = {"measured": BLUE, "published": PURPLE, "assumed": LIGHT}
y = np.arange(len(rows))[::-1]
for yi, r in zip(y, rows):
    ax.barh(yi, r["seconds"], color=col[r["source"]], edgecolor=GRAY if r["source"] == "assumed" else "none",
            lw=0.5, hatch="///" if r["source"] == "assumed" else None, height=0.7)
    ax.text(r["seconds"] * 1.25, yi, f"Ch. {r['chapter']}", va="center", fontsize=5.8, color=GRAY)
ax.set_yticks(y, [r["label"] for r in rows], fontsize=6.6)
ax.set_xscale("log")
ax.set_xlim(1e-9, 1)
ax.set_xticks([1e-9, 1e-6, 1e-3, 1], ["1 ns", "1 µs", "1 ms", "1 s"])
ax.set_xlabel("Time (log scale)")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(fc=BLUE, label="measured on our test machine"),
                   Patch(fc=PURPLE, label="published measurement"),
                   Patch(fc=LIGHT, ec=GRAY, hatch="///", label="assumed in a model")],
          loc="upper right", frameon=False, fontsize=6.5)
ax.grid(True, axis="x")
clean(ax)
save(fig, P("fig-19-01-costs.png"))
print("figures written to", OUT)
