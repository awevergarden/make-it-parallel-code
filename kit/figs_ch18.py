"""figs_ch18.py -- figures for Chapter 18, Elections, Transactions and Consensus.

Usage: python3 kit/figs_ch18.py OUTDIR
Figures 18.1 and 18.4 plot the chapter's simulations (elect.c, raftsim.c).
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch18")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

banner(P("fig-18-00-banner.png"), seed=126, mode="blocks")

# ------------------------------------------------ 18.1 election messages (simulated)
el = list(csv.DictReader(open(os.path.join(DATA, "elect.csv"))))
n = [int(r["n"]) for r in el]
fig, ax = plt.subplots(figsize=(FIG_W, 2.1), layout="constrained")
for key, lab, c, mk, ls in (("bully_lowest_detects", "bully, lowest process notices", ORANGE, "^", "--"),
                            ("ring_worst", "ring, worst ID order", INK, "s", "-."),
                            ("ring_random", "ring, random ID order", BLUE, "o", "-"),
                            ("ring_best", "ring, best ID order", TEALD, "D", ":")):
    ax.plot(n, [float(r[key]) for r in el], color=c, marker=mk, ms=3.5, lw=1.2, ls=ls, label=lab)
ax.set_xscale("log", base=2); ax.set_yscale("log")
ax.set_xticks(n, [str(k) for k in n])
ax.set_xlabel("Processes (log scale)")
ax.set_ylabel("Messages per election\n(log scale)")
ax.grid(True, which="major")
ax.legend(loc="upper left", frameon=False, fontsize=6.6)
clean(ax)
save(fig, P("fig-18-01-elections.png"))

# ------------------------------------------------ 18.2 two-phase commit (schematic)
fig, ax = canvas(FIG_W, 1.85)
lanes = {"coordinator": 1.55, "participant 1": 1.1, "participant 2": 0.7, "participant 3": 0.3}
for lab, y in lanes.items():
    ax.text(0.05, y, lab, fontsize=6.5, va="center")
    line(ax, [0.95, 4.55], [y, y], color=LIGHT, lw=0.8)
for y in (1.1, 0.7, 0.3):
    arrow(ax, 1.0, 1.55, 1.25, y + 0.03, color=BLUE, ms=4)
    arrow(ax, 1.45, y, 1.75, 1.52, color=TEALD, ms=4)
ax.text(1.05, 1.72, "PREPARE", fontsize=5.8, color=BLUE)
ax.text(1.55, 1.72, "votes: YES", fontsize=5.8, color=TEALD)
ax.add_patch(Rectangle((1.9, 1.49), 1.55, 0.12, fc=LIGHT, ec=GRAY, lw=0.5, hatch="xx"))
ax.text(2.67, 1.72, "coordinator down", fontsize=5.8, color=GRAY, ha="center")
for y in (1.1, 0.7, 0.3):
    ax.add_patch(Rectangle((1.9, y - 0.06), 1.55, 0.12, fc=AMBER, ec="none", alpha=0.8))
ax.text(2.67, 0.08, "blocked: voted YES, may not decide alone, and nobody knows the outcome",
        fontsize=6, color=INK, ha="center")
for y in (1.1, 0.7, 0.3):
    arrow(ax, 3.5, 1.55, 3.75, y + 0.03, color=ORANGE, ms=4)
ax.text(3.55, 1.72, "COMMIT", fontsize=5.8, color=ORANGE)
save(fig, P("fig-18-02-twopc.png"))

# ------------------------------------------------ 18.3 Raft roles (schematic)
fig, ax = canvas(FIG_W, 1.55)
box(ax, 0.2, 0.55, 1.0, 0.45, "follower", fc=BLUE, ec="none", tc=WHITE, fs=7)
box(ax, 1.85, 0.55, 1.0, 0.45, "candidate", fc=AMBER, ec="none", tc=INK, fs=7)
box(ax, 3.5, 0.55, 1.0, 0.45, "leader", fc=TEALD, ec="none", tc=WHITE, fs=7)
arrow(ax, 1.22, 0.86, 1.83, 0.86, color=GRAY, ms=5)
ax.text(1.52, 1.05, "timeout:\nnew term", fontsize=6, ha="center", color=GRAY, linespacing=1.05)
arrow(ax, 2.87, 0.86, 3.48, 0.86, color=GRAY, ms=5)
ax.text(3.17, 1.05, "votes from\na majority", fontsize=6, ha="center", color=GRAY, linespacing=1.05)
arrow(ax, 1.83, 0.66, 1.22, 0.66, color=GRAY, ms=5)
ax.text(1.52, 0.4, "hears a leader\nor higher term", fontsize=6, ha="center", color=GRAY, linespacing=1.05)
ax.add_patch(Arc((2.35, 0.55), 3.3, 0.8, theta1=180, theta2=360, color=GRAY, lw=0.8))
ax.text(2.35, 0.03, "sees a higher term: step down", fontsize=6, ha="center", color=GRAY)
ax.add_patch(Arc((2.35, 1.0), 0.5, 0.5, theta1=20, theta2=160, color=GRAY, lw=0.8))
ax.text(2.35, 1.32, "split vote: timeout, try again", fontsize=6, ha="center", color=GRAY)
save(fig, P("fig-18-03-raft-roles.png"))

# ------------------------------------------------ 18.4 recovery times (simulated)
fig, ax = plt.subplots(figsize=(FIG_W, 1.95), layout="constrained")
bins = np.arange(0, 1500, 50)
for m, lab, c, h in (("raft", "random timeouts, 150–300 ms", BLUE, None),
                     ("fixed", "fixed timeouts, 150 ms", ORANGE, "///")):
    x = [float(l) for l in open(os.path.join(DATA, f"recovery_{m}.txt"))]
    w = np.ones(len(x)) / len(x) * 100
    ax.hist(np.clip(x, 0, 1449), bins=bins, weights=w, color=c, alpha=0.75, hatch=h,
            edgecolor=WHITE, lw=0.3, label=lab)
ax.set_xlabel("Time from leader crash to new leader (ms; longer times shown at 1,450)")
ax.set_ylabel("Share of\nrecoveries (%)")
ax.legend(loc="upper right", frameon=False, fontsize=6.8)
ax.grid(True, axis="y")
clean(ax)
save(fig, P("fig-18-04-recovery.png"))

# ------------------------------------------------ 18.5 SimQueue complete (schematic)
fig, ax = canvas(FIG_W, 2.05)
box(ax, 0.05, 0.85, 0.72, 0.4, "clients", fc=PAPER, ec=GRAY, fs=6.6)
for k in range(3):
    x = 1.15 + k * 0.62
    box(ax, x, 1.2 if k == 1 else 0.9, 0.52, 0.42, "leader" if k == 1 else "follower",
        fc=TEALD if k == 1 else BLUE, ec="none", tc=WHITE, fs=5.8)
ax.text(1.95, 1.8, "scheduler: Raft-replicated job log (Ch. 18)", fontsize=6.3, ha="center")
arrow(ax, 0.79, 1.2, 1.75, 1.52, color=GRAY, ms=5)          # clients -> leader
arrow(ax, 1.77, 1.3, 1.62, 1.2, color=TEALD, ms=4)          # leader replicates
arrow(ax, 2.29, 1.3, 2.39, 1.2, color=TEALD, ms=4)
ax.text(2.02, 0.75, "replicates\nthe log", fontsize=5.8, color=TEALD, ha="center", linespacing=1.0)
for k in range(3):
    y = 1.45 - k * 0.55
    box(ax, 3.55, y, 1.0, 0.4, f"worker {k + 1}", fc=INK, ec="none", tc=WHITE, fs=6.2)
    arrow(ax, 2.29, 1.45, 3.53, y + 0.2, color=GRAY, ms=5)  # leader -> workers
ax.text(3.2, 0.1, "leases + fencing tokens (Ch. 17)\nheartbeats (Ch. 17)", fontsize=6,
        color=GRAY, ha="center", linespacing=1.1)
ax.text(0.05, 0.3, "logs stamped with hybrid\nlogical clocks (Ch. 16)", fontsize=6, color=GRAY,
        linespacing=1.1)
ax.text(1.2, 0.45, "poll-based servers,\nwork queues (Ch. 7, 9)", fontsize=6, color=GRAY,
        linespacing=1.1)
save(fig, P("fig-18-05-simqueue.png"))
print("figures written to", OUT)
