"""figs_ch06.py -- figures for Chapter 6, SIMD and Vectorization.

Usage: python3 kit/figs_ch06.py OUTDIR
Measured figures read data/ch06/*.csv (stamped if values.json is provisional).
"""
import sys, os, csv, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch06")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)
VALS = json.load(open(os.path.join(DATA, "values.json")))

def med(name, keys, val):
    d = {}
    for r in csv.DictReader(open(os.path.join(DATA, name))):
        d.setdefault(tuple(r[k] for k in keys), []).append(float(r[val]))
    return d

def stamp(fig):
    if VALS.get("provisional"):
        fig.text(0.99, 0.99, "PROVISIONAL · trial data", ha="right",
                 va="top", fontsize=7, color=ORANGE, weight="bold")

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

# ------------------------------------------------ 6.0 banner (Part II)
banner(P("fig-06-00-banner.png"), seed=42, mode="wave")

# ------------------------------------------------ 6.1 scalar vs SIMD (schematic)
fig, ax = canvas(FIG_W, 1.95)
cw, ch = 0.3, 0.22
def cells(x, y, vals, fc, tc=WHITE):
    for k, t in enumerate(vals):
        box(ax, x + k * cw, y, cw - 0.03, ch, t, fc=fc, ec="none", tc=tc,
            fs=6.8, r=0.02, weight="bold")
ax.text(0.05, 1.9, "(a) Scalar: four add instructions", fontsize=7.5,
        weight="bold", va="top")
for k in range(4):
    y = 1.45 - k * 0.3
    cells(0.1, y, [f"x{k}"], BLUE)
    ax.text(0.47, y + ch / 2, "+", ha="center", va="center", fontsize=8)
    cells(0.55, y, [f"y{k}"], TEALD)
    ax.text(0.92, y + ch / 2, "→", ha="center", va="center", fontsize=8)
    cells(1.0, y, [f"z{k}"], ORANGE)
    ax.text(1.4, y + ch / 2, f"add #{k + 1}", va="center", fontsize=6.6, color=GRAY)
ax.text(2.25, 1.9, "(b) SIMD: one add instruction, four lanes", fontsize=7.5,
        weight="bold", va="top")
cells(2.35, 1.45, ["x0", "x1", "x2", "x3"], BLUE)
ax.text(2.35 + 4 * cw + 0.08, 1.45 + ch / 2, "+", va="center", fontsize=8)
cells(2.35, 1.1, ["y0", "y1", "y2", "y3"], TEALD)
line(ax, [2.35, 2.35 + 4 * cw - 0.03], [1.0, 1.0], color=INK, lw=0.8)
cells(2.35, 0.7, ["z0", "z1", "z2", "z3"], ORANGE)
ax.text(2.35 + 4 * cw + 0.08, 0.7 + ch / 2, "vector add #1", va="center",
        fontsize=6.6, color=GRAY)
for k, (bits, lanes) in enumerate([(128, 2), (256, 4), (512, 8)]):
    y = 0.3 - k * 0.0
x0 = 2.35
ax.text(x0, 0.44, "A register holds", fontsize=6.8, color=INK)
for k, (bits, lanes) in enumerate([(128, 2), (256, 4), (512, 8)]):
    xx = x0 + k * 0.75
    ax.text(xx, 0.3, f"{bits} bits:", fontsize=6.5, color=GRAY, va="center")
    for l in range(lanes):
        ax.add_patch(Rectangle((xx + 0.38 + l * 0.04, 0.26), 0.035, 0.08,
                     fc=BLUE, ec="none"))
    ax.text(xx, 0.12, f"{lanes} doubles", fontsize=6.3, color=GRAY, va="center")
save(fig, P("fig-06-01-simd.png"))

