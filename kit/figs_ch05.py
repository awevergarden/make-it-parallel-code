"""figs_ch05.py -- figures for Chapter 5, Memory and the Roofline.

Usage: python3 kit/figs_ch05.py OUTDIR
Measured figures read data/ch05/*.csv (stamped if values.json is provisional).
"""
import sys, os, csv, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch05")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)
VALS = json.load(open(os.path.join(DATA, "values.json")))
rows = lambda n: list(csv.DictReader(open(os.path.join(DATA, n))))

def stamp(fig):
    if VALS.get("provisional"):
        fig.text(0.99, 0.99, "PROVISIONAL · trial data", ha="right",
                 va="top", fontsize=7, color=ORANGE, weight="bold")

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

KB, MB, GB = 1024, 1024 ** 2, 1024 ** 3
def size_label(b):
    return f"{b // GB} GB" if b >= GB else f"{b // MB} MB" if b >= MB else f"{b // KB} KB"

# ------------------------------------------------ 5.0 banner (Part II)
banner(P("fig-05-00-banner.png"), seed=35, mode="wave")

# ------------------------------------------------ 5.1 hierarchy (schematic)
fig, ax = canvas(FIG_W, 2.0)
levels = [("Registers", "~1 KB", "under 1 ns", INK, WHITE),
          ("L1 cache", "tens of KB per core", "~1–2 ns", BLUE, WHITE),
          ("L2 cache", "about 1–2 MB per core", "~5 ns", TEALD, WHITE),
          ("L3 cache", "tens to hundreds of MB, shared", "~10–50 ns", TEAL, INK),
          ("Main memory (DRAM)", "gigabytes", "~100 ns", AMBER, INK)]
cx, top, lh = 1.35, 1.9, 0.33
for k, (nm, size, lat, fc, tc) in enumerate(levels):
    w = 0.9 + k * 0.42
    y = top - (k + 1) * lh
    ax.add_patch(Polygon([(cx - w / 2, y), (cx + w / 2, y),
                          (cx + (w - 0.42) / 2 + 0.0, y + lh - 0.03),
                          (cx - (w - 0.42) / 2, y + lh - 0.03)],
                         closed=True, fc=fc, ec="none"))
    ax.text(cx, y + (lh - 0.03) / 2, nm, ha="center", va="center",
            fontsize=7, color=tc, weight="bold")
    ax.text(2.75, y + (lh - 0.03) / 2, size, va="center", fontsize=7, color=INK)
    ax.text(4.55, y + (lh - 0.03) / 2, lat, va="center", ha="right",
            fontsize=7, color=GRAY)
ax.text(2.75, top + 0.02, "Typical size", fontsize=7, weight="bold", color=INK)
ax.text(4.55, top + 0.02, "Latency", fontsize=7, weight="bold", ha="right",
        color=INK)
arrow(ax, 0.1, 1.75, 0.1, 0.25, color=GRAY, lw=1, ms=6)
ax.text(0.16, 1.0, "bigger,\nslower,\ncheaper\nper byte", fontsize=6.5,
        color=GRAY, va="center", linespacing=1.1)
save(fig, P("fig-05-01-hierarchy.png"))

# ------------------------------------------------ 5.2 latency staircase (measured)
lat = [(int(r["bytes"]), float(r["ns_per_load"])) for r in rows("latency.csv")]
fig, ax = plt.subplots(figsize=(FIG_W, 2.2), layout="constrained")
for (lo, hi, lab, c) in [(4 * KB, 48 * KB, "L1", BLUE), (48 * KB, 2 * MB, "L2", TEALD),
                          (2 * MB, 1.2 * GB, "L3 and memory", GRAY)]:
    ax.axvspan(lo, hi, color=c, alpha=0.08, lw=0)
    ax.text(np.sqrt(lo * hi) if lab != "L3 and memory" else 2.4 * MB,
            240, lab, ha="center" if lab != "L3 and memory" else "left",
            va="top", fontsize=7, color=c, weight="bold")
ax.plot([b for b, _ in lat], [t for _, t in lat], color=ORANGE, marker="o",
        ms=3.5, lw=1.2, zorder=3)
