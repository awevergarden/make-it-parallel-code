"""figs_ch03.py -- figures for Chapter 3, Measuring Speed Honestly.

Usage: python3 kit/figs_ch03.py OUTDIR
Measured figures read data/ch03/*.csv. When data/ch03/values.json says
"provisional": true (trial data), those figures carry a visible stamp.
"""
import sys, os, csv, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch03")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)
VALS = json.load(open(os.path.join(DATA, "values.json")))

def rows(name):
    with open(os.path.join(DATA, name)) as f:
        return list(csv.DictReader(f))

def stamp(fig):
    if VALS.get("provisional"):
        fig.text(0.99, 0.99, "PROVISIONAL · trial data", ha="right",
                 va="top", fontsize=7, color=ORANGE, weight="bold")

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

# ------------------------------------------------ 3.0 chapter banner
banner(P("fig-03-00-banner.png"), seed=21, mode="rise")

# ------------------------------------------------ 3.1 convergence (real output)
fig, ax = plt.subplots(figsize=(FIG_W, 2.2), layout="constrained")
conv = rows("convergence.csv")
for (n, color, marker, ls) in [(33, TEALD, "s", "-"), (65, BLUE, "o", "--"),
                               (129, ORANGE, "^", "-.")]:
    pts = [(int(r["steps"]), float(r["center"])) for r in conv
           if int(r["n"]) == n]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, ls=ls,
            marker=marker, ms=3.5, lw=1.1, label=f"{n} × {n} grid")
ax.axhline(25, color=INK, lw=0.8, ls=":")
ax.text(11, 26.2, "exact steady state: 25 °C", fontsize=7, color=INK,
        va="bottom")
ax.set_xscale("log")
ax.set_xlim(8, 1.3e5)
ax.set_ylim(0, 31)
ax.set_xlabel("Time steps (log scale)")
ax.set_ylabel("Center temperature (°C)")
ax.grid(True, axis="y")
ax.legend(loc="center left", frameon=False)
clean(ax)
save(fig, P("fig-03-01-convergence.png"))

# ------------------------------------------------ 3.2 run-to-run variation
rep = [float(r["seconds"]) for r in rows("repeat.csv")]
fig, ax = plt.subplots(figsize=(FIG_W, 1.8), layout="constrained")
ax.hist(rep, bins=15, color=BLUE, edgecolor=WHITE, lw=0.6, zorder=2)
m = st.median(rep)
ax.axvline(m, color=ORANGE, lw=1.3, ls="--", zorder=3)
ax.axvline(min(rep), color=INK, lw=1.0, ls=":", zorder=3)
top = ax.get_ylim()[1]
ax.text(m, top * 0.97, f" median {m:.3f} s", color=ORANGE, fontsize=7,
        va="top", ha="left")
ax.text(min(rep), top * 0.75, f" fastest {min(rep):.3f} s", color=INK,
        fontsize=7, va="top", ha="left")
ax.set_xlabel("Run time (seconds)")
ax.set_ylabel("Number of runs")
ax.grid(True, axis="y")
clean(ax)
stamp(fig)
save(fig, P("fig-03-02-variation.png"))

# ------------------------------------------------ 3.3 optimization levels
opt = {}
for r in rows("opt.csv"):
    opt.setdefault(r["opt"], []).append(float(r["seconds"]))
levels = ["O0", "O1", "O2", "O3"]
fig, ax = plt.subplots(figsize=(FIG_W, 1.9), layout="constrained")
meds = [st.median(opt[k]) for k in levels]
ax.bar(range(4), meds, color=[GRAY, TEAL, BLUE, TEALD], width=0.6, zorder=2)
for k, lev in enumerate(levels):
    ax.scatter([k] * len(opt[lev]), opt[lev], s=8, color=INK, zorder=3,
               marker="o", lw=0)
    ax.text(k, meds[k] + max(meds) * 0.03, f"{meds[k]:.2f} s", ha="center",
            va="bottom", fontsize=7.5, color=INK)
ax.set_xticks(range(4), ["-" + l for l in levels], family=MONO, fontsize=7.5)
ax.set_ylabel("Run time (seconds)")
ax.set_ylim(0, max(meds) * 1.2)
ax.grid(True, axis="y")
clean(ax)
stamp(fig)
save(fig, P("fig-03-03-opt-levels.png"))

# ------------------------------------------------ 3.4 Amdahl's law (model)
fig, ax = plt.subplots(figsize=(FIG_W, 2.5), layout="constrained")
p = 2.0 ** np.arange(0, 11)
ax.plot(p, p, color=GRAY, lw=0.9, ls=":", label="ideal (f = 0)")
for f, color, marker, ls in [(0.01, BLUE, "o", "-"), (0.05, TEALD, "s", "--"),
                             (0.10, ORANGE, "^", "-."), (0.25, INK, "D", "-")]:
    ax.plot(p, 1 / (f + (1 - f) / p), color=color, marker=marker, ms=3.5,
            lw=1.1, ls=ls, label=f"f = {f:g}")
    ax.text(1100, 1 / f, f"1/f = {1 / f:g}", fontsize=6.8, color=color,
            va="center")
ax.set_xscale("log", base=2)
ax.set_yscale("log", base=2)
ax.set_xticks(p, [f"{int(x):,}" for x in p])
ax.set_yticks([1, 4, 16, 64, 256, 1024], ["1", "4", "16", "64", "256", "1,024"])
ax.set_xlim(0.8, 3000)
ax.set_ylim(0.8, 1400)
ax.set_xlabel("Number of processors p (log scale)")
ax.set_ylabel("Speedup (log scale)")
ax.grid(True, which="major")
ax.legend(loc="upper left", frameon=False, fontsize=7)
ax.text(0.99, 0.02, "model", transform=ax.transAxes, ha="right",
        fontsize=7, color=GRAY, style="italic")
