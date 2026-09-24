"""values_ch13.py -- Chapter 13 values: exact-checked distributed products
with counted traffic, one-core Strassen timings, layout balance, the
heterogeneous partition, and MODEL predictions (mmdistmodel.py).

Usage (from the book root):
    python3 kit/values_ch13.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, os, shutil, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mmdistmodel as mdm, distmodel as dm

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch13")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
v = {"provisional": a.provisional, "machine_desc": a.machine}
f0 = lambda x: f"{x:,.0f}"

tr = rows("traffic.csv")
v["mm_runs"] = str(len(tr))
v["mm_all_exact"] = "yes" if all(r["wrong"] == "0" for r in tr) else "no"
for r in tr:
    k = f"{r['algorithm']}_{r['processes']}"
    v[f"rx_{k}"] = f0(int(r["max_received"]))
    v[f"rt_{k}"] = f0(int(r["total_received"]))
n2 = 720 * 720
if os.path.exists(os.path.join(DST, "bug.csv")):
    for r in rows("bug.csv"):
        v[f"bug_wrong_{r['processes']}"] = f0(int(r["wrong"]))
    v["bug_total_9"] = f0(n2)
v["n2"] = f0(n2)

s = {}
for r in rows("strassen.csv"):
    s.setdefault(int(r["n"]), []).append(r)
for n in (512, 1024, 2048):
    ik = st.median(float(r["ikj_s"]) for r in s[n])
    sv = st.median(float(r["strassen_s"]) for r in s[n])
    v[f"st_ikj_{n}"] = f"{ik:.2f}"
    v[f"st_str_{n}"] = f"{sv:.2f}"
    v[f"st_gain_{n}"] = f"{ik / sv:.2f}"
    v[f"st_diff_{n}"] = s[n][0]["max_diff"]
    v[f"st_max_{n}"] = s[n][0]["max_entry"]

bal = {}
for r in rows("balance.csv"):
    bal.setdefault(r["layout"], []).append(int(r["updates"]))
for k, w in bal.items():
    key = "block" if k == "block" else "cyclic"
    v[f"bal_{key}_min"], v[f"bal_{key}_max"] = f0(min(w)), f0(max(w))
    v[f"bal_{key}_eff"] = f0(sum(w) / len(w) / max(w) * 100)
v["bal_block_ratio"] = f"{max(bal['block']) / min(bal['block']):.1f}"

h = {r["quantity"]: r["value"] for r in rows("hetero.csv")}
v.update(het_strips=h["strips_half_perimeter"], het_cols=h["columns_half_perimeter"],
         het_group=h["columns_grouping"], het_bound=h["lower_bound"],
         het_equal=h["equal_split_time"], het_prop=h["proportional_time"])

c8 = json.load(open(os.path.join(ROOT, "data", "ch08", "values.json")))
F = float(c8["mm1_ikj_2048"]) * 1e9
v["F_gflops"] = c8["mm1_ikj_2048"]
n = 8192
for p in (64, 1024, 4096, 16384):
    for alg in ("1d", "cannon", "2.5d"):
        v[f"sh_{alg.replace('.', '')}_{p}"] = f0(mdm.share(n, p, alg, F) * 100)
v["comp_ms_4096"] = f"{mdm.compute(n, 4096, F) * 1e3:.0f}"
v.update(m_alpha_us=f0(dm.ALPHA * 1e6), m_beta_gbs=f0(dm.BETA_NET / 1e9))
if os.path.exists(os.path.join(DST, "blas.csv")):
    bl = {int(r["n"]): float(r["GFLOPs"]) for r in rows("blas.csv")}
    for k_, x_ in bl.items():
        v[f"blas_{k_}"] = f"{x_:.0f}"
    Fb = bl[2048] * 1e9
    v["blas_vs_ikj"] = f"{Fb / F:.0f}"
    v["st_eff_gflops"] = f"{2 * 2048 ** 3 / float(v['st_str_2048']) / 1e9:.1f}"
    v["ikj_gflops_2048"] = f"{2 * 2048 ** 3 / float(v['st_ikj_2048']) / 1e9:.1f}"
    for p in (1024, 4096, 16384):
        for alg in ("1d", "cannon", "2.5d"):
            v[f"shb_{alg.replace('.', '')}_{p}"] = f0(mdm.share(n, p, alg, Fb) * 100)
    sh = mdm.share(n, 4096, "cannon", Fb)
    v["overlap_gain_4096"] = f"{1 / max(sh, 1 - sh):.1f}"
json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in v if k.startswith(("rx_", "st_gain", "bal", "het", "sh_", "comp", "F_"))}))
