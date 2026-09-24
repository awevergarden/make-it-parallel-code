"""figs_ch10.py -- figures for Chapter 10, Message Passing with MPI.

Usage: python3 kit/figs_ch10.py OUTDIR
Figure 10.3 plots real local MPI ping-pong times with a fitted model;
Figure 10.5 is a MODEL (distmodel.py, heatmodel.py) from one-process rates.
"""
import sys, os, csv, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import distmodel as dm, heatmodel as hm
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch10")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)
VALS = json.load(open(os.path.join(DATA, "values.json")))
RANK = [INK, BLUE, ORANGE, TEAL]

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

banner(P("fig-10-00-banner.png"), seed=70, mode="blocks")

# ------------------------------------------------ 10.1 SPMD launch (schematic)
fig, ax = canvas(FIG_W, 1.62)
box(ax, 0.02, 0.62, 1.32, 0.34, "mpirun -np 4 ./heat", fc=PAPER, ec=GRAY,
    fs=6.6, r=0.03)
ax.texts[-1].set_family(MONO)
for k in range(4):
    x = 1.62 + k * 0.74
    box(ax, x, 0.85, 0.66, 0.42, f"rank {k}\nsame program", fc=RANK[k], ec="none",
        tc=WHITE, fs=6.4, r=0.04)
    box(ax, x, 0.3, 0.66, 0.36, f"its own\nrows", fc=PAPER, ec=RANK[k], tc=INK,
        fs=6.2, r=0.03)
    line(ax, [x + 0.33, x + 0.33], [0.84, 0.67], color=GRAY, lw=0.8)
xa, xb = 1.62, 1.62 + 3 * 0.74 + 0.66
line(ax, [xa, xa, xb, xb], [1.33, 1.4, 1.4, 1.33], color=GRAY, lw=0.8)
arrow(ax, 0.68, 0.98, 0.68, 1.4, color=GRAY, lw=0.8, ms=5, style="-")
line(ax, [0.68, xa], [1.4, 1.4], color=GRAY, lw=0.8)
ax.text((xa + xb) / 2, 1.44, "starts 4 copies", ha="center", fontsize=6.5,
        color=GRAY)
ax.text(1.62, 0.1, "Each process learns its rank and size, and picks its data "
        "from them.", fontsize=6.5, color=GRAY)
save(fig, P("fig-10-01-spmd.png"))

# ------------------------------------------------ 10.2 eager vs rendezvous (schematic)
fig, ax = canvas(FIG_W, 1.8)
def panel(x0, title, rendezvous):
    ax.text(x0, 1.75, title, fontsize=7.5, weight="bold", va="top")
    for k, lab in enumerate(("sender", "receiver")):
        xx = x0 + 0.3 + k * 1.3
        ax.text(xx, 1.47, lab, ha="center", fontsize=6.8, color=GRAY)
        line(ax, [xx, xx], [1.38, 0.12], color=LIGHT, lw=1.5)
    s, r = x0 + 0.3, x0 + 1.6
    if not rendezvous:
        arrow(ax, s, 1.25, r, 1.05, color=BLUE, lw=1.1, ms=6)
        ax.text((s + r) / 2, 1.2, "header + data", fontsize=6.3, color=BLUE,
                ha="center")
        ax.text(s - 0.05, 1.0, "Send\nreturns", fontsize=6.3, color=TEALD,
                ha="right", va="center", linespacing=1.05)
        ax.text(r + 0.05, 0.55, "Recv copies\nfrom buffer", fontsize=6.3,
                color=GRAY, va="center", linespacing=1.05)
    else:
        arrow(ax, s, 1.25, r, 1.08, color=BLUE, lw=1.1, ms=6)
        ax.text((s + r) / 2, 1.22, "ready to send?", fontsize=6.3, color=BLUE,
                ha="center")
        arrow(ax, r, 0.78, s, 0.6, color=ORANGE, lw=1.1, ms=6)
        ax.text((s + r) / 2, 0.76, "go (Recv posted)", fontsize=6.3,
                color=ORANGE, ha="center")
        arrow(ax, s, 0.5, r, 0.32, color=BLUE, lw=1.1, ms=6)
        ax.text((s + r) / 2, 0.46, "data", fontsize=6.3, color=BLUE, ha="center")
        ax.text(s - 0.05, 0.9, "Send\nwaits", fontsize=6.3, color=ORANGE,
                ha="right", va="center", linespacing=1.05)
