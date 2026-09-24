"""figs_ch04.py -- figures for Chapter 4, Inside the CPU.

Usage: python3 kit/figs_ch04.py OUTDIR
Measured figures read data/ch04/*.csv (stamped if values.json is provisional).
"""
import sys, os, csv, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch04")
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

STAGE = [("F", "Fetch", BLUE), ("D", "Decode", TEALD), ("E", "Execute", ORANGE),
         ("M", "Memory", AMBER), ("W", "Write back", INK)]

# ------------------------------------------------ 4.0 banner (Part II)
banner(P("fig-04-00-banner.png"), seed=28, mode="wave")

# ------------------------------------------------ 4.1 pipeline timing
fig, ax = canvas(FIG_W, 1.9)
cw, rh, x0 = 0.22, 0.17, 0.62
def row(y, start, label):
    ax.text(x0 - 0.08, y + rh / 2, label, ha="right", va="center",
            fontsize=7, family=MONO)
    for k, (ab, _, c) in enumerate(STAGE):
        box(ax, x0 + (start + k) * cw + 0.01, y, cw - 0.02, rh, ab, fc=c,
            ec="none", tc=WHITE if c not in (AMBER,) else INK, fs=6.5,
            r=0.02, weight="bold")
ax.text(0.02, 1.88, "(a) Without pipelining: one instruction at a time",
        fontsize=7.5, weight="bold", va="top")
for i in range(3):
    row(1.52 - i * 0.19, 5 * i, f"instr {i + 1}")
ax.text(x0 + 15 * cw + 0.05, 1.14 + 0.085, "15 cycles", fontsize=7, color=ORANGE,
        weight="bold", va="center")
ax.text(0.02, 1.0, "(b) Pipelined: a new instruction enters every cycle",
        fontsize=7.5, weight="bold", va="top")
for i in range(3):
    row(0.66 - i * 0.19, i, f"instr {i + 1}")
ax.text(x0 + 7 * cw + 0.05, 0.28 + 0.085, "7 cycles", fontsize=7, color=ORANGE,
        weight="bold", va="center")
for c in range(16):
    ax.text(x0 + c * cw + cw / 2, 0.04, str(c + 1), ha="center", fontsize=6,
            color=GRAY)
