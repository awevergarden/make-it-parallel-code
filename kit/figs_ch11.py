"""figs_ch11.py -- figures for Chapter 11, Networks, Clusters and Clouds.

Usage: python3 kit/figs_ch11.py OUTDIR
Figure 11.4 mixes our measurements (Chapters 9-11) with one published
measurement (De Sensi et al., SC20), marked differently.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALS = json.load(open(os.path.join(ROOT, "data", "ch11", "values.json")))
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

banner(P("fig-11-00-banner.png"), seed=77, mode="blocks")

# ------------------------------------------------ 11.1 anatomy of a cluster
fig, ax = canvas(FIG_W, 2.05)
box(ax, 0.05, 1.45, 0.85, 0.42, "you\n(ssh)", fc=PAPER, ec=GRAY, fs=6.8)
box(ax, 1.15, 1.45, 1.0, 0.42, "login node\ncompile, submit", fc=BLUE, ec="none",
    tc=WHITE, fs=6.6)
box(ax, 2.45, 1.45, 1.05, 0.42, "scheduler\n(Slurm)", fc=AMBER, ec="none", fs=6.8)
arrow(ax, 0.92, 1.66, 1.13, 1.66, color=GRAY, ms=6)
arrow(ax, 2.17, 1.66, 2.43, 1.66, color=GRAY, ms=6)
for k in range(6):
    x = 0.35 + k * 0.62
    box(ax, x, 0.62, 0.5, 0.36, f"node\n{k + 1}", fc=INK, ec="none", tc=WHITE,
        fs=6.3, r=0.03)
    line(ax, [x + 0.25, x + 0.25], [0.62, 0.45], color=ORANGE, lw=1.0)
line(ax, [0.3, 4.1], [0.45, 0.45], color=ORANGE, lw=2.2)
ax.text(4.15, 0.45, "fast\nnetwork", fontsize=6.4, color=ORANGE, va="center",
        linespacing=1.05)
arrow(ax, 2.97, 1.43, 2.3, 1.0, color=GRAY, ms=6)
ax.text(3.0, 1.2, "starts jobs on\nfree nodes", fontsize=6.3, color=GRAY,
        linespacing=1.05)
box(ax, 1.4, 0.05, 1.6, 0.28, "shared parallel file system", fc=TEAL, ec="none",
    fs=6.5, r=0.03)
line(ax, [2.2, 2.2], [0.33, 0.45], color=ORANGE, lw=1.0)
save(fig, P("fig-11-01-cluster.png"))

# ------------------------------------------------ 11.2 topologies (8 or 16 nodes)
fig, axs = plt.subplots(1, 4, figsize=(FIG_W, 1.35))
def draw(ax, pts, edges, title):
    for a_, b_ in edges:
        ax.plot([pts[a_][0], pts[b_][0]], [pts[a_][1], pts[b_][1]], color=GRAY, lw=0.8,
                zorder=1)
    ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=14, color=BLUE, zorder=2)
    ax.set_title(title, fontsize=7.2, pad=2)
    ax.set_aspect("equal"); ax.axis("off")
n = 8
th = [2 * np.pi * k / n for k in range(n)]
draw(axs[0], [(np.cos(t), np.sin(t)) for t in th], [(k, (k + 1) % n) for k in range(n)],
     "ring")
g = [(c, r) for r in range(4) for c in range(4)]
me = [(r * 4 + c, r * 4 + c + 1) for r in range(4) for c in range(3)] + \
     [(r * 4 + c, (r + 1) * 4 + c) for r in range(3) for c in range(4)]
draw(axs[1], g, me, "2D mesh")
te = me + [(r * 4, r * 4 + 3) for r in range(4)] + [(c, 12 + c) for c in range(4)]
ax_ = axs[2]
draw(ax_, g, [e for e in te if e in me], "2D torus")
for k in range(4):                        # wraparound links: stubs at every edge
    ax_.plot([-0.55, 0], [k, k], color=ORANGE, lw=0.9, ls="--", zorder=1)
    ax_.plot([3, 3.55], [k, k], color=ORANGE, lw=0.9, ls="--", zorder=1)
    ax_.plot([k, k], [-0.55, 0], color=ORANGE, lw=0.9, ls="--", zorder=1)
    ax_.plot([k, k], [3, 3.55], color=ORANGE, lw=0.9, ls="--", zorder=1)
cube = [(0, 0), (1, 0), (0, 1), (1, 1), (0.45, 0.35), (1.45, 0.35), (0.45, 1.35), (1.45, 1.35)]
ce = [(u, u ^ (1 << i)) for u in range(8) for i in range(3) if u < u ^ (1 << i)]
draw(axs[3], cube, ce, "3D hypercube")
fig.subplots_adjust(left=0.01, right=0.99, top=0.85, bottom=0.02, wspace=0.25)
save(fig, P("fig-11-02-topologies.png"))

# ------------------------------------------------ 11.3 store-and-forward vs cut-through
fig, ax = canvas(FIG_W, 1.75)
def lane(y, label):
    ax.text(0.05, y + 0.09, label, fontsize=6.6, va="center")
seg, hops = 0.55, 3
ax.text(0.05, 1.7, "(a) Store-and-forward: each switch waits for the whole packet",
        fontsize=7.2, weight="bold", va="top")
for h in range(hops):
    lane(1.25 - h * 0.22, f"link {h + 1}")
    box(ax, 0.75 + h * seg, 1.25 - h * 0.22, seg - 0.03, 0.17, "packet", fc=BLUE,
        ec="none", tc=WHITE, fs=6, r=0.02)
ax.text(0.75 + hops * seg + 0.05, 0.9, "time ≈ hops × packet time", fontsize=6.5,
        color=BLUE, va="center")
ax.text(0.05, 0.72, "(b) Cut-through: the head moves on while the tail arrives",
        fontsize=7.2, weight="bold", va="top")
d = 0.08
for h in range(hops):
    lane(0.3 - h * 0.12 + 0.2 - 0.2, "") if False else None
    box(ax, 0.75 + h * d, 0.36 - h * 0.12, seg - 0.03, 0.1, "", fc=TEALD, ec="none",
        r=0.02)
    ax.text(0.7, 0.41 - h * 0.12, f"link {h + 1}", fontsize=6.2, ha="right", va="center")
ax.text(0.75 + 2 * d + seg + 0.05, 0.25, "time ≈ hops × switch delay + packet time",
        fontsize=6.5, color=TEALD, va="center")
arrow(ax, 0.75, 0.02, 4.4, 0.02, color=GRAY, ms=6)
ax.text(4.42, 0.05, "time", fontsize=6.3, color=GRAY, va="bottom", ha="right")
save(fig, P("fig-11-03-switching.png"))

# ------------------------------------------------ 11.4 latency-bandwidth landscape
pts = [("MPI, same machine (Ch. 10)", float(VALS["a_mpi"]), float(VALS["b_mpi"]), BLUE, "o", True),
       ("pipe (Ch. 9)", float(VALS["a_pipe"]), float(VALS["b_pipe"]), TEALD, "s", True),
       ("TCP loopback (Ch. 9)", float(VALS["a_tcp"]), float(VALS["b_tcp"]), ORANGE, "^", True),
       ("internet, via proxy (Ch. 11)", float(VALS["wan_alpha_ms"]) * 1000,
        float(VALS["wan_mbps"]) / 1000, INK, "D", True),
       ("Slingshot MPI, 100 Gb/s NIC (published)", 2.5, 12.1, PURPLE, "*", False),
       ("Chapter 10 model assumption", 2.0, 10.0, GRAY, "o", None)]
fig, ax = plt.subplots(figsize=(FIG_W, 2.3), layout="constrained")
for lab, al, be, c, mk, measured in pts:
    if measured is None:
        ax.scatter(al, be, s=40, facecolors="none", edgecolors=c, lw=1.1, label=lab, zorder=3)
    else:
        ax.scatter(al, be, s=46 if mk == "*" else 26, color=c, marker=mk, label=lab, zorder=3)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(0.5, 1e5); ax.set_ylim(0.05, 60)
ax.set_xlabel("Latency α (µs, log scale)")
ax.set_ylabel("Bandwidth β\n(GB/s, log scale)")
ax.grid(True, which="major")
ax.legend(loc="lower left", frameon=False, fontsize=6.5, handletextpad=0.3)
ax.text(0.99, 0.97, "better: up and left", transform=ax.transAxes, ha="right",
        va="top", fontsize=6.6, color=GRAY, style="italic")
clean(ax)
save(fig, P("fig-11-04-landscape.png"))
print("figures written to", OUT)
