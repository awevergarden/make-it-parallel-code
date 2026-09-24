"""values_ch05.py -- turn Chapter 5 benchmark results into book values.

Usage (from the book root):
    python3 kit/values_ch05.py RESULTS_DIR --machine "..." [--provisional]
Bandwidths count 32 bytes per triad iteration (two reads, one write, and
the write-allocate read of the destination line), matching HeatSim's
traffic model; the STREAM convention (24 bytes) is also reported.
"""
import argparse, csv, json, os, re, shutil, statistics as st

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch05")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):     # else: already in place
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
text = lambda n: open(os.path.join(DST, n)).read()

v = {"provisional": a.provisional, "machine_desc": a.machine}
raw = re.search(r"compiler: (.*)", text("machine.txt")).group(1)
m = re.search(r"clang version ([\d.]+)", raw)
v["compiler"] = (("Apple Clang " if "Apple" in raw else "Clang ") + m.group(1)) if m \
    else "GCC " + re.search(r"(\d+\.\d+\.\d+)\s*$", raw).group(1)
f1 = lambda x: f"{x:.1f}"
f0 = lambda x: f"{x:,.0f}"

lat = {int(r["bytes"]): float(r["ns_per_load"]) for r in rows("latency.csv")}
pick = lambda lo, hi: st.median([t for b, t in lat.items() if lo <= b <= hi])
KB, MB = 1024, 1024 * 1024
v.update(lat_l1=f1(pick(4 * KB, 32 * KB)), lat_l2=f1(pick(64 * KB, 512 * KB)),
         lat_4m=f0(lat[4 * MB]), lat_16m=f0(lat[16 * MB]),
         lat_mem=f0(pick(256 * MB, 1024 * MB)))
v["lat_ratio"] = f0(pick(256 * MB, 1024 * MB) / pick(4 * KB, 32 * KB))

sd = {(r["kind"], r["param"]): float(r["ns_per_element"]) for r in rows("stride.csv")}
v.update(str_1=f"{sd[('stride', '1')]:.2f}", str_8=f1(sd[("stride", "8")]),
         str_64=f1(sd[("stride", "64")]),
         str_ratio_8=f1(sd[("stride", "8")] / sd[("stride", "1")]),
         row_ns=f"{sd[('order', 'row')]:.2f}", col_ns=f1(sd[("order", "column")]),
         col_ratio=f1(sd[("order", "column")] / sd[("order", "row")]))

bw = {r["level"]: float(r["GBps"]) * 32 / 24 for r in rows("bandwidth.csv")}
for k, name in (("L1", "l1"), ("L2", "l2"), ("L3", "l3"), ("memory", "mem")):
    v[f"bw_{name}"] = f0(bw[k])
v["bw_mem_stream"] = f1(bw["memory"] * 24 / 32)
v["bw_ratio"] = f1(bw["L1"] / bw["memory"])

peak = float(re.search(r"GFLOPs,([\d.]+)", text("peak.txt")).group(1))
v["peak"] = f1(peak)
v["ridge"] = f"{peak / bw['memory']:.2f}"

mm = {}
for r in rows("matmul.csv"):
    mm.setdefault(r["variant"], []).append(float(r["GFLOPs"]))
mm = {k: st.median(x) for k, x in mm.items()}
v.update(mm_ijk=f"{mm['ijk']:.2f}", mm_ikj=f1(mm["ikj"]), mm_tiled=f1(mm["tiled"]),
         mm_ikj_speedup=f1(mm["ikj"] / mm["ijk"]),
         mm_tiled_speedup=f1(mm["tiled"] / mm["ijk"]),
         mm_tiled_vs_ikj_pct=f0(abs(1 - mm["tiled"] / mm["ikj"]) * 100),
         mm_tiled_faster="faster" if mm["tiled"] > mm["ikj"] else "slower")

h = {}
for r in rows("heat.csv"):
    h.setdefault((r["version"], int(r["n"])), []).append(float(r["mlups"]))
h = {k: st.median(x) for k, x in h.items()}
for n in (256, 4096, 6144):
    v[f"v1_{n}"] = f0(h[("v1", n)])
    v[f"v2_{n}"] = f0(h[("v2", n)])
    v[f"v2_gain_{n}"] = f"{h[('v2', n)] / h[('v1', n)]:.2f}"
g1, g2 = h[("v1", 4096)] * 4 / 1000, h[("v2", 4096)] * 4 / 1000
r1, r2 = bw["memory"] * 4 / 24, bw["memory"] * 4 / 16
v.update(v1_gflops=f1(g1), v2_gflops=f1(g2), roof_v1=f1(r1), roof_v2=f1(r2),
         pct_roof_v1=f0(g1 / r1 * 100), pct_roof_v2=f0(g2 / r2 * 100))
# ---- transposes and conflict misses (Chapter 5 expansion)
if os.path.exists(os.path.join(DST, "transpose.csv")):
    tr = {}
    for r in rows("transpose.csv"):
        tr.setdefault((r["variant"], int(r["n"])), []).append(float(r["ns_per_element"]))
    tr = {k: st.median(x) for k, x in tr.items()}
    for n in (1024, 4096):
        v[f"tr_naive_{n}"] = f1(tr[("naive", n)])
        v[f"tr_tiled_{n}"] = f1(tr[("tiled", n)])
        v[f"tr_gain_{n}"] = f1(tr[("naive", n)] / tr[("tiled", n)])
    cf = {}
    for r in rows("conflict.csv"):
        cf.setdefault(int(r["width"]), []).append(float(r["ns_per_element"]))
    cf = {k: st.median(x) for k, x in cf.items()}
    v.update(cf_4096=f"{cf[4096]:.2f}", cf_4104=f"{cf[4104]:.2f}",
             cf_gain=f1(cf[4096] / cf[4104]))

json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps(v))