ax.set_xscale("log", base=2)
ax.set_yscale("log")
ticks = [4 * KB, 64 * KB, MB, 16 * MB, 256 * MB]
ax.set_xticks(ticks, [size_label(t) for t in ticks])
ax.set_yticks([1, 3, 10, 30, 100], ["1", "3", "10", "30", "100"])
ax.set_ylim(0.9, 300)
ax.set_xlabel("Working-set size (log scale)")
ax.set_ylabel("Nanoseconds per load\n(log scale)")
ax.grid(True, which="major", axis="y")
clean(ax)
stamp(fig)
save(fig, P("fig-05-02-latency.png"))

# ------------------------------------------------ 5.3 cache lines and stride (schematic)
fig, ax = canvas(FIG_W, 1.05)
cw, x0 = 0.12, 0.62
def strip(y, stride, label):
    ax.text(x0 - 0.08, y + 0.1, label, ha="right", va="center", fontsize=7)
    for k in range(24):
        ax.add_patch(Rectangle((x0 + k * cw, y), cw - 0.015, 0.2,
                     fc=ORANGE if k % stride == 0 else LIGHT, ec="none"))
    for line_k in range(3):
        ax.add_patch(Rectangle((x0 + line_k * 8 * cw - 0.005, y - 0.03),
                     8 * cw - 0.005, 0.26, fc="none", ec=INK, lw=0.8))
strip(0.5, 1, "stride 1")
strip(0.1, 8, "stride 8")
for line_k in range(3):
    ax.text(x0 + line_k * 8 * cw + 4 * cw, 0.82, f"line {line_k + 1}: 64 bytes",
            ha="center", fontsize=6.5, color=GRAY)
ax.text(x0 + 24 * cw + 0.08, 0.6, "all 8 values\nused per line", fontsize=6.6,
        va="center", color=INK, linespacing=1.1)
ax.text(x0 + 24 * cw + 0.08, 0.2, "1 of 8 values\nused per line", fontsize=6.6,
        va="center", color=INK, linespacing=1.1)
save(fig, P("fig-05-03-lines.png"))

# ------------------------------------------------ 5.4 stride (measured)
sd = [(int(r["param"]), float(r["ns_per_element"])) for r in rows("stride.csv")
      if r["kind"] == "stride"]
fig, ax = plt.subplots(figsize=(FIG_W, 1.95), layout="constrained")
ax.plot([s for s, _ in sd], [t for _, t in sd], color=BLUE, marker="o", ms=4,
        lw=1.2, zorder=3)
ax.axvline(8, color=GRAY, lw=0.8, ls=":")
ax.text(8.4, max(t for _, t in sd) * 0.95, "one element\nper cache line",
        fontsize=6.8, color=GRAY, va="top", linespacing=1.1)
ax.set_xscale("log", base=2)
ax.set_xticks([1, 2, 4, 8, 16, 32, 64], ["1", "2", "4", "8", "16", "32", "64"])
ax.set_ylim(0, max(t for _, t in sd) * 1.12)
ax.set_xlabel("Stride (elements; log scale)")
ax.set_ylabel("Nanoseconds per element")
ax.grid(True, axis="y")
clean(ax)
stamp(fig)
save(fig, P("fig-05-04-stride.png"))

# ------------------------------------------------ 5.5 roofline (measured ceilings)
bw = {r["level"]: float(r["GBps"]) * 32 / 24 for r in rows("bandwidth.csv")}
peak = float(VALS["peak"])
fig, ax = plt.subplots(figsize=(FIG_W, 2.45), layout="constrained")
ai = np.logspace(-2, 1.3, 200)
ax.plot(ai, np.minimum(peak, ai * bw["memory"]), color=INK, lw=1.6,
        label=f"memory ({bw['memory']:.0f} GB/s)")
ax.plot(ai, np.minimum(peak, ai * bw["L2"]), color=TEALD, lw=1.0, ls="--",
        label=f"L2 cache ({bw['L2']:.0f} GB/s)")
ridge = peak / bw["memory"]
ax.axvline(ridge, color=GRAY, lw=0.7, ls=":")
ax.text(ridge * 1.08, 0.13, f"ridge point\n{ridge:.2f} flop/byte", fontsize=6.6,
        color=GRAY, va="bottom", linespacing=1.1)
