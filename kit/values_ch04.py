"""values_ch04.py -- turn Chapter 4 benchmark results into book values.

Usage (from the book root):
    python3 kit/values_ch04.py RESULTS_DIR --machine "..." [--provisional]
Writes data/ch04/values.json (see values_ch03.py for the conventions).
"""
import argparse, csv, json, os, re, shutil, statistics as st

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch04")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):     # else: already in place
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))

v = {"provisional": a.provisional, "machine_desc": a.machine}
raw = re.search(r"compiler: (.*)", open(os.path.join(DST, "machine.txt")).read()).group(1)
m = re.search(r"clang version ([\d.]+)", raw)
v["compiler"] = (("Apple Clang " if "Apple" in raw else "Clang ") + m.group(1)) if m \
    else "GCC " + re.search(r"(\d+\.\d+\.\d+)\s*$", raw).group(1)

acc = {}
for r in rows("accum.csv"):
    acc.setdefault(int(r["accumulators"]), []).append(float(r["ns_per_add"]))
med = {k: st.median(x) for k, x in acc.items()}
for k in (1, 2, 4, 8):
    v[f"acc_{k}"] = f"{med[k]:.2f}"
v["acc_speedup_2"] = f"{med[1] / med[2]:.1f}"
v["acc_speedup_4"] = f"{med[1] / med[4]:.1f}"
v["acc_speedup_8"] = f"{med[1] / med[8]:.1f}"
v["acc_8_vs_4_pct"] = f"{abs(med[4] - med[8]) / med[4] * 100:.0f}"

br = {}
for r in rows("branch.csv"):
    br.setdefault((r["variant"], int(r["threshold"])), []).append(float(r["ns_per_element"]))
b = {k: st.median(x) for k, x in br.items()}
rnd, srt = b[("jump", 128)], b[("jump_sorted", 128)]
v.update(br_random=f"{rnd:.2f}", br_sorted=f"{srt:.2f}",
         br_ratio=f"{rnd / srt:.1f}",
         br_always=f"{b[('jump', 0)]:.2f}", br_never=f"{b[('jump', 256)]:.2f}",
         br_75=f"{b[('jump', 64)]:.2f}",
         br_penalty_ns=f"{(rnd - srt) / 0.5:.1f}",
         br_O2_random=f"{b[('O2', 128)]:.2f}", br_O2_sorted=f"{b[('O2_sorted', 128)]:.2f}")
# ---- instruction costs and branch patterns (Chapter 4 expansion)
if os.path.exists(os.path.join(DST, "instr.csv")):
    ic = {}
    for r in rows("instr.csv"):
        ic.setdefault(r["op"], []).append((float(r["latency_ns"]), float(r["throughput_ns"])))
    for op, xs in ic.items():
        v[f"lat_{op}"] = f"{st.median(x[0] for x in xs):.1f}"
        v[f"thr_{op}"] = f"{st.median(x[1] for x in xs):.2f}"
    v["div_vs_mul"] = f"{st.median(x[0] for x in ic['divide']) / st.median(x[0] for x in ic['multiply']):.0f}"
    v["div_vs_mul_thr"] = f"{st.median(x[1] for x in ic['divide']) / st.median(x[1] for x in ic['multiply']):.0f}"
    pt = {}
    for r in rows("pattern.csv"):
        pt.setdefault(int(r["period"]), []).append(float(r["ns_per_element"]))
    pt = {k: st.median(x) for k, x in pt.items()}
    rnd = pt[max(pt)]
    v["pat_2"], v["pat_256"], v["pat_1024"] = (f"{pt[2]:.2f}", f"{pt[256]:.2f}", f"{pt[1024]:.2f}")
    v["pat_4096"], v["pat_rand"] = f"{pt[4096]:.2f}", f"{rnd:.2f}"
    # longest period still under half the random cost
    ok = [k for k in sorted(pt) if pt[k] < 0.5 * rnd]
    v["pat_learned"] = f"{max(ok):,}"
    v["pat_forgot"] = f"{min(k for k in pt if k > max(ok)):,}"

json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps(v, indent=1))