panel(0.3, "(a) Eager: small messages", False)
line(ax, [2.33, 2.33], [0.1, 1.7], color=LIGHT, lw=0.8)
panel(2.55, "(b) Rendezvous: large messages", True)
save(fig, P("fig-10-02-protocols.png"))

# ------------------------------------------------ 10.3 MPI ping-pong (measured)
d = {}
for r in csv.DictReader(open(os.path.join(DATA, "pingpong.csv"))):
    d.setdefault(int(r["bytes"]), []).append(float(r["microseconds"]))
n = sorted(d); t = [st.median(d[k]) for k in n]
fig, ax = plt.subplots(figsize=(FIG_W, 2.1), layout="constrained")
ax.scatter(n, t, color=BLUE, marker="o", s=16, zorder=3, label="MPI (measured)")
xs = np.logspace(np.log10(6), np.log10(3e6), 100)
al, be = float(VALS["a_mpi"]), float(VALS["b_mpi"]) * 1000
ax.plot(xs, al + xs / be, color=BLUE, lw=0.9, ls="--", label="fitted α + n/β")
ax.axvline(4096, color=GRAY, lw=0.7, ls=":")
ax.text(4400, 60, "eager\nlimit", fontsize=6.5, color=GRAY, va="center",
        linespacing=1.05)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("Message size (bytes, log scale)")
ax.set_ylabel("One-way time (µs, log scale)")
ax.grid(True, which="major")
ax.legend(loc="upper left", frameon=False, fontsize=7)
clean(ax)
save(fig, P("fig-10-03-pingpong.png"))

# ------------------------------------------------ 10.4 topology + column type (schematic)
fig, ax = canvas(FIG_W, 2.05)
ax.text(0.05, 2.0, "(a) 6 ranks in a 3 × 2 Cartesian grid", fontsize=7.5,
        weight="bold", va="top")
cw_, chh = 0.62, 0.36
pos = {}
for r in range(3):
    for c in range(2):
        rank = r * 2 + c
        x, y = 0.3 + c * (cw_ + 0.22), 1.35 - r * (chh + 0.18)
        pos[rank] = (x, y)
        hl = rank == 3
        nb = rank in (1, 5, 2)
        box(ax, x, y, cw_, chh, f"rank {rank}\n({r},{c})",
            fc=ORANGE if hl else (BLUE if nb else PAPER),
            ec="none" if (hl or nb) else GRAY, tc=WHITE if (hl or nb) else INK,
            fs=6.5, r=0.04)
def mid(k, dx=0, dy=0):
    x, y = pos[k]
    return x + cw_ / 2 + dx, y + chh / 2 + dy
for k, lab in [(1, "up"), (5, "down"), (2, "left")]:
    (x0, y0), (x1, y1) = mid(3), mid(k)
    lo, hi = (0.36, 0.64) if y0 == y1 else (0.3, 0.68)   # stay in the gap
    arrow(ax, x0 + (x1 - x0) * lo, y0 + (y1 - y0) * lo,
          x0 + (x1 - x0) * hi, y0 + (y1 - y0) * hi, color=INK, lw=1.1, ms=7)
ax.text(1.8, 0.72, "rank 3's right\nneighbor:\nMPI_PROC_NULL", fontsize=6.2,
        color=GRAY, va="center", linespacing=1.1)
line(ax, [2.45, 2.45], [0.05, 1.95], color=LIGHT, lw=0.8)
ax.text(2.6, 2.0, "(b) Column 2 as one MPI_Type_vector", fontsize=7.5,
        weight="bold", va="top")
cs_ = 0.3
for i in range(4):
    for j in range(5):
        x, y = 2.65 + j * cs_, 1.45 - i * cs_
        on = j == 2
        ax.add_patch(Rectangle((x, y), cs_ - 0.03, cs_ - 0.03,
                     fc=ORANGE if on else PAPER, ec="none" if on else LIGHT, lw=0.6))
        ax.text(x + (cs_ - 0.03) / 2, y + (cs_ - 0.03) / 2, str(5 * i + j),
                ha="center", va="center", fontsize=6.5,
                color=WHITE if on else INK)
ax.text(2.65, 0.28, "count 4, block length 1, stride 5:\n"
        "four blocks of one double, five apart", fontsize=6.4, color=GRAY,
        va="center", linespacing=1.15)
save(fig, P("fig-10-04-topology.png"))

