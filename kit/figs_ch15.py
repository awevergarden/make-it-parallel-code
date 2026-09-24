"""figs_ch15.py -- figures for Chapter 15, NPUs, TPUs and AI-Scale Parallelism.

Usage: python3 kit/figs_ch15.py OUTDIR
Figure 15.3 plots the REAL precision experiment (precision.py).
"""
import sys, os, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch15")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

banner(P("fig-15-00-banner.png"), seed=105, mode="wave")

# ------------------------------------------------ 15.1 number formats (schematic)
fmts = [("float32", 1, 8, 23), ("bfloat16", 1, 8, 7), ("float16", 1, 5, 10),
        ("FP8 (E4M3)", 1, 4, 3), ("int8", 0, 0, 0)]
fig, ax = canvas(FIG_W, 1.75)
unit = 0.08
for r, (name, sgn, ex, man) in enumerate(fmts):
    y = 1.5 - r * 0.3
    ax.text(0.05, y + 0.08, name, fontsize=6.8, va="center", weight="bold")
    x = 0.85
    if name == "int8":
        for k in range(8):
            ax.add_patch(Rectangle((x + k * unit, y), unit - 0.012, 0.16, fc=GRAY, ec="none"))
        ax.text(x + 8 * unit + 0.06, y + 0.08, "integer, with a scale factor",
                fontsize=6.3, va="center", color=GRAY)
        continue
    for k, (count, c) in enumerate(((sgn, INK), (ex, ORANGE), (man, BLUE))):
        for _ in range(count):
            ax.add_patch(Rectangle((x, y), unit - 0.012, 0.16, fc=c, ec="none"))
            x += unit
    ax.text(x + 0.06, y + 0.08, f"{ex} exponent, {man} fraction", fontsize=6.1,
            va="center", color=GRAY)
ax.text(0.85, 0.05, "navy: sign   orange: exponent (range)   blue: fraction (precision)",
        fontsize=6.3, color=GRAY)
save(fig, P("fig-15-01-formats.png"))

# ------------------------------------------------ 15.2 weight-stationary array (schematic)
fig, ax = canvas(FIG_W, 2.05)
x0, y0, s = 1.55, 0.35, 0.45
for k in range(3):
    for j in range(3):
        box(ax, x0 + j * s, y0 + (2 - k) * s, s - 0.08, s - 0.08, f"B{k}{j}", fc=TEALD,
            ec="none", tc=WHITE, fs=6.6, r=0.03)
        if j < 2:
            arrow(ax, x0 + j * s + s - 0.08, y0 + (2 - k) * s + 0.18,
                  x0 + (j + 1) * s, y0 + (2 - k) * s + 0.18, color=BLUE, ms=5)
        if k < 2:
            arrow(ax, x0 + j * s + 0.18, y0 + (2 - k) * s, x0 + j * s + 0.18,
                  y0 + (1 - k) * s + s - 0.08, color=ORANGE, ms=5)
for k in range(3):                                     # skewed rows of A entering
    y = y0 + (2 - k) * s + 0.18
    for r_ in range(3):
        xx = x0 - 0.3 - (r_ + k) * 0.28
        box(ax, xx, y - 0.09, 0.24, 0.18, f"A{r_}{k}", fc=BLUE, ec="none", tc=WHITE,
            fs=5.6, r=0.02)
ax.text(0.05, 1.95, "Rows of A stream in from the left, skewed by one cycle per row;",
        fontsize=6.6, va="top")
ax.text(0.05, 1.82, "the weights B stay put; partial sums flow down and leave as rows of C.",
        fontsize=6.6, va="top")
for j in range(3):
    arrow(ax, x0 + j * s + 0.18, y0, x0 + j * s + 0.18, y0 - 0.2, color=ORANGE, ms=5)
ax.text(x0 + 0.6, 0.05, "C leaves the bottom", fontsize=6.3, color=ORANGE, ha="center")
save(fig, P("fig-15-03-systolic.png"))

# ------------------------------------------------ 15.3 precision (REAL)
pr = list(csv.DictReader(open(os.path.join(DATA, "precision.csv"))))
labels = ["float32", "bfloat16", "float16", "fp8_e4m3", "int8"]
nice = {"float32": "float32", "bfloat16": "bfloat16", "float16": "float16",
        "fp8_e4m3": "FP8 E4M3", "int8": "int8"}
