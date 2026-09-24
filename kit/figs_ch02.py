"""figs_ch02.py -- figures for Chapter 2, The C You Need."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)

# ------------------------------------------------ 2.0 chapter banner
banner(P("fig-02-00-banner.png"), seed=14, mode="rise")

# ------------------------------------------------ 2.1 compilation pipeline
fig, ax = canvas(FIG_W, 1.12)
files = [("heat.c", "C source"), ("heat.i", "expanded\nsource"),
         ("heat.s", "assembly\ncode"), ("heat.o", "object\ncode"),
         ("heat", "executable\nprogram")]
steps = ["preprocess", "compile", "assemble", "link"]
fw, gap, y0, fh = 0.5, 0.5, 0.62, 0.36
xs = [0.05 + k * (fw + gap) for k in range(len(files))]
for k, ((name, what), x) in enumerate(zip(files, xs)):
    last = k == len(files) - 1
    box(ax, x, y0, fw, fh, name, fc=INK if last else PAPER,
        ec=INK if last else GRAY, tc=WHITE if last else INK, fs=7.5,
        weight="bold", r=0.04)
    ax.text(x + fw / 2, y0 - 0.06, what, ha="center", va="top", fontsize=6.8,
            color=GRAY, linespacing=1.1)
for k, name in enumerate(steps):
    xa, xb = xs[k] + fw + 0.02, xs[k + 1] - 0.02
    arrow(ax, xa, y0 + fh / 2, xb, y0 + fh / 2, color=BLUE, lw=1.1, ms=7)
    ax.text((xa + xb) / 2, y0 + fh / 2 + 0.07, name, ha="center",
            va="bottom", fontsize=6.6, color=BLUE, weight="bold")
# libraries feed the linker
lx = (xs[3] + fw + xs[4]) / 2
box(ax, lx - 0.42, 0.0, 0.84, 0.28, "libraries\n(libc, libm)", fc=WHITE,
    ec=TEALD, tc=TEALD, fs=6.3, r=0.04, ls="--")
arrow(ax, lx, 0.3, lx, y0 + fh / 2 - 0.03, color=TEALD, lw=0.9, ms=6)
save(fig, P("fig-02-01-pipeline.png"))

# ------------------------------------------------ 2.2 memory, addresses, pointer
fig, ax = canvas(FIG_W, 1.6)
cw, chh, x0, y0 = 0.48, 0.34, 0.55, 0.72
addr = [1000 + 8 * k for k in range(8)]
content = {2: ("24.58", "t", AMBER), 5: ("1016", "p", TEAL)}
for k, a in enumerate(addr):
    x = x0 + k * cw
    fc = content[k][2] if k in content else PAPER
    ax.add_patch(Rectangle((x, y0), cw, chh, fc=fc, ec=GRAY, lw=0.6, zorder=2))
    if k in content:
        ax.text(x + cw / 2, y0 + chh / 2, content[k][0], ha="center",
                va="center", fontsize=7.5, weight="bold", color=INK, zorder=3)
        ax.text(x + cw / 2, y0 + chh + 0.05, content[k][1], ha="center",
                va="bottom", fontsize=8, weight="bold", color=INK,
                family=MONO)
    else:
        ax.text(x + cw / 2, y0 + chh / 2, "…", ha="center", va="center",
                fontsize=7, color=GRAY, zorder=3)
    ax.text(x + cw / 2, y0 - 0.05, str(a), ha="center", va="top",
            fontsize=6.8, color=GRAY)
ax.text(x0 - 0.05, y0 - 0.05, "address", ha="right", va="top", fontsize=6.8,
        color=GRAY)
# pointer arrow from p's cell to t's cell (curved, below)
pa = FancyArrowPatch((x0 + 5.5 * cw, y0 - 0.2), (x0 + 2.5 * cw, y0 - 0.2),
                     connectionstyle="arc3,rad=-0.25", arrowstyle="-|>",
                     mutation_scale=7, color=ORANGE, lw=1.1)
ax.add_patch(pa)
ax.text(x0 + 4 * cw, 0.1, "p holds the address of t, so *p means \"the value at 1016\"",
        ha="center", va="bottom", fontsize=6.8, color=ORANGE)
ax.text(x0 + 2.5 * cw, 1.55, "double t = 24.58;", ha="center", va="top",
        fontsize=7, family=MONO, color=INK)
ax.text(x0 + 5.5 * cw, 1.55, "double *p = &t;", ha="center", va="top",
        fontsize=7, family=MONO, color=INK)
save(fig, P("fig-02-02-pointer.png"))

# ------------------------------------------------ 2.4 row-major layout
fig, ax = canvas(FIG_W, 2.3)
n, gs, gx, gy = 4, 0.24, 0.55, 1.12
hot, nbr = 6, {2: "up", 10: "down", 5: "left", 7: "right"}
def cell_fc(k):
    if k == hot:
        return ORANGE
    if k in nbr:
        return TEAL
    return PAPER if (k // n) % 2 == 0 else LIGHT
for i in range(n):
    for j in range(n):
        k = i * n + j
        x, y = gx + j * gs, gy + (n - 1 - i) * gs
        ax.add_patch(Rectangle((x, y), gs, gs, fc=cell_fc(k), ec=WHITE,
                               lw=1.2, zorder=2))
        ax.text(x + gs / 2, y + gs / 2, str(k), ha="center", va="center",
                fontsize=7.5, weight="bold",
                color=WHITE if k == hot else INK, zorder=3)
for j in range(n):
    ax.text(gx + j * gs + gs / 2, gy + n * gs + 0.05, str(j), ha="center",
            va="bottom", fontsize=7, color=GRAY)
for i in range(n):
    ax.text(gx - 0.06, gy + (n - 1 - i) * gs + gs / 2, str(i), ha="right",
            va="center", fontsize=7, color=GRAY)
ax.text(gx + n * gs / 2, gy + n * gs + 0.2, "column j", ha="center",
        va="bottom", fontsize=7, color=GRAY)
ax.text(gx - 0.28, gy + n * gs / 2, "row i", ha="center", va="center",
        fontsize=7, color=GRAY, rotation=90)
ax.text(gx + n * gs / 2, gy - 0.1, "(a) the grid you imagine", ha="center",
        va="top", fontsize=7.5, weight="bold")
# explanation text to the right of the grid
tx = 2.05
ax.text(tx, 2.2, "Cell (i, j) lives at index  i·n + j", fontsize=7.5,
        weight="bold", va="top", color=INK)
ax.text(tx, 1.98, "Here n = 4, so cell (1, 2) is element 6:",
        fontsize=7.2, va="top", color=INK)
for r, (lab, off, val) in enumerate([("up", "− n", 2), ("down", "+ n", 10),
                                      ("left", "− 1", 5), ("right", "+ 1", 7)]):
    ax.text(tx + 0.1, 1.76 - r * 0.16, f"{lab:<5}", fontsize=7, va="top",
            color=TEALD, weight="bold")
    ax.text(tx + 0.5, 1.76 - r * 0.16, f"6 {off} = {val}", fontsize=7,
            va="top", color=INK)
ax.text(tx, 1.06, "Rows are contiguous; a column is\nevery n-th element.",
        fontsize=7, va="top", color=GRAY, linespacing=1.15)
# (b) the memory strip
sw, sy, sx = 0.27, 0.3, 0.13
for k in range(n * n):
    x = sx + k * sw
    ax.add_patch(Rectangle((x, sy), sw, 0.26, fc=cell_fc(k), ec=WHITE,
                           lw=1.0, zorder=2))
    ax.text(x + sw / 2, sy + 0.13, str(k), ha="center", va="center",
            fontsize=7, weight="bold", color=WHITE if k == hot else INK,
            zorder=3)
for r in range(n):
    xa, xb = sx + r * n * sw + 0.02, sx + (r + 1) * n * sw - 0.02
    line(ax, [xa, xa, xb, xb], [sy - 0.03, sy - 0.07, sy - 0.07, sy - 0.03],
         color=GRAY, lw=0.7)
    ax.text((xa + xb) / 2, sy - 0.1, f"row {r}", ha="center", va="top",
            fontsize=6.8, color=GRAY)
for tgt, rad in [(2, 0.4), (10, -0.4)]:
    xa, xb = sx + hot * sw + sw / 2, sx + tgt * sw + sw / 2
    ax.add_patch(FancyArrowPatch((xa, sy + 0.28), (xb, sy + 0.28),
                 connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>",
                 mutation_scale=6, color=TEALD, lw=0.9, zorder=4))
ax.text(sx + 4 * sw + sw / 2, sy + 0.33, "− n", ha="center", va="bottom", fontsize=7,
        color=TEALD, weight="bold")
ax.text(sx + 8 * sw + sw / 2, sy + 0.33, "+ n", ha="center", va="bottom", fontsize=7,
        color=TEALD, weight="bold")
ax.text(sx + 16 * sw, sy - 0.24, "(b) the array in memory", ha="right",
        va="top", fontsize=7.5, weight="bold")
save(fig, P("fig-02-04-row-major.png"))

# ------------------------------------------------ 2.5 array of pointers vs one block
fig, ax = canvas(FIG_W, 1.5)
# (a) array of row pointers, rows scattered
ax.text(0.05, 1.46, "(a) Array of row pointers: n + 1 allocations",
        fontsize=7.5, weight="bold", va="top")
px, py0 = 0.18, 0.22
for r in range(4):
    y = py0 + (3 - r) * 0.26
    ax.add_patch(Rectangle((px, y), 0.26, 0.2, fc=AMBER, ec=WHITE, lw=1))
    ax.text(px + 0.13, y + 0.1, "•", ha="center", va="center", fontsize=8,
            color=INK)
    rx = [0.95, 1.42, 0.75, 1.25][r]
    ry = y + [0.02, 0.0, -0.02, 0.02][r]
    for k in range(4):
        ax.add_patch(Rectangle((rx + k * 0.16, ry), 0.16, 0.2,
                               fc=PAPER if r % 2 == 0 else LIGHT, ec=WHITE,
                               lw=0.8))
    ax.text(rx + 0.66, ry + 0.1, f"row {r}", fontsize=6.5, va="center",
            color=GRAY)
    arrow(ax, px + 0.2, y + 0.11, rx - 0.02, ry + 0.1, color=GRAY, lw=0.7,
          ms=5)
ax.text(px + 0.13, py0 - 0.06, "rows", ha="center", va="top", fontsize=6.5,
        color=GRAY, family=MONO)
# (b) one contiguous block
bx = 2.5
ax.text(bx, 1.46, "(b) One contiguous block: 1 allocation",
        fontsize=7.5, weight="bold", va="top")
ax.add_patch(Rectangle((bx + 0.05, 0.9), 0.26, 0.2, fc=AMBER, ec=WHITE, lw=1))
ax.text(bx + 0.18, 1.0, "•", ha="center", va="center", fontsize=8, color=INK)
ax.text(bx + 0.37, 1.0, "grid", ha="left", va="center", fontsize=6.5,
        color=GRAY, family=MONO)
cs = 0.12
for k in range(16):
    ax.add_patch(Rectangle((bx + 0.05 + k * cs, 0.42), cs, 0.2,
                           fc=PAPER if (k // 4) % 2 == 0 else LIGHT, ec=WHITE,
                           lw=0.8))
arrow(ax, bx + 0.18, 0.89, bx + 0.18, 0.64, color=GRAY, lw=0.7, ms=5)
for r in range(4):
    ax.text(bx + 0.05 + (r * 4 + 2) * cs, 0.37, f"row {r}", ha="center",
            va="top", fontsize=6.3, color=GRAY)
ax.text(bx + 0.05, 0.12, "Neighbors are a fixed distance\napart; one free() releases all.",
        fontsize=6.8, color=GRAY, va="center", linespacing=1.15)
line(ax, [2.38, 2.38], [0.05, 1.42], color=LIGHT, lw=0.8)
save(fig, P("fig-02-05-layouts.png"))

# ------------------------------------------------ 2.6 process memory layout
fig, ax = canvas(FIG_W, 1.95)
bx, bw = 1.35, 1.25
segs = [  # (label, height, fill, text color, note)
    ("stack (main thread)", 0.26, BLUE, WHITE,
     "local variables, function arguments;\none stack per thread, grows down"),
    ("stack (thread 2)", 0.26, BLUE, WHITE, None),
    ("free space", 0.34, WHITE, GRAY, None),
    ("heap", 0.3, AMBER, INK, "malloc and calloc blocks; grows up"),
    ("static data", 0.23, TEAL, INK, "global and static variables"),
    ("code", 0.23, INK, WHITE, "the program's machine instructions"),
]
y = 1.78
tops = []
for label, h, fc, tc, note in segs:
    y -= h
    ax.add_patch(Rectangle((bx, y), bw, h - 0.02, fc=fc,
                           ec=GRAY if fc == WHITE else "none", lw=0.6,
                           ls="--" if fc == WHITE else "-"))
    ax.text(bx + bw / 2, y + (h - 0.02) / 2, label, ha="center", va="center",
            fontsize=7.2, color=tc, weight="bold")
    tops.append((y, h))
    if note:
        ny = y + (h - 0.02) / 2 if label != "stack (main thread)" else y
        ax.text(bx + bw + 0.12, ny, note, fontsize=6.8, color=INK,
                va="center", linespacing=1.15)
# growth arrows
arrow(ax, bx + bw - 0.12, tops[1][0] - 0.02, bx + bw - 0.12,
      tops[1][0] - 0.16, color=BLUE, lw=1, ms=6)
arrow(ax, bx + bw - 0.12, tops[3][0] + 0.3, bx + bw - 0.12,
      tops[3][0] + 0.44, color=ORANGE, lw=1, ms=6)
ax.text(bx - 0.1, 1.77, "high\naddresses", ha="right", va="top", fontsize=6.5,
        color=GRAY, linespacing=1.1)
ax.text(bx - 0.1, 0.02, "low\naddresses", ha="right", va="bottom",
        fontsize=6.5, color=GRAY, linespacing=1.1)
# brackets on the left: private vs shared
def bracket(ytop, ybot, text, color):
    xb = bx - 0.62
    line(ax, [xb + 0.06, xb, xb, xb + 0.06], [ytop, ytop, ybot, ybot],
         color=color, lw=1)
    ax.text(xb - 0.05, (ytop + ybot) / 2, text, ha="right", va="center",
            fontsize=6.8, color=color, weight="bold", linespacing=1.1)
bracket(1.76, tops[1][0], "private to\neach thread", BLUE)
bracket(tops[3][0] + tops[3][1] - 0.02, tops[5][0], "shared by\nall threads", ORANGE)
save(fig, P("fig-02-06-process.png"))

# ------------------------------------------------ 2.3 swapping cur and next
fig, ax = canvas(FIG_W, 1.18)
CS = 0.12                                    # cell size of the mini grids
YA, YB = 0.6, 0.1                            # lower edges of buffers A and B
def buffer(x, y, name, shade):
    for k in range(9):
        r, c = divmod(k, 3)
        ax.add_patch(Rectangle((x + c * CS, y + (2 - r) * CS), CS, CS,
                               fc=shade, ec=WHITE, lw=0.8))
    ax.text(x + 1.5 * CS, y - 0.03, name, ha="center", va="top", fontsize=6.8,
            color=GRAY, weight="bold")
def panel(ox, title, cur_to_a):
    ax.text(ox + 1.0, 1.17, title, ha="center", va="top", fontsize=7.5,
            weight="bold")
    buffer(ox + 1.25, YA, "buffer A", TEAL)
    buffer(ox + 1.25, YB, "buffer B", LIGHT)
    ca, cb = YA + 1.5 * CS, YB + 1.5 * CS    # vertical centers of A and B
    for k, (name, y) in enumerate([("cur", ca), ("next", cb)]):
        box(ax, ox + 0.08, y - 0.1, 0.5, 0.2, name, fc=AMBER, ec="none",
            fs=7, weight="bold", r=0.03)
        to_a = (k == 0) == cur_to_a
        arrow(ax, ox + 0.6, y, ox + 1.22, ca if to_a else cb, color=ORANGE,
              lw=1.0, ms=6)
panel(0.05, "During step s", True)
panel(2.4, "After the swap", False)
line(ax, [2.3, 2.3], [0.05, 1.12], color=LIGHT, lw=0.8)
ax.text(1.74, 0.5, "reads A,\nwrites B", fontsize=6.5, color=GRAY,
        va="center", linespacing=1.1)
ax.text(4.09, 0.5, "reads B,\nwrites A", fontsize=6.5, color=GRAY,
        va="center", linespacing=1.1)
save(fig, P("fig-02-03-swap.png"))

print("figures written to", OUT)
