"""values_ch03.py -- turn Chapter 3 benchmark results into book values.

Usage (from the book root):
    python3 kit/values_ch03.py RESULTS_DIR --machine "Apple M2 laptop" \
        [--provisional]
Copies the CSV/TXT files to data/ch03/ and writes data/ch03/values.json.
The book's typesetting takes Chapter 3's numbers from that file; with
"provisional": true every such number is highlighted, and the figure
scripts stamp measured figures, so trial numbers can't reach print.
"""
import argparse, csv, json, os, re, shutil, statistics as st

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch03")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):     # else: already in place
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)

def rows(name):
    with open(os.path.join(DST, name)) as f:
        return list(csv.DictReader(f))

def text(name):
    return open(os.path.join(DST, name)).read()

v = {"provisional": a.provisional, "machine_desc": a.machine}
raw = re.search(r"compiler: (.*)", text("machine.txt")).group(1).strip()
m = re.search(r"clang version ([\d.]+)", raw)
if m:
    v["compiler"] = ("Apple Clang " if "Apple" in raw else "Clang ") + m.group(1)
else:
    m = re.search(r"([\d]+\.[\d]+\.[\d]+)\s*$", raw)
    v["compiler"] = "GCC " + m.group(1) if m else raw

opt = {}
for r in rows("opt.csv"):
    opt.setdefault(r["opt"], []).append(float(r["seconds"]))
med = {k: st.median(x) for k, x in opt.items()}
for k in ("O0", "O1", "O2", "O3"):
    v[f"opt_{k}"] = f"{med[k]:.2f}"
v["opt_ratio_O0"] = f"{med['O0'] / med['O2']:.1f}"
v["opt_ratio_O1"] = f"{med['O1'] / med['O2']:.1f}"
v["opt_O3_vs_O2_pct"] = f"{abs(med['O3'] - med['O2']) / med['O2'] * 100:.0f}"

rep = [float(r["seconds"]) for r in rows("repeat.csv")]
m = st.median(rep)
v.update(rep_n=str(len(rep)), rep_median=f"{m:.3f}", rep_min=f"{min(rep):.3f}",
         rep_max=f"{max(rep):.3f}",
         rep_spread_pct=f"{(max(rep) - min(rep)) / m * 100:.0f}",
         rep_max_over_min_pct=f"{(max(rep) / min(rep) - 1) * 100:.0f}")

tm = text("timer.txt")
v["timer_res_ns"] = re.search(r"resolution: (\d+)", tm).group(1)
v["timer_step_ns"] = re.search(r"step: (\d+)", tm).group(1)
v["timer_cost_ns"] = re.search(r"reading: ([\d.]+)", tm).group(1)

d = text("dce.txt")
v["dce_unused"] = re.search(r"discarded: ([\d.]+)", d).group(1)
v["dce_used"] = f"{float(re.search(r'printed: +([\d.]+)', d).group(1)):.2f}"

rate = {}
for r in rows("sweep.csv"):
    n, s, t = int(r["n"]), int(r["steps"]), float(r["seconds"])
    rate.setdefault(n, []).append((n - 2) ** 2 * s / t / 1e6)
best = {n: st.median(x) for n, x in rate.items()}
peak_n = max(best, key=best.get)
big = max(best)
v.update(sweep_peak=f"{best[peak_n]:,.0f}", sweep_peak_n=str(peak_n),
         sweep_big_n=f"{big:,}", sweep_big=f"{best[big]:,.0f}",
         sweep_drop_pct=f"{(1 - best[big] / best[peak_n]) * 100:.0f}",
         sweep_ratio=f"{best[peak_n] / best[big]:.1f}")

check = text("check.txt")
v["v1_check_s"] = f"{float(re.search(r'time: ([\d.]+)', check).group(1)):.2f}"

# ---- profiling (Chapter 3 expansion)
if os.path.exists(os.path.join(DST, "profile.csv")):
    pr = {}
    for r in rows("profile.csv"):
        pr.setdefault((r["variant"], r["step"]), []).append(
            (float(r["seconds"]), float(r["percent"])))
    for (var, step), xs in pr.items():
        key = "ins" if var == "insertion" else "q"
        v[f"prof_{key}_{step}_ms"] = f"{st.median(x[0] for x in xs) * 1000:.0f}"
        v[f"prof_{key}_{step}_pct"] = f"{st.median(x[1] for x in xs):.0f}"
    tot = {k: sum(st.median(x[0] for x in pr[(var, s_)])
                  for s_ in ("generate", "smooth", "sort", "summarize"))
           for k, var in (("ins", "insertion"), ("q", "qsort"))}
    v["prof_ins_total_ms"] = f"{tot['ins'] * 1000:.0f}"
    v["prof_q_total_ms"] = f"{tot['q'] * 1000:.0f}"
    v["prof_q_speedup"] = f"{tot['ins'] / tot['q']:.1f}"
    f_sort = st.median(x[1] for x in pr[("insertion", "sort")]) / 100
    v["prof_amdahl8"] = f"{1 / ((1 - f_sort) + f_sort / 8):.1f}"
    v["prof_amdahl_inf"] = f"{1 / (1 - f_sort):.1f}"
    cg = text("callgrind.txt")
    for step, fn in (("sort", "insertion_sort"), ("smooth", "smooth"), ("generate", "generate")):
        m = re.search(r"\(\s*([\d.]+)%\)\s+\S*" + fn, cg)
        v[f"cg_{step}_pct"] = f"{float(m.group(1)):.0f}" if m else "?"

json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps(v, indent=1))
