"""values_ch06.py -- turn Chapter 6 benchmark results into book values.

Usage (from the book root):
    python3 kit/values_ch06.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, os, re, shutil, statistics as st

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch06")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):     # else: already in place
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)

def med(name, keys, val):
    d = {}
    for r in csv.DictReader(open(os.path.join(DST, name))):
        d.setdefault(tuple(r[k] for k in keys), []).append(float(r[val]))
    return {k: st.median(x) for k, x in d.items()}

v = {"provisional": a.provisional, "machine_desc": a.machine}
raw = re.search(r"compiler: (.*)", open(os.path.join(DST, "machine.txt")).read()).group(1)
m = re.search(r"clang version ([\d.]+)", raw)
v["compiler"] = (("Apple Clang " if "Apple" in raw else "Clang ") + m.group(1)) if m \
    else "GCC " + re.search(r"(\d+\.\d+\.\d+)\s*$", raw).group(1)
f1 = lambda x: f"{x:.1f}"
f0 = lambda x: f"{x:,.0f}"

dx = med("daxpy.csv", ["variant", "level"], "GFLOPs")
for w in ("scalar", "v128", "v256", "v512", "intrin"):
    for lv in ("L1", "L2", "memory"):
        v[f"dx_{w}_{lv.lower()}"] = f1(dx[(w, lv)])
for w in ("v128", "v256", "v512"):
    for lv in ("L1", "memory"):
        v[f"dx_gain_{w}_{lv.lower()}"] = f1(dx[(w, lv)] / dx[("scalar", lv)])

rd = med("reduce.csv", ["build", "function"], "ns_per_add")
v.update(red_plain=f"{rd[('strict', 'plain')]:.2f}", red_simd=f"{rd[('strict', 'simd')]:.2f}",
         red_fast=f"{rd[('fast', 'plain')]:.2f}",
         red_gain=f1(rd[("strict", "plain")] / rd[("strict", "simd")]))
sums = {}
for r in csv.DictReader(open(os.path.join(DST, "reduce.csv"))):
    sums[(r["build"], r["function"])] = r["sum"]
v.update(sum_plain=sums[("strict", "plain")], sum_simd=sums[("strict", "simd")],
         sum_fast=sums[("fast", "plain")])

mm = med("matmul.csv", ["variant"], "GFLOPs")
for w in ("scalar", "v128", "v256", "v512"):
    v[f"mm_{w}"] = f1(mm[(w,)])
v["mm_gain"] = f1(mm[("v512",)] / mm[("scalar",)])

h = med("heat.csv", ["version", "n"], "mlups")
for n in ("256", "1024", "4096", "6144"):
    for ver in ("v1", "v2", "v3_v128", "v3_v512"):
        v[f"h_{ver}_{n}"] = f0(h[(ver, n)])
    v[f"h_gain128_{n}"] = f1(h[("v3_v128", n)] / h[("v2", n)])
    v[f"h_gain512_{n}"] = f1(h[("v3_v512", n)] / h[("v2", n)])
    v[f"h_total_{n}"] = f1(h[("v3_v128", n)] / h[("v1", n)])
# ---- vectorization patterns (Chapter 6 expansion)
if os.path.exists(os.path.join(DST, "vpatterns.csv")):
    vp = med("vpatterns.csv", ["build", "kernel"], "ns_per_element")
    for (b_, k_), x in vp.items():
        v[f"vp_{b_}_{k_}"] = f"{x:.2f}"
    for k_ in ("particles_aos", "particles_soa", "relu", "axpy_double", "axpy_float"):
        v[f"vp_gain_{k_}"] = f1(vp[("scalar", k_)] / vp[("v512", k_)])
    v["vp_soa_vs_aos"] = f1(vp[("v512", "particles_aos")] / vp[("v512", "particles_soa")])
    v["vp_f_vs_d_128"] = f1(vp[("v128", "axpy_double")] / vp[("v128", "axpy_float")])
    v["vp_f_vs_d_512"] = f1(vp[("v512", "axpy_double")] / vp[("v512", "axpy_float")])

json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in list(v)[:6]}), "...", len(v), "values")
