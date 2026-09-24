"""figs_ch20.py -- figures for Chapter 20, Exponential Growth and Performance Planning.

Usage: python3 kit/figs_ch20.py OUTDIR
Figures 20.1-20.2 plot published data with our least-squares fits;
Figure 20.3 plots our queue simulation with the Erlang C formula;
Figure 20.4 plots the capacity plan (Erlang C).
"""
import sys, os, csv, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookstyle import *
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch20")
os.makedirs(OUT, exist_ok=True)
P = lambda name: os.path.join(OUT, name)
rows = lambda n: list(csv.DictReader(open(os.path.join(DATA, n))))

def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

banner(P("fig-20-00-banner.png"), seed=140, mode="rise")
data = rows("growth_data.csv")
fits = {r["series"]: r for r in rows("fits.csv")}
def line_of(name, x0, x1):
    f = fits[name]
    xs = np.array([x0, x1])
    return xs, 2 ** (float(f["slope"]) * xs + float(f["intercept"]))

# ------------------------------------------------ 20.1 transistors
tr = [r for r in data if r["kind"] == "transistors"]
fig, ax = plt.subplots(figsize=(FIG_W, 2.4), layout="constrained")
ax.scatter([float(r["year"]) for r in tr], [float(r["value"]) for r in tr], color=BLUE, s=16, zorder=3)
xs, ys = line_of("transistors all", 1970, 2025)
ax.plot(xs, ys, color=ORANGE, lw=1.1, ls="--", label=f"fit: doubling every {float(fits['transistors all']['doubling_years']):.2f} years")
for r in tr:
    if r["name"] in ("Intel 4004", "Intel 80386", "Intel Pentium 4", "Intel Core 2 Duo", "NVIDIA H100", "NVIDIA B200 (two dies)"):
        lab = r["name"].replace(" (two dies)", "")
        ax.annotate(lab, (float(r["year"]), float(r["value"])), textcoords="offset points",
                    xytext=(4, -9), fontsize=5.8, color=GRAY)
ax.set_yscale("log")
ax.set_xlabel("Year")
ax.set_ylabel("Transistors per chip\n(log scale)")
ax.grid(True, which="major")
ax.legend(loc="upper left", frameon=False, fontsize=6.8)
clean(ax)
save(fig, P("fig-20-01-transistors.png"))

# ------------------------------------------------ 20.2 TOP500 No. 1
t5 = [r for r in data if r["kind"] == "top500"]
fig, ax = plt.subplots(figsize=(FIG_W, 2.4), layout="constrained")
ax.scatter([float(r["year"]) for r in t5], [float(r["value"]) for r in t5], color=INK, s=16, zorder=3)
for name, c, x0, x1 in (("top500 1993-2013", TEALD, 1993, 2014), ("top500 2013-2026", ORANGE, 2013, 2027)):
    xs, ys = line_of(name, x0, x1)
    d = float(fits[name]["doubling_years"])
    ax.plot(xs, ys, color=c, lw=1.2, ls="--", label=f"{name[7:]}: doubling every {d:.2f} years")
for r in t5:
    if r["name"] in ("CM-5", "ASCI Red", "Roadrunner", "Frontier", "LineShine"):
        ax.annotate(r["name"], (float(r["year"]), float(r["value"])), textcoords="offset points",
                    xytext=(4, -9), fontsize=5.8, color=GRAY)
ax.set_yscale("log")
ax.set_yticks([1e9, 1e12, 1e15, 1e18], ["1 GFLOP/s", "1 TFLOP/s", "1 PFLOP/s", "1 EFLOP/s"])
ax.set_xlabel("Year of the TOP500 list")
ax.set_ylabel("Linpack Rmax of the\nNo. 1 system (log scale)")
ax.grid(True, which="major")
ax.legend(loc="upper left", frameon=False, fontsize=6.8)
clean(ax)
save(fig, P("fig-20-02-top500.png"))

# ------------------------------------------------ 20.3 queue (simulated + theory)
def erlang_c_wait(c, rho, mean=10.0):
    lam, mu = rho * c / mean, 1 / mean
    A = lam / mu
    s = sum(A ** k / math.factorial(k) for k in range(c))
    top = A ** c / math.factorial(c) * c / (c - A)
    return top / (s + top) / (c * mu - lam)
q = rows("queue.csv")
fig, ax = plt.subplots(figsize=(FIG_W, 2.2), layout="constrained")
rr = np.linspace(0.2, 0.96, 80)
ax.plot(rr * 100, [erlang_c_wait(8, r) for r in rr], color=GRAY, lw=1.1, label="Erlang C formula (random job lengths)")
e = [(float(r["utilization"]), float(r["mean_wait_min"])) for r in q if r["jobs"] == "exp"]
ax.scatter([x * 100 for x, _ in e], [w for _, w in e], color=BLUE, s=20, zorder=3, label="simulated, random job lengths")
for kind, mk, c, lab in (("fixed", "s", TEALD, "simulated, all jobs 10 minutes"),
                         ("mixed", "^", ORANGE, "simulated, mixed short and long jobs")):
    w = float(next(r["mean_wait_min"] for r in q if r["jobs"] == kind))
    ax.scatter([80], [w], color=c, marker=mk, s=26, zorder=4, label=lab)
ax.set_xlabel("Utilization of 8 workers (%)")
ax.set_ylabel("Mean wait before\na job starts (minutes)")
ax.set_ylim(0, 22)
ax.grid(True, axis="y")
ax.legend(loc="upper left", frameon=False, fontsize=6.5)
clean(ax)
save(fig, P("fig-20-03-queue.png"))

# ------------------------------------------------ 20.4 capacity plan (Erlang C)
base = 0.5 * 8 / 10.0
months = np.arange(0, 37)
fig, ax = plt.subplots(figsize=(FIG_W, 2.0), layout="constrained")
for c, col, ls in ((8, ORANGE, "-"), (12, BLUE, "--"), (16, TEALD, "-."), (25, INK, ":")):
    w = []
    for m in months:
        rho = base * 1.05 ** m * 10 / c
        w.append(erlang_c_wait(c, rho) if rho < 0.995 else np.nan)
    ax.plot(months, w, color=col, lw=1.3, ls=ls, label=f"{c} workers")
ax.axhline(5, color=GRAY, lw=0.8, ls=":")
ax.text(35.5, 5.4, "target: 5 minutes", fontsize=6.3, color=GRAY, ha="right")
ax.set_ylim(0, 15)
ax.set_xlabel("Months from now (arrivals grow 5% per month)")
ax.set_ylabel("Mean wait\n(minutes)")
ax.grid(True, axis="y")
ax.legend(loc="upper left", frameon=False, fontsize=6.6, ncol=2)
clean(ax)
save(fig, P("fig-20-04-plan.png"))
print("figures written to", OUT)
