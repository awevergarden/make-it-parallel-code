"""fit_growth.py -- doubling times of transistor counts and of the
fastest supercomputer, by least squares on log2 of the values.
Make It Parallel, Chapter 20.

Data: growth_data.csv (published transistor counts; the No. 1 system of
the TOP500 list by Linpack Rmax, with the year of the list).
Also fits the TOP500 series the wrong way -- least squares on the raw
values instead of their logarithms -- to show how the largest values
dominate such a fit.
Run:  python3 fit_growth.py      (prints CSV)
"""
import csv, math

rows = list(csv.DictReader(open("growth_data.csv")))

def fit(points):
    """Least-squares line through (year, log2 value): returns doubling
    time in years, and the largest deviation of a point from the line
    as a factor."""
    n = len(points)
    xs = [p[0] for p in points]
    ys = [math.log2(p[1]) for p in points]
    mx, my = sum(xs) / n, sum(ys) / n
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    icpt = my - slope * mx
    worst = max(abs(y - (icpt + slope * x)) for x, y in zip(xs, ys))
    return 1 / slope, 2 ** worst, slope, icpt

def pts(kind, lo=0, hi=9999):
    return [(float(r["year"]), float(r["value"])) for r in rows
            if r["kind"] == kind and lo <= float(r["year"]) <= hi]

print("series,first_year,last_year,points,doubling_years,worst_factor,slope,intercept")
for name, kind, lo, hi in (("transistors all", "transistors", 0, 9999),
                           ("transistors to 2006", "transistors", 0, 2006),
                           ("transistors 2006 on", "transistors", 2006, 9999),
                           ("top500 all", "top500", 0, 9999),
                           ("top500 1993-2013", "top500", 0, 2013.6),
                           ("top500 2013-2026", "top500", 2013.4, 9999)):
    p = pts(kind, lo, hi)
    d, w, s, b = fit(p)
    print(f"{name},{int(min(x for x, _ in p))},{int(max(x for x, _ in p))},{len(p)},{d:.2f},{w:.1f},{s:.5f},{b:.4f}")

# The pitfall: an exponential fitted to the raw values (grid search over the
# doubling time; the best scale for each is found by least squares).
p = pts("top500")
x0 = min(x for x, _ in p)                  # measure time from the first list
best = None
for i in range(50, 400):
    d = i / 100
    g = [2 ** ((x - x0) / d) for x, _ in p]
    a = sum(gi * y for gi, (_, y) in zip(g, p)) / sum(gi * gi for gi in g)
    err = sum((a * gi - y) ** 2 for gi, (_, y) in zip(g, p))
    if best is None or err < best[0]:
        best = (err, d, a)
_, d, a = best
first = min(p)
miss = max(a * 2 ** ((first[0] - x0) / d) / first[1], first[1] / (a * 2 ** ((first[0] - x0) / d)))
print(f"top500 raw-scale fit,{int(first[0])},{int(max(x for x, _ in p))},{len(p)},{d:.2f},{miss:.0f},,")
