"""figs_ch16.py -- figures for Chapter 16, Time and Order.

Usage: python3 kit/figs_ch16.py OUTDIR
Figure 16.3's timestamps are computed by the clock rules below, not typed;
Figure 16.2 plots the REAL Cristian runs (simulated server clock).
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

banner(P("fig-16-00-banner.png"), seed=112, mode="blocks")

# ------------------------------------------------ 16.1 SimQueue (schematic)
fig, ax = canvas(FIG_W, 1.75)
box(ax, 0.05, 0.7, 0.8, 0.45, "clients\nsubmit jobs", fc=PAPER, ec=GRAY, fs=6.6)
box(ax, 1.25, 0.55, 1.1, 0.75, "scheduler\n(job log,\nqueue)", fc=BLUE, ec="none", tc=WHITE, fs=6.8)
arrow(ax, 0.87, 0.92, 1.23, 0.92, color=GRAY, ms=6)
for k in range(3):
    y = 1.25 - k * 0.5
    box(ax, 2.9, y, 1.0, 0.36, f"worker {k + 1}\nruns HeatSim", fc=TEALD, ec="none", tc=WHITE, fs=6.2)
    arrow(ax, 2.37, 0.92, 2.88, y + 0.18, color=GRAY, ms=5)
    ax.text(3.95, y + 0.18, f"log {k + 1}", fontsize=6.2, color=ORANGE, va="center")
ax.text(1.25, 0.35, "log 0", fontsize=6.2, color=ORANGE)
ax.text(0.05, 0.1, "Every machine logs events with its own clock: in which order did they happen?",
        fontsize=6.6, color=INK)
save(fig, P("fig-16-01-simqueue.png"))

# ------------------------------------------------ 16.2 space-time diagram (computed)
# events: (process, x, kind, message id); sends name their message
events = [(0, 0.6, "local", None), (0, 1.3, "send", "m1"), (1, 2.0, "recv", "m1"),
          (2, 1.0, "local", None), (1, 2.7, "send", "m2"), (2, 3.3, "recv", "m2"),
          (1, 3.6, "local", None), (2, 3.9, "send", "m3"), (0, 4.4, "recv", "m3"),
          (0, 2.3, "local", None)]
events.sort(key=lambda e: e[1])                     # process in time order
L = [0, 0, 0]; V = [[0] * 3 for _ in range(3)]; stamp = {}; sent = {}
labels = []
for proc, x, kind, msg in events:
    if kind == "recv":
        l, vv = sent[msg]
        L[proc] = max(L[proc], l) + 1
        V[proc] = [max(a, b) for a, b in zip(V[proc], vv)]
        V[proc][proc] += 1
    else:
        L[proc] += 1
        V[proc][proc] += 1
    if kind == "send":
        sent[msg] = (L[proc], list(V[proc]))
    labels.append((proc, x, kind, msg, L[proc], list(V[proc])))
fig, ax = canvas(FIG_W, 1.75)
ys = {0: 1.45, 1: 0.9, 2: 0.35}
for proc, y in ys.items():
    line(ax, [0.4, 4.6], [y, y], color=GRAY, lw=0.8)
    ax.text(0.05, y, f"P{proc}", fontsize=7, va="center", weight="bold")
arrow(ax, 4.45, 0.08, 4.62, 0.08, color=GRAY, ms=5)
ax.text(4.4, 0.08, "time", fontsize=6, color=GRAY, ha="right", va="center")
pos = {}
for proc, x, kind, msg, l, vv in labels:
    pos[(msg, kind)] = (x, ys[proc])
    ax.scatter([x], [ys[proc]], s=16, color=ORANGE if kind != "local" else INK, zorder=4)
    dy = 0.13 if proc != 2 else -0.14
    ax.text(x, ys[proc] + dy, f"{l}  [{','.join(map(str, vv))}]", fontsize=5.6, ha="center",
            va="center", color=BLUE)
for msg in ("m1", "m2", "m3"):
    (x1, y1), (x2, y2) = pos[(msg, "send")], pos[(msg, "recv")]
    arrow(ax, x1, y1, x2, y2, color=ORANGE, ms=5)
save(fig, P("fig-16-03-clocks.png"))

# ------------------------------------------------ 16.3 Cristian (REAL, simulated clock)
cr = list(csv.DictReader(open(os.path.join(ROOT, "data", "ch16", "cristian.csv"))))
rtt = [float(r["rtt_ms"]) for r in cr]
er = [float(r["error_ms"]) for r in cr]
fig, ax = plt.subplots(figsize=(FIG_W, 2.0), layout="constrained")
xs = [0, max(rtt) * 1.05]
ax.fill_between(xs, [-x / 2 for x in xs], [x / 2 for x in xs], color=LIGHT, alpha=0.6,
                label="guaranteed range: ±RTT/2")
ax.scatter(rtt, er, s=14, color=BLUE, zorder=3, label="measured error of the estimate")
ax.axhline(0, color=GRAY, lw=0.6)
ax.set_xlabel("Round-trip time (ms)")
ax.set_ylabel("Estimate − true\nserver time (ms)")
ax.set_xlim(0, xs[1])
ax.legend(loc="lower left", frameon=False, fontsize=6.8)
ax.grid(True, axis="y")
clean(ax)
save(fig, P("fig-16-02-cristian.png"))
print("figures written to", OUT)
