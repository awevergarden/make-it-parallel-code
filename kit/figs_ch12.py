"""figs_ch12.py -- figures for Chapter 12, Modeling Distributed Performance.

Usage: python3 kit/figs_ch12.py OUTDIR
Figure 12.2 plots REAL halo-byte counts from HeatSim v7 with the formulas;
Figures 12.3 and 12.4 are MODELS (kit/scalemodel.py).
"""
import sys, os, csv, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import scalemodel as sm
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch12")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)
rows_ = lambda n: list(csv.DictReader(open(os.path.join(DATA, n))))

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

banner(P("fig-12-00-banner.png"), seed=84, mode="blocks")

# ------------------------------------------------ 12.1 rows vs squares (schematic)
fig, ax = canvas(FIG_W, 1.95)
cols4 = [INK, BLUE, ORANGE, TEAL]
S = 1.3
def panel(x0, title, blocks, note):
    ax.text(x0, 1.9, title, fontsize=7.5, weight="bold", va="top")
    for (bx, by, bw, bh, c) in blocks:
        ax.add_patch(Rectangle((x0 + bx * S, 0.35 + by * S), bw * S - 0.03,
                     bh * S - 0.03, fc=c, ec="none", alpha=0.85))
    ax.text(x0, 0.17, note, fontsize=6.4, color=GRAY, va="center")
panel(0.05, "(a) 4 row strips", [(0, 0.75 - k * 0.25, 1, 0.25, cols4[k]) for k in range(4)],
      "each sends 2 rows of n values")
line(ax, [2.3, 2.3], [0.1, 1.85], color=LIGHT, lw=0.8)
panel(2.45, "(b) 2 × 2 square blocks",
      [(0, 0.5, 0.5, 0.5, cols4[0]), (0.5, 0.5, 0.5, 0.5, cols4[1]),
       (0, 0, 0.5, 0.5, cols4[2]), (0.5, 0, 0.5, 0.5, cols4[3])],
      "each sends a half-row and a half-column")
ax.add_patch(Rectangle((0.05, 0.35 + S * 0.5 - 0.025), S - 0.03, 0.04, fc=AMBER, ec="none"))
ax.text(0.05 + S + 0.06, 0.35 + S * 0.5, "cut:\nn values", fontsize=6.3, va="center",
        linespacing=1.05)
ax.add_patch(Rectangle((2.45 + S * 0.5 - 0.035, 0.35), 0.04, S - 0.03, fc=AMBER, ec="none"))
ax.add_patch(Rectangle((2.45, 0.35 + S * 0.5 - 0.035), S - 0.03, 0.04, fc=AMBER, ec="none"))
ax.text(2.45 + S + 0.06, 0.35 + S * 0.5, "each cut:\nn/2 values\nper block", fontsize=6.3,
        va="center", linespacing=1.05)
save(fig, P("fig-12-01-decomposition.png"))

# ------------------------------------------------ 12.2 halo bytes per process (REAL)
h = rows_("halo.csv")
fig, ax = plt.subplots(figsize=(FIG_W, 2.1), layout="constrained")
ps = [int(r["processes"]) for r in h if r["layout"] == "rows" and int(r["processes"]) > 1]
for layout, c, mk in (("rows", ORANGE, "^"), ("squares", BLUE, "o")):
    pts = [(int(r["processes"]), int(r["max_bytes"])) for r in h
           if r["layout"] == layout and int(r["processes"]) > 1]
    ax.scatter([p for p, _ in pts], [b / 1024 for _, b in pts], color=c, marker=mk, s=22,
               zorder=3, label=f"{layout}: measured")
xs = [2, 4, 8, 16, 32, 64]
ax.plot(xs, [sm.halo_bytes(1024, p, "rows") / 1024 for p in xs], color=ORANGE, lw=0.9,
        ls="--", label="rows: formula")
ax.plot(xs, [sm.halo_bytes(1024, p, "squares") / 1024 for p in xs], color=BLUE, lw=0.9,
        ls="--", label="squares: formula")
ax.set_xscale("log", base=2)
ax.set_xticks(ps, [str(p) for p in ps])
ax.set_ylim(0, 19)
ax.set_xlabel("Processes")
ax.set_ylabel("Halo KB sent per step\n(busiest process)")
ax.grid(True, axis="y")
ax.legend(loc="lower left", frameon=False, fontsize=6.6, ncol=2)
clean(ax)
save(fig, P("fig-12-02-halo-bytes.png"))

# ------------------------------------------------ 12.3 communication share (MODEL)
rt = {}
for r in rows_("rates.csv"):
    rt.setdefault(int(r["n"]), []).append(float(r["mlups"]))
R = {"l2": st.median(rt[256]) * 1e6, "l3": st.median(rt[1024]) * 1e6,
     "mem": st.median(rt[4096]) * 1e6}
pp = 2 ** np.arange(1, 13)
fig, ax = plt.subplots(figsize=(FIG_W, 2.2), layout="constrained")
for n, layout, c, mk, ls in ((4096, "rows", ORANGE, "^", "--"), (4096, "squares", ORANGE, "o", "-"),
                             (16384, "rows", BLUE, "^", "--"), (16384, "squares", BLUE, "o", "-")):
    ax.plot(pp, [sm.comm(n, int(p), layout) / sm.step_time(n, int(p), R, layout) * 100
                 for p in pp], color=c, marker=mk, ms=3.3, lw=1.1, ls=ls,
            label=f"{n:,} grid, {layout}")
ax.set_xscale("log", base=2)
ax.set_xticks([2, 8, 32, 128, 512, 2048], ["2", "8", "32", "128", "512", "2,048"])
ax.set_ylim(0, 100)
ax.set_xlabel("Nodes, one process each (log scale)")
ax.set_ylabel("Share of each step\nspent communicating (%)")
ax.grid(True, axis="y")
ax.legend(loc="upper left", frameon=False, fontsize=6.8)
ax.text(0.99, 0.97, "model, not measured", transform=ax.transAxes, ha="right",
        va="top", fontsize=7, color=GRAY, style="italic")
clean(ax)
save(fig, P("fig-12-03-comm-share.png"))

# ------------------------------------------------ 12.4 weak scaling (MODEL)
fig, ax = plt.subplots(figsize=(FIG_W, 1.9), layout="constrained")
pp4 = 4 ** np.arange(0, 7)
for layout, c, mk, ls in (("rows", ORANGE, "^", "--"), ("squares", BLUE, "o", "-")):
    ax.plot(pp4, [sm.weak_efficiency(1024, int(p), R, layout) * 100 for p in pp4],
            color=c, marker=mk, ms=3.5, lw=1.2, ls=ls, label=layout)
ax.set_xscale("log", base=4)
ax.set_xticks(pp4, [f"{int(p):,}" for p in pp4])
ax.set_ylim(80, 101)
ax.set_xlabel("Nodes, each holding a 1,024 × 1,024 block (log scale)")
ax.set_ylabel("Weak-scaling\nefficiency (%)")
ax.grid(True, axis="y")
ax.legend(loc="lower left", frameon=False, fontsize=7)
ax.text(0.99, 0.05, "model, not measured", transform=ax.transAxes, ha="right",
        fontsize=7, color=GRAY, style="italic")
clean(ax)
save(fig, P("fig-12-04-weak.png"))
print("figures written to", OUT)