ax.text(12, peak * 1.12, f"compute ceiling {peak:.1f} GFLOP/s", fontsize=6.8,
        ha="right", color=INK)
g1, g2 = float(VALS["v1_gflops"]), float(VALS["v2_gflops"])
ax.scatter([4 / 24], [g1], s=28, color=ORANGE, marker="o", zorder=4,
           label="HeatSim v1, 4,096 grid")
ax.scatter([4 / 16], [g2], s=34, color=BLUE, marker="^", zorder=4,
           label="HeatSim v2, 4,096 grid")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(0.03, 20)
ax.set_ylim(0.1, 20)
ax.set_xlabel("Arithmetic intensity (flop/byte, log scale)")
ax.set_ylabel("GFLOP/s (log scale)")
ax.grid(True, which="major")
ax.legend(loc="lower right", frameon=False, fontsize=6.8)
clean(ax)
stamp(fig)
save(fig, P("fig-05-05-roofline.png"))

# ------------------------------------------------ 5.6 two steps per sweep (schematic)
fig, ax = canvas(FIG_W, 1.95)
RH, GW = 0.13, 0.82
def mini(x0, name, colors):
    ax.text(x0 + GW / 2, 1.62, name, ha="center", va="bottom", fontsize=7,
            family=MONO, weight="bold")
    for r in range(9):
        y = 1.5 - r * (RH + 0.02)
        ax.add_patch(Rectangle((x0, y), GW, RH, fc=colors.get(r, PAPER), ec="none"))
        if x0 < 1 or 2.3 < x0 < 2.5:
            ax.text(x0 - 0.05, y + RH / 2, str(r), ha="right", va="center",
                    fontsize=6, color=GRAY)
done = {1: BLUE, 2: BLUE}
ax.text(0.2, 1.93, "1  Step A writes next row 4", fontsize=7.5, weight="bold",
        va="top")
mini(0.35, "cur", {**done, 3: TEAL, 4: TEAL, 5: TEAL})
mini(1.3, "next", {4: ORANGE})
ax.text(2.45, 1.93, "2  Step B writes cur row 3", fontsize=7.5, weight="bold",
        va="top")
mini(2.6, "cur", {**done, 3: ORANGE})
mini(3.55, "next", {2: TEAL, 3: TEAL, 4: TEAL})
line(ax, [2.33, 2.33], [0.2, 1.9], color=LIGHT, lw=0.8)
keys = [("read", TEAL), ("written", ORANGE), ("already at step t + 2", BLUE)]
for k, (lab, c) in enumerate(keys):
    x = 0.35 + k * 1.05
    ax.add_patch(Rectangle((x, 0.03), 0.12, 0.1, fc=c, ec="none"))
    ax.text(x + 0.17, 0.08, lab, fontsize=6.6, va="center", color=INK)
save(fig, P("fig-05-06-two-steps.png"))

# ------------------------------------------------ 5.7 v1 vs v2 (measured)
h = {}
for r in rows("heat.csv"):
    h.setdefault((r["version"], int(r["n"])), []).append(float(r["mlups"]))
ns = sorted({n for _, n in h})
fig, ax = plt.subplots(figsize=(FIG_W, 2.0), layout="constrained")
ax.plot(ns, [st.median(h[("v1", n)]) for n in ns], color=ORANGE, marker="o",
        ms=4, lw=1.2, label="v1: one step per sweep")
ax.plot(ns, [st.median(h[("v2", n)]) for n in ns], color=BLUE, marker="^",
        ms=4.5, lw=1.2, ls="--", label="v2: two steps per sweep")
ax.set_xscale("log", base=2)
ax.set_xticks(ns, [f"{n:,}" for n in ns])
ax.set_ylim(0, max(max(x) for x in h.values()) * 1.15)
ax.set_xlabel("Grid width n (log scale)")
ax.set_ylabel("Million cell updates\nper second")
ax.grid(True, axis="y")
ax.legend(loc="lower left", frameon=False)
clean(ax)
stamp(fig)
save(fig, P("fig-05-07-v1-v2.png"))
print("figures written to", OUT)