# ------------------------------------------------ 10.5 halo decomposition (schematic)
fig, ax = canvas(FIG_W, 2.2)
ax.text(0.05, 2.15, "(a) Global grid", fontsize=7.5, weight="bold", va="top")
gx, gw, rh = 0.15, 1.2, 0.13
glob = ["edge"] + [0] * 4 + [1] * 4 + [2] * 4 + ["edge"]
for k, who in enumerate(glob):
    y = 1.9 - (k + 1) * rh
    fc = LIGHT if who == "edge" else RANK[who]
    ax.add_patch(Rectangle((gx, y), gw, rh - 0.015, fc=fc, ec="none"))
for k in range(3):
    ax.text(gx + gw + 0.05, 1.9 - (2.5 + 4 * k + 1) * rh + rh / 2,
            f"rank {k}", fontsize=6.5, va="center", color=RANK[k])
ax.text(2.0, 2.15, "(b) What each rank stores", fontsize=7.5, weight="bold",
        va="top")
for k in range(3):
    x0 = 2.0 + k * 0.85
    halo_top = LIGHT if k == 0 else RANK[k - 1]
    halo_bot = RANK[k + 1] if k < 2 else LIGHT
    rows = [halo_top] + [RANK[k]] * 4 + [halo_bot]
    for r, fc in enumerate(rows):
        y = 1.75 - r * 0.2
        halo = r in (0, 5)
        ax.add_patch(Rectangle((x0, y), 0.7, 0.17, fc=fc, ec=ORANGE if halo else "none",
                     lw=1.0, ls="--", alpha=0.45 if halo else 1.0))
    ax.text(x0 + 0.35, 0.45, f"rank {k}", ha="center", fontsize=6.6, color=RANK[k],
            weight="bold")
# rows: r = 0 top halo (y 1.75), r = 1..4 owned (y 1.55 ... 0.95), r = 5 bottom halo (0.75)
for k in range(2):
    x0 = 2.0 + k * 0.85                       # rank k; rank k + 1 starts at x0 + 0.85
    # rank k's last owned row -> rank k+1's top halo
    arrow(ax, x0 + 0.71, 1.035, x0 + 0.84, 1.835, color=ORANGE, lw=0.9, ms=5)
    # rank k+1's first owned row -> rank k's bottom halo
    arrow(ax, x0 + 0.84, 1.635, x0 + 0.71, 0.835, color=ORANGE, lw=0.9, ms=5)
ax.text(2.0, 0.22, "Dashed rows are halos: copies of a neighbor's edge row,\n"
        "refreshed by MPI_Sendrecv before every step.", fontsize=6.5, color=GRAY,
        va="center", linespacing=1.15)
save(fig, P("fig-10-05-halo.png"))

# ------------------------------------------------ 10.6 predicted scaling (MODEL)
rate = {}
for r in csv.DictReader(open(os.path.join(DATA, "rates.csv"))):
    rate.setdefault((r["version"], int(r["n"])), []).append(float(r["mlups"]))
rate = {k: st.median(x) * 1e6 for k, x in rate.items()}
R = {"l2": rate[("v6", 256)], "l3": rate[("v6", 1024)], "mem": rate[("v6", 4096)]}
r1 = rate[("v1", 4096)]
ps = 2 ** np.arange(0, 9)
fig, ax = plt.subplots(figsize=(FIG_W, 2.45), layout="constrained")
ax.plot(ps, ps, color=GRAY, lw=0.9, ls=":", label="ideal: speedup = p")
for nn, c, mk, ls in [(4096, BLUE, "o", "-"), (16384, TEALD, "s", "--")]:
    ax.plot(ps, [dm.speedup(nn, int(p), R, r1) for p in ps], color=c, marker=mk,
            ms=3.8, lw=1.2, ls=ls, label=f"MPI, {nn:,} × {nn:,} grid")
sp = np.arange(1, 17)
ax.plot(sp, [hm.speedup(4096, int(p), R, r1) for p in sp], color=ORANGE, lw=1.2,
        ls="-.", label="threads on one node, 4,096 grid")
ax.set_xscale("log", base=2); ax.set_yscale("log", base=2)
ax.set_xticks(ps, [str(int(p)) for p in ps])
ax.set_yticks([1, 4, 16, 64, 256, 1024], ["1", "4", "16", "64", "256", "1,024"])
ax.set_xlabel("Nodes p, one process each (log scale)")
ax.set_ylabel("Predicted speedup\nover v1 (log scale)")
ax.grid(True, which="major")
ax.legend(loc="upper left", frameon=False, fontsize=6.8)
ax.text(0.99, 0.02, "model, not measured", transform=ax.transAxes, ha="right",
        fontsize=7, color=GRAY, style="italic")
clean(ax)
save(fig, P("fig-10-06-model.png"))
print("figures written to", OUT)