# ------------------------------------------------ 6.2 vector loop + remainder (schematic)
fig, ax = canvas(FIG_W, 1.0)
n, vf, cw = 19, 4, 0.2
x0 = 0.3
for i in range(n):
    body = i < (n // vf) * vf
    fc = [BLUE, TEALD, TEAL, AMBER][(i // vf) % 4] if body else ORANGE
    ax.add_patch(Rectangle((x0 + i * cw, 0.45), cw - 0.02, 0.25, fc=fc, ec="none"))
    ax.text(x0 + i * cw + cw / 2 - 0.01, 0.575, str(i), ha="center",
            va="center", fontsize=6, color=WHITE if fc in (BLUE, TEALD, ORANGE) else INK)
for g in range(n // vf):
    xa, xb = x0 + g * vf * cw, x0 + (g + 1) * vf * cw - 0.02
    line(ax, [xa, xa, xb, xb], [0.4, 0.35, 0.35, 0.4], color=GRAY, lw=0.7)
    ax.text((xa + xb) / 2, 0.3, f"vector trip {g + 1}", ha="center", va="top",
            fontsize=6.3, color=GRAY)
xa = x0 + (n // vf) * vf * cw
ax.text(xa + 1.5 * cw, 0.3, "scalar\nremainder", ha="center", va="top",
        fontsize=6.3, color=ORANGE, linespacing=1.05)
ax.text(x0, 0.9, "A loop of 19 iterations with 4-wide vectors:", fontsize=7,
        weight="bold", va="center")
save(fig, P("fig-06-02-remainder.png"))

# ------------------------------------------------ 6.3 AoS vs SoA (schematic)
fig, ax = canvas(FIG_W, 1.3)
cw = 0.16
col = {"x": BLUE, "y": TEALD, "z": AMBER}
ax.text(0.05, 1.25, "(a) Array of structures", fontsize=7.5, weight="bold", va="top")
for p_ in range(4):
    for k, c in enumerate("xyz"):
        i = p_ * 3 + k
        ax.add_patch(Rectangle((0.1 + i * cw, 0.72), cw - 0.02, 0.22, fc=col[c], ec="none"))
        ax.text(0.1 + i * cw + cw / 2 - 0.01, 0.83, f"{c}{p_}", ha="center", va="center",
                fontsize=5.8, color=WHITE if c != "z" else INK)
ax.text(0.1, 0.55, "The x values are 24 bytes apart:\na vector load of four x's needs a gather.",
        fontsize=6.4, color=GRAY, va="top", linespacing=1.1)
ax.text(2.45, 1.25, "(b) Structure of arrays", fontsize=7.5, weight="bold", va="top")
for k, c in enumerate("xyz"):
    for p_ in range(4):
        ax.add_patch(Rectangle((2.5 + p_ * cw + k * 0.7, 0.72), cw - 0.02, 0.22,
                     fc=col[c], ec="none"))
        ax.text(2.5 + p_ * cw + k * 0.7 + cw / 2 - 0.01, 0.83, f"{c}{p_}",
                ha="center", va="center", fontsize=5.8, color=WHITE if c != "z" else INK)
ax.text(2.5, 0.55, "The x values are contiguous:\none vector load gets four of them.",
        fontsize=6.4, color=GRAY, va="top", linespacing=1.1)
line(ax, [2.3, 2.3], [0.1, 1.2], color=LIGHT, lw=0.8)
save(fig, P("fig-06-03-layout.png"))

# ------------------------------------------------ 6.4 daxpy by width and level (measured)
d = med("daxpy.csv", ["variant", "level"], "GFLOPs")
ws = [("scalar", "scalar", LIGHT, ""), ("v128", "128-bit", TEAL, "//"),
      ("v256", "256-bit", BLUE, ".."), ("v512", "512-bit", INK, "xx")]
levels = [("L1", "In L1 cache (16 KB)"), ("L2", "In L2 cache (512 KB)"),
          ("memory", "From memory (256 MB)")]
fig, ax = plt.subplots(figsize=(FIG_W, 2.15), layout="constrained")
bw_ = 0.19
for k, (w, lab, c, hatch) in enumerate(ws):
    vals = [st.median(d[(w, lv)]) for lv, _ in levels]
    xs = np.arange(3) + (k - 1.5) * bw_
    ax.bar(xs, vals, width=bw_ * 0.92, color=c, hatch=hatch, edgecolor=WHITE,
           lw=0.3, label=lab, zorder=2)
    for x, val in zip(xs, vals):
        ax.text(x, val + 0.3, f"{val:.1f}", ha="center", va="bottom", fontsize=6)
ax.set_xticks(range(3), [t for _, t in levels])
ax.set_ylabel("GFLOP/s")
ax.set_ylim(0, max(st.median(x) for x in d.values()) * 1.15)
ax.grid(True, axis="y")
ax.legend(loc="upper right", frameon=False, fontsize=7, title="vector width",
          title_fontsize=7)
clean(ax)
stamp(fig)
save(fig, P("fig-06-04-daxpy.png"))

# ------------------------------------------------ 6.5 HeatSim versions (measured)
h = med("heat.csv", ["version", "n"], "mlups")
ns = sorted({int(n) for _, n in h})
fig, ax = plt.subplots(figsize=(FIG_W, 2.1), layout="constrained")
for ver, lab, c, mk, ls in [("v1", "v1: sequential", ORANGE, "o", "-"),
                             ("v2", "v2: two steps per sweep", GRAY, "s", ":"),
                             ("v3_v128", "v3: vectorized, 128-bit", BLUE, "^", "--"),
                             ("v3_v512", "v3: vectorized, 512-bit", INK, "D", "-.")]:
    ax.plot(ns, [st.median(h[(ver, str(n))]) for n in ns], color=c, marker=mk,
            ms=3.8, lw=1.2, ls=ls, label=lab)
ax.set_xscale("log", base=2)
ax.set_xticks(ns, [f"{n:,}" for n in ns])
ax.set_ylim(0, max(max(x) for x in h.values()) * 1.12)
ax.set_xlabel("Grid width n (log scale)")
ax.set_ylabel("Million cell updates\nper second")
ax.grid(True, axis="y")
ax.legend(loc="upper right", frameon=False, fontsize=7)
clean(ax)
stamp(fig)
save(fig, P("fig-06-05-heatsim.png"))
print("figures written to", OUT)
