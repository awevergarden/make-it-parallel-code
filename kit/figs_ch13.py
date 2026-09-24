"""figs_ch13.py -- figures for Chapter 13, Matrix Multiplication and Partitioning.

Usage: python3 kit/figs_ch13.py OUTDIR
Figures 13.2 and 13.5 use real computed/counted data; 13.6 is a MODEL.
"""
import sys, os, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import mmdistmodel as mdm
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch13")
VALS = json.load(open(os.path.join(DATA, "values.json")))
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)
rows_ = lambda n: list(csv.DictReader(open(os.path.join(DATA, n))))
OWN = [INK, BLUE, ORANGE, TEAL]

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

banner(P("fig-13-00-banner.png"), seed=91, mode="blocks")

# ------------------------------------------------ 13.1 layouts (schematic)
fig, axs = plt.subplots(1, 3, figsize=(FIG_W, 1.7))
N = 8
layouts = [("(a) 1D block rows", lambda i, j: i // 2),
           ("(b) 2D blocks", lambda i, j: (i // 4) * 2 + j // 4),
           ("(c) 2D block-cyclic", lambda i, j: ((i // 2) % 2) * 2 + (j // 2) % 2)]
from matplotlib.colors import ListedColormap
for ax, (t, own) in zip(axs, layouts):
    g = np.array([[own(i, j) for j in range(N)] for i in range(N)])
    ax.imshow(g, cmap=ListedColormap(OWN), vmin=0, vmax=3)
    for k in range(1, N):
        ax.axhline(k - 0.5, color=WHITE, lw=0.4)
        ax.axvline(k - 0.5, color=WHITE, lw=0.4)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(t, fontsize=7.2, loc="left", pad=3)
    for s in ax.spines.values():
        s.set_visible(False)
fig.text(0.5, 0.02, "Processes 0–3: navy, blue, orange, teal", ha="center",
         fontsize=6.5, color=GRAY)
fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.1, wspace=0.12)
save(fig, P("fig-13-01-layouts.png"))

# ------------------------------------------------ 13.2 balance (computed)
bal = {}
for r in rows_("balance.csv"):
    bal.setdefault(r["layout"], []).append(int(r["updates"]))
fig, ax = plt.subplots(figsize=(FIG_W, 1.8), layout="constrained")
x = np.arange(4)
ax.bar(x - 0.2, bal["block"], width=0.38, color=ORANGE, label="2D block")
ax.bar(x + 0.2, bal["block-cyclic"], width=0.38, color=BLUE, hatch="///",
       edgecolor=WHITE, lw=0.3, label="2D block-cyclic (blocks of 4)")
ax.axhline(sum(bal["block"]) / 4, color=INK, lw=0.8, ls=":")
ax.text(-0.45, sum(bal["block"]) / 4 + 800, "average", fontsize=6.5, color=INK, ha="left")
ax.set_xticks(x, [f"process {k}" for k in range(4)])
ax.set_ylabel("Element updates")
ax.legend(loc="upper left", frameon=False, fontsize=7)
ax.grid(True, axis="y")
clean(ax)
save(fig, P("fig-13-02-balance.png"))

# ------------------------------------------------ 13.3 Cannon's skew (schematic)
fig, ax = canvas(FIG_W, 1.75)
q, cs = 3, 0.34
def gridlabels(x0, title, lab, color):
    ax.text(x0, 1.7, title, fontsize=7.2, weight="bold", va="top")
    for i in range(q):
        for j in range(q):
            box(ax, x0 + j * cs, 1.15 - i * cs * 1.02, cs - 0.03, cs - 0.03, lab(i, j),
                fc=color, ec="none", tc=WHITE, fs=6.2, r=0.02)
gridlabels(0.05, "(a) A before", lambda i, j: f"A{i}{j}", BLUE)
gridlabels(1.2, "(b) A after skew", lambda i, j: f"A{i}{(i + j) % q}", BLUE)
gridlabels(2.35, "(c) B after skew", lambda i, j: f"B{(i + j) % q}{j}", ORANGE)
ax.text(3.45, 1.2, "Row i of A\nshifts left i\nplaces; column j\nof B shifts up j\nplaces. Now each\nprocess holds\nmatching k.",
        fontsize=6.3, color=GRAY, va="top", linespacing=1.1)
ax.text(0.05, 0.05, "Then, √p times: multiply the local blocks, shift A left by 1 and B up by 1.",
        fontsize=6.5, color=INK)
save(fig, P("fig-13-03-cannon.png"))

# ------------------------------------------------ 13.4 SUMMA (schematic)
fig, ax = canvas(FIG_W, 1.85)
def mat(x0, y0, s, label, color, hl=None):
    ax.add_patch(Rectangle((x0, y0), s, s, fc=PAPER, ec=GRAY, lw=0.6))
    if hl:
        ax.add_patch(Rectangle(hl[0], hl[1], hl[2], fc=color, ec="none", alpha=0.9))
    ax.text(x0 + s / 2, y0 - 0.1, label, ha="center", va="top", fontsize=7)
s = 1.05
mat(0.2, 0.35, s, "C (block (i, j) highlighted)", INK,
    ((0.2 + s * 0.5, 0.35 + s * 0.5), s * 0.25, s * 0.25))
ax.text(1.38, 0.87, "+=", fontsize=9, va="center")
mat(1.65, 0.35, s, "A: column panel k", BLUE, ((1.65 + s * 0.6, 0.35), s * 0.12, s))
ax.text(2.83, 0.87, "×", fontsize=9, va="center")
mat(3.05, 0.35, s, "B: row panel k", ORANGE, ((3.05, 0.35 + s * 0.3), s, s * 0.12))
ax.text(0.2, 1.8, "Step k: the owners broadcast panel k of A along process rows, and panel k of B",
        fontsize=6.5, va="top")
ax.text(0.2, 1.67, "along process columns; each process adds the outer product of its pieces to its C block.",
        fontsize=6.5, va="top")
save(fig, P("fig-13-04-summa.png"))

# ------------------------------------------------ 13.5 counted traffic (REAL)
tr = rows_("traffic.csv")
fig, ax = plt.subplots(figsize=(FIG_W, 2.0), layout="constrained")
n2 = 720 * 720
for alg, lab, c, mk in (("1d", "1D ring", ORANGE, "^"), ("cannon", "Cannon", BLUE, "o"),
                        ("summa", "SUMMA (Fox identical)", TEALD, "s")):
    pts = sorted((int(r["processes"]), int(r["max_received"])) for r in tr
                 if r["algorithm"] == alg and int(r["processes"]) in (4, 9, 16))
    ax.plot([p for p, _ in pts], [m / n2 for _, m in pts], color=c, marker=mk, ms=5,
            lw=1.1, label=lab)
ax.set_xticks([4, 9, 16])
ax.set_ylim(0, 1.1)
ax.set_xlabel("Processes")
ax.set_ylabel("Values received by the busiest\nprocess, as a fraction of n²")
ax.grid(True, axis="y")
ax.legend(loc="center right", frameon=False, fontsize=7)
clean(ax)
save(fig, P("fig-13-05-traffic.png"))

# ------------------------------------------------ 13.6 comm share (MODEL)
F = float(VALS["F_gflops"]) * 1e9
pp = 4 ** np.arange(1, 8)
fig, ax = plt.subplots(figsize=(FIG_W, 2.0), layout="constrained")
for alg, lab, c, mk, ls in (("1d", "1D ring", ORANGE, "^", "--"),
                            ("cannon", "Cannon (2D)", BLUE, "o", "-"),
                            ("2.5d", "2.5D, 4 copies", TEALD, "s", "-.")):
    ax.plot(pp, [mdm.share(8192, int(p), alg, F) * 100 for p in pp], color=c, marker=mk,
            ms=3.6, lw=1.2, ls=ls, label=lab)
ax.set_xscale("log", base=4)
ax.set_xticks(pp, [f"{int(p):,}" for p in pp])
ax.set_ylim(0, 100)
ax.set_xlabel("Nodes, one process each (log scale)")
ax.set_ylabel("Share of time\ncommunicating (%)")
ax.grid(True, axis="y")
ax.legend(loc="upper left", frameon=False, fontsize=7)
ax.text(0.99, 0.97, "model, not measured", transform=ax.transAxes, ha="right", va="top",
        fontsize=7, color=GRAY, style="italic")
clean(ax)
save(fig, P("fig-13-06-model.png"))
print("figures written to", OUT)