wide = {r["format"]: float(r["relative_error"]) for r in pr if r["accumulate"] != r["format"]}
own = {r["format"]: float(r["relative_error"]) for r in pr if r["accumulate"] == r["format"]}
wide["float32"] = own.get("float32", wide.get("float32"))
fig, ax = plt.subplots(figsize=(FIG_W, 2.0), layout="constrained")
x = np.arange(len(labels))
ax.bar(x - 0.19, [wide[l] for l in labels], width=0.36, color=BLUE,
       label="accumulate in 32 bits (int8: exact integers)")
ax.bar([i + 0.19 for i, l in enumerate(labels) if l in ("bfloat16", "float16")],
       [own[l] for l in ("bfloat16", "float16")], width=0.36, color=ORANGE, hatch="///",
       edgecolor=WHITE, lw=0.3, label="accumulate in the same 16-bit format")
ax.set_yscale("log")
ax.set_xticks(x, [nice[l] for l in labels])
ax.set_ylabel("Relative error\n(log scale)")
ax.set_ylim(1e-7, 30)
ax.grid(True, axis="y")
ax.legend(loc="upper left", frameon=False, fontsize=6.6)
clean(ax)
save(fig, P("fig-15-02-precision.png"))

# ------------------------------------------------ 15.4 parallelism strategies (schematic)
fig, ax = canvas(FIG_W, 2.25)
cols = [BLUE, TEALD, ORANGE, AMBER]
ax.text(0.05, 2.2, "(a) Data parallel", fontsize=7.2, weight="bold", va="top")
for k in range(4):
    box(ax, 0.1 + k * 0.33, 1.55, 0.28, 0.4, "full\nmodel", fc=cols[k], ec="none",
        tc=WHITE if k < 3 else INK, fs=5.4, r=0.02)
ax.text(0.1, 1.42, "each: its own data;\nallreduce gradients", fontsize=6, color=GRAY,
        va="top", linespacing=1.05)
ax.text(1.6, 2.2, "(b) Tensor parallel", fontsize=7.2, weight="bold", va="top")
box(ax, 1.65, 1.55, 1.2, 0.4, "", fc=PAPER, ec=GRAY)
for k in range(4):
    ax.add_patch(Rectangle((1.68 + k * 0.29, 1.6), 0.26, 0.3, fc=cols[k], ec="none",
                           zorder=4))
ax.text(1.65, 1.42, "each layer's matrices\nsplit across devices", fontsize=6, color=GRAY,
        va="top", linespacing=1.05)
ax.text(3.1, 2.2, "(c) Pipeline parallel", fontsize=7.2, weight="bold", va="top")
for k in range(4):
    box(ax, 3.15 + k * 0.36, 1.55, 0.3, 0.4, f"layers\n{k + 1}/4", fc=cols[k], ec="none",
        tc=WHITE if k < 3 else INK, fs=5.4, r=0.02)
ax.text(3.15, 1.42, "consecutive layers\non different devices", fontsize=6, color=GRAY,
        va="top", linespacing=1.05)
ax.text(0.05, 0.98, "(d) A 4-stage pipeline with 6 micro-batches: gray cells are the bubble",
        fontsize=7.2, weight="bold", va="top")
m, st_, cw, ch_ = 6, 4, 0.2, 0.15
for s_ in range(st_):
    y = 0.62 - s_ * 0.17
    ax.text(0.5, y + ch_ / 2, f"stage {s_ + 1}", fontsize=6, ha="right", va="center")
    for t in range(m + st_ - 1):
        mb = t - s_
        busy = 0 <= mb < m
        ax.add_patch(Rectangle((0.6 + t * cw, y), cw - 0.02, ch_,
                     fc=cols[s_] if busy else LIGHT, ec="none"))
        if busy:
            ax.text(0.6 + t * cw + cw / 2 - 0.01, y + ch_ / 2, str(mb + 1), fontsize=5.5,
                    ha="center", va="center", color=WHITE if s_ < 3 else INK)
ax.text(0.6 + (m + st_ - 1) * cw + 0.1, 0.4, "idle fraction\n= (stages − 1) /\n"
        "(micro-batches +\nstages − 1)", fontsize=6.2, color=GRAY, va="center",
        linespacing=1.1)
save(fig, P("fig-15-04-parallelism.png"))
print("figures written to", OUT)