ax.text(x0 - 0.08, 0.04, "cycle", ha="right", fontsize=6.5, color=GRAY)
for k, (ab, name, c) in enumerate(STAGE):
    ax.add_patch(Rectangle((2.72 + (k % 3) * 0.62, 0.66 - (k // 3) * 0.2),
                           0.1, 0.1, fc=c, ec="none"))
    ax.text(2.85 + (k % 3) * 0.62, 0.71 - (k // 3) * 0.2, f"{ab} {name}",
            fontsize=6.3, va="center", color=INK)
save(fig, P("fig-04-01-pipeline.png"))

# ------------------------------------------------ 4.2 accumulators (measured)
acc = {}
for r in rows("accum.csv"):
    acc.setdefault(int(r["accumulators"]), []).append(float(r["ns_per_add"]))
ks = [1, 2, 4, 8]
med = [st.median(acc[k]) for k in ks]
fig, ax = plt.subplots(figsize=(FIG_W, 1.95), layout="constrained")
ax.bar(range(4), med, color=[INK, BLUE, TEALD, TEAL], width=0.6, zorder=2)
for i, k in enumerate(ks):
    ax.scatter([i] * len(acc[k]), acc[k], s=7, color=ORANGE, zorder=3, lw=0)
    ax.text(i, max(acc[k]) + max(med) * 0.03,
            f"{med[i]:.2f} ns" + ("" if k == 1 else f"  ({med[0] / med[i]:.1f}×)"),
            ha="center", va="bottom", fontsize=7.2)
ax.set_xticks(range(4), [f"{k} accumulator" + ("s" if k > 1 else "") for k in ks])
ax.set_ylabel("Nanoseconds per addition")
ax.set_ylim(0, max(max(v) for v in acc.values()) * 1.2)
ax.grid(True, axis="y")
clean(ax)
stamp(fig)
save(fig, P("fig-04-02-accumulators.png"))

# ------------------------------------------------ 4.3 out-of-order core (schematic)
fig, ax = canvas(FIG_W, 2.5)
box(ax, 0.05, 1.9, 0.9, 0.42, "Instruction\ncache", fc=PAPER, ec=GRAY, fs=6.8)
fe = [("Fetch", BLUE), ("Decode", BLUE), ("Rename", BLUE)]
for k, (nm, c) in enumerate(fe):
    box(ax, 1.15 + k * 0.72, 1.95, 0.6, 0.32, nm, fc=c, ec="none", tc=WHITE,
        fs=7, weight="bold")
    if k:
        arrow(ax, 1.15 + k * 0.72 - 0.11, 2.11, 1.15 + k * 0.72 - 0.01, 2.11,
              color=GRAY, ms=5)
arrow(ax, 0.96, 2.11, 1.14, 2.11, color=GRAY, ms=5)
ax.text(1.15, 2.4, "in order: follows the program", fontsize=6.6, color=BLUE,
        weight="bold")
box(ax, 3.4, 1.7, 1.15, 0.72, "Reorder buffer:\ninstructions in flight,\nretired in order",
    fc=AMBER, ec="none", fs=6.8)
arrow(ax, 3.05, 2.11, 3.38, 2.11, color=GRAY, ms=5)
box(ax, 1.15, 1.2, 2.04, 0.38, "Scheduler: waits for operands,\nsends ready instructions",
    fc=PAPER, ec=TEALD, tc=INK, fs=6.6)
arrow(ax, 2.55, 1.93, 2.17, 1.6, color=GRAY, ms=5)
units = [("ALU", TEALD), ("ALU", TEALD), ("FP /\nvector", ORANGE),
         ("FP /\nvector", ORANGE), ("Load", INK), ("Store", INK), ("Branch", PURPLE)]
for k, (nm, c) in enumerate(units):
    x = 0.12 + k * 0.49
    box(ax, x, 0.42, 0.42, 0.42, nm, fc=c, ec="none", tc=WHITE, fs=6.3,
        weight="bold")
    arrow(ax, 2.17, 1.19, x + 0.21, 0.86, color=LIGHT, lw=0.7, ms=4)
ax.text(0.12, 0.3, "execution units: out of order, whenever inputs are ready",
        fontsize=6.6, color=ORANGE, weight="bold", va="top")
box(ax, 3.62, 0.42, 0.93, 0.42, "Data cache", fc=PAPER, ec=GRAY, fs=6.8)
arrow(ax, 3.56, 0.63, 3.61, 0.63, color=GRAY, ms=4, style="<|-|>")
arrow(ax, 3.3, 0.88, 3.72, 1.68, color=GRAY, ms=5)
ax.text(3.58, 1.12, "results", fontsize=6.6, color=GRAY, va="center")
save(fig, P("fig-04-03-core.png"))

# ------------------------------------------------ 4.4 two-bit predictor
fig, ax = canvas(FIG_W, 1.45)
states = [("Strongly\ntaken", BLUE, WHITE), ("Weakly\ntaken", TEAL, INK),
          ("Weakly\nnot taken", AMBER, INK), ("Strongly\nnot taken", ORANGE, WHITE)]
xs = [0.3 + k * 1.1 for k in range(4)]
for (nm, c, tc), x in zip(states, xs):
    ax.add_patch(matplotlib.patches.Ellipse((x + 0.35, 0.72), 0.72, 0.44,
                 fc=c, ec="none", zorder=2))
    ax.text(x + 0.35, 0.72, nm, ha="center", va="center", fontsize=6.6,
            color=tc, weight="bold", zorder=3, linespacing=1.05)
for k in range(3):
    xa, xb = xs[k] + 0.72, xs[k + 1] - 0.02
    ax.add_patch(FancyArrowPatch((xa, 0.8), (xb, 0.8),
                 connectionstyle="arc3,rad=-0.35", arrowstyle="-|>",
                 mutation_scale=6, color=GRAY, lw=0.8))
    ax.text((xa + xb) / 2, 1.08, "not taken", ha="center", fontsize=6.2,
            color=GRAY)
    ax.add_patch(FancyArrowPatch((xb, 0.64), (xa, 0.64),
                 connectionstyle="arc3,rad=-0.35", arrowstyle="-|>",
                 mutation_scale=6, color=GRAY, lw=0.8))
    ax.text((xa + xb) / 2, 0.3, "taken", ha="center", fontsize=6.2,
            color=GRAY)
ax.text(xs[0] + 0.35, 1.2, "predict taken", ha="center", fontsize=7,
        color=BLUE, weight="bold")
ax.text(xs[1] + 0.35, 1.2, "predict taken", ha="center", fontsize=7,
        color=BLUE, weight="bold")
ax.text(xs[2] + 0.35, 1.2, "predict not taken", ha="center", fontsize=7,
        color=ORANGE, weight="bold")
ax.text(xs[3] + 0.35, 1.2, "predict not taken", ha="center", fontsize=7,
        color=ORANGE, weight="bold")
ax.text(2.35, 0.05, "A single surprise moves the counter one step; it takes two "
        "in a row to change the prediction.", ha="center", fontsize=6.6,
        color=GRAY)
save(fig, P("fig-04-04-predictor.png"))

# ------------------------------------------------ 4.5 branch predictability (measured)
br = {}
for r in rows("branch.csv"):
    br.setdefault((r["variant"], int(r["threshold"])), []).append(
        float(r["ns_per_element"]))
ts = sorted(t for (v, t) in br if v == "jump")
pct = [(256 - t) / 256 * 100 for t in ts]
fig, ax = plt.subplots(figsize=(FIG_W, 1.95), layout="constrained")
ax.plot(pct, [st.median(br[("jump", t)]) for t in ts], color=BLUE, marker="o",
        ms=3.8, lw=1.2, label="random data, branch kept", zorder=3)
s = st.median(br[("jump_sorted", 128)])
o = st.median(br[("O2", 128)])
ax.axhline(s, color=TEALD, lw=1.0, ls="--")
ax.text(101, s + 0.04, " sorted data", va="bottom", fontsize=6.8, color=TEALD)
ax.axhline(o, color=ORANGE, lw=1.0, ls=":")
ax.text(101, o - 0.04, " plain -O2", va="top", fontsize=6.8, color=ORANGE)
ax.set_xlim(-3, 118)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_ylim(0, max(st.median(v) for v in br.values()) * 1.15)
ax.set_xlabel("Percentage of elements for which the branch is taken")
ax.set_ylabel("Nanoseconds per element")
ax.grid(True, axis="y")
clean(ax)
stamp(fig)
save(fig, P("fig-04-05-branches.png"))
# ------------------------------------------------ 4.6 branch-pattern length (measured)
if os.path.exists(os.path.join(DATA, "pattern.csv")):
    pt = {}
    for r in rows("pattern.csv"):
        pt.setdefault(int(r["period"]), []).append(float(r["ns_per_element"]))
    ks = sorted(pt)
    fig, ax = plt.subplots(figsize=(FIG_W, 1.95), layout="constrained")
    ax.plot(ks, [st.median(pt[k]) for k in ks], color=BLUE, marker="o", ms=3.5,
            lw=1.2, zorder=3)
    ax.axhline(float(VALS["br_random"]), color=ORANGE, lw=0.9, ls="--")
    ax.text(2.2, float(VALS["br_random"]) + 0.15, "fully random branch (Figure 4.5)",
            fontsize=6.6, color=ORANGE)
    ax.set_xscale("log", base=2)
    ax.set_xticks([2, 16, 128, 1024, 8192, 65536, 1048576],
                  ["2", "16", "128", "1,024", "8,192", "65,536", "1M"])
    ax.set_ylim(0, max(max(x) for x in pt.values()) * 1.25)
    ax.set_xlabel("Length of the repeating pattern (log scale)")
    ax.set_ylabel("Nanoseconds per element")
    ax.grid(True, axis="y")
    clean(ax)
    stamp(fig)
    save(fig, P("fig-04-06-patterns.png"))

print("figures written to", OUT)