clean(ax)
save(fig, P("fig-03-04-amdahl.png"))

# ------------------------------------------------ 3.5 strong vs weak scaling
fig, ax = canvas(FIG_W, 1.72)
sx, h = 0.28, 0.22                      # inches per unit of work, bar height
def bar(x, y, units, label, fc, tc=WHITE):
    box(ax, x, y, units * sx, h, label, fc=fc, ec="none", tc=tc, fs=6.5,
        r=0.02)
def stack(x, y, p, units_each):
    hh = h / p
    for m in range(p):
        ax.add_patch(Rectangle((x, y + m * hh), units_each * sx, hh * 0.85,
                               fc=BLUE, ec="none"))
def panel(x0, title, weak):
    ax.text(x0, 1.68, title, fontsize=7.5, weight="bold", va="top")
    for k, (lab, pc) in enumerate([("1 core", 1), ("4 cores", 4)]):
        y = 1.05 - k * 0.42
        ax.text(x0 + 0.42, y + h / 2, lab, ha="right", va="center",
                fontsize=7)
        bx = x0 + 0.47
        bar(bx, y, 1, "s", INK)
        px = bx + sx + 0.01
        if pc == 1 and not weak:
            bar(px, y, 4, "parallel work", BLUE)
            note, end = "time 5", px + 4 * sx
        elif pc == 1:
            bar(px, y, 1, "p", BLUE)
            note, end = "time 2", px + sx
        else:
            stack(px, y, 4, 1)
            end = px + sx
            note = ("time 2, with 4×\nthe parallel work" if weak
                    else "time 2 (speedup 2.5)")
        ax.text(end + 0.06, y + h / 2, note, fontsize=7, va="center",
                linespacing=1.1)
panel(0.02, "(a) Strong scaling: same problem", False)
panel(2.42, "(b) Weak scaling: bigger problem", True)
line(ax, [2.36, 2.36], [0.05, 1.62], color=LIGHT, lw=0.8)
ax.text(0.02, 0.2, "The work is fixed, so the serial part\n"
        "limits speedup (Amdahl).", fontsize=6.8, color=GRAY, va="center",
        linespacing=1.15)
ax.text(2.42, 0.2, "The time is fixed, so the parallel work\n"
        "grows with the cores (Gustafson).", fontsize=6.8, color=GRAY,
        va="center", linespacing=1.15)
save(fig, P("fig-03-05-scaling.png"))

# ------------------------------------------------ 3.6 grid-size sweep
rate = {}
for r in rows("sweep.csv"):
    n, s, t = int(r["n"]), int(r["steps"]), float(r["seconds"])
    rate.setdefault(n, []).append((n - 2) ** 2 * s / t / 1e6)
ns = sorted(rate)
fig, ax = plt.subplots(figsize=(FIG_W, 2.2), layout="constrained")
ax.plot(ns, [st.median(rate[n]) for n in ns], color=BLUE, marker="o",
        ms=4, lw=1.2, zorder=3)
for n in ns:
    ax.scatter([n] * len(rate[n]), rate[n], s=6, color=INK, zorder=4, lw=0)
ax.set_xscale("log", base=2)
ax.set_xticks([64, 128, 256, 512, 1024, 2048, 4096],
              ["64", "128", "256", "512", "1,024", "2,048", "4,096"])
ax.set_ylim(0, max(max(v) for v in rate.values()) * 1.15)
ax.set_xlabel("Grid width n (log scale)")
ax.set_ylabel("Million cell updates\nper second")
ax.grid(True, axis="y")
sec = ax.secondary_xaxis("top")
mem = {64: "64 KB", 256: "1 MB", 1024: "16 MB", 4096: "256 MB"}
sec.set_xticks(list(mem), list(mem.values()), fontsize=6.8, color=GRAY)
sec.set_xlabel("memory for both grids", fontsize=7, color=GRAY)
sec.tick_params(length=2)
clean(ax)
stamp(fig)
save(fig, P("fig-03-06-size-sweep.png"))

# ------------------------------------------------ 3.7 profile: time vs instructions
if os.path.exists(os.path.join(DATA, "profile.csv")):
    steps = [("generate", "generate"), ("smooth", "smooth"), ("sort", "sort (30,000 values)")]
    tp = [float(VALS[f"prof_ins_{k}_pct"]) for k, _ in steps]
    ip = [float(VALS[f"cg_{k}_pct"]) for k, _ in steps]
    fig, ax = plt.subplots(figsize=(FIG_W, 1.75), layout="constrained")
    y = np.arange(len(steps))
    ax.barh(y + 0.19, tp, height=0.36, color=BLUE, label="share of run time (measured)")
    ax.barh(y - 0.19, ip, height=0.36, color=AMBER, hatch="///", edgecolor=WHITE,
            lw=0.3, label="share of instructions (callgrind)")
    for yy, a_, b_ in zip(y, tp, ip):
        ax.text(a_ + 1, yy + 0.19, f"{a_:.0f}%", va="center", fontsize=6.8)
        ax.text(b_ + 1, yy - 0.19, f"{b_:.0f}%", va="center", fontsize=6.8)
    ax.set_yticks(y, [lab for _, lab in steps])
    ax.set_xlim(0, 85)
    ax.set_xlabel("Percent of the whole program")
    ax.legend(loc="lower right", frameon=False, fontsize=6.8)
    clean(ax)
    stamp(fig)
    save(fig, P("fig-03-07-profile.png"))

print("figures written to", OUT)
