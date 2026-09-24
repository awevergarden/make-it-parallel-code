"""values_ch08.py -- Chapter 8 values: real correctness data and one-core
rates, plus MODEL predictions (heatmodel.py, mmmodel.py).

Usage (from the book root):
    python3 kit/values_ch08.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, math, os, re, shutil, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heatmodel as hm, mmmodel as mm

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch08")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):     # else: already in place
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
v = {"provisional": a.provisional, "machine_desc": a.machine}
f1 = lambda x: f"{x:.1f}"
f0 = lambda x: f"{x:,.0f}"

# ---- reductions (real)
red = {(int(r["threads"]), r["kind"]): r["value"] for r in rows("reduce.csv")}
seq = float(red[(1, "sequential")])
for p in (1, 2, 3, 4, 8, 16):
    v[f"red_{p}"] = red[(p, "reduction")]
v["red_seq"] = red[(1, "sequential")]
v["red_repro"] = red[(1, "reproducible")]
v["red_task"] = red[(1, "task_sum")]
v["repro_same"] = "yes" if len({red[(p, "reproducible")] for p in (1, 2, 3, 4, 8, 16)}) == 1 else "no"
v["task_same"] = "yes" if len({red[(p, "task_sum")] for p in (1, 2, 3, 4, 8, 16)}) == 1 else "no"
rel = max(abs(float(red[(p, "reduction")]) - seq) / seq for p in (2, 3, 4, 8, 16))
e = math.floor(math.log10(rel))
v["red_rel"] = f"{rel / 10 ** e:.1f} × 10^{e}^".replace("-", "−")

# ---- the Bug Hunt (real)
bug = {}
for r in rows("sum_bug.csv"):
    bug.setdefault(int(r["threads"]), []).append(int(r["count"]))
for p in (1, 2, 4, 8):
    v[f"bug_{p}"] = f0(st.median(bug[p]))
v["bug_expected"] = f0((100000000 + 2) // 3)

# ---- schedules (real assignment) and triangular work (model)
owner = {}
for r in rows("schedule.csv"):
    owner.setdefault(r["schedule"], {})[int(r["i"])] = int(r["thread"])
def efficiency(assign, p=4):
    work = [0] * p
    for i, t in assign.items():
        work[t] += i + 1                         # work grows with i
    return sum(work) / p / max(work), work
def simulate_dynamic(nit=400, p=4, chunk=10):
    work = [0] * p
    for c in range(0, nit, chunk):
        t = work.index(min(work))                # idle thread takes next chunk
        work[t] += sum(i + 1 for i in range(c, min(c + chunk, nit)))
    return sum(work) / p / max(work), work
for k in ("static", "static1", "static25"):
    eff, work = efficiency(owner[k])
    v[f"eff_{k}"] = f0(eff * 100)
eff_d, _ = simulate_dynamic()
v["eff_dynamic"] = f0(eff_d * 100)
_, w = efficiency(owner["static"])
v["work_t0"], v["work_t3"] = f0(w[0]), f0(w[3])

# ---- HeatSim one-core rates (real) and model
rate = {}
for r in rows("rates.csv"):
    rate.setdefault((r["version"], int(r["n"])), []).append(float(r["mlups"]))
rate = {k: st.median(x) * 1e6 for k, x in rate.items()}
for n in (256, 1024, 4096):
    for ver in ("v1", "v4", "v5"):
        v[f"r_{ver}_{n}"] = f0(rate[(ver, n)] / 1e6)
v["v5_vs_v4_pct"] = f0(max(abs(rate[("v5", n)] / rate[("v4", n)] - 1) * 100
                          for n in (256, 1024, 4096)))
R5 = {"l2": rate[("v5", 256)], "l3": rate[("v5", 1024)], "mem": rate[("v5", 4096)]}
T_FORK = 5e-6                                    # assumed extra cost per region
for n in (256, 1024, 4096):
    v[f"s5_{n}_16"] = f1(hm.speedup(n, 16, R5, rate[("v1", n)]))
t1 = (254 ** 2) / rate[("v1", 256)]
v["s5_256_16_perstep"] = f1(t1 / (hm.step_time(256, 16, R5) + T_FORK))
v["m_fork_us"] = f0(T_FORK * 1e6)
v["m_barrier_us"] = f0(hm.T_BARRIER * 1e6)

# ---- matrix multiplication: one-core rates (real) and model
g = {}
for r in rows("matmul.csv"):
    g.setdefault((r["variant"], int(r["n"])), []).append(float(r["GFLOPs"]))
g = {k: st.median(x) for k, x in g.items()}
for (ver, n), x in g.items():
    v[f"mm1_{ver}_{n}"] = f1(x)
r_ikj, r_t = g[("ikj", 2048)] * 1e9, g[("tiled", 2048)] * 1e9
cap = mm.BETA * mm.BW_ONE_CORE / mm.BYTES_PER_FLOP["ikj"]
v.update(mm_cap_ikj=f1(cap / 1e9), mm_p_sat=f1(cap / r_ikj),
         mm_ikj_16=f1(mm.rate("ikj", 16, r_ikj) / 1e9),
         mm_tiled_16=f0(mm.rate("tiled", 16, r_t) / 1e9),
         mm_ratio_16=f1(mm.rate("tiled", 16, r_t) / mm.rate("ikj", 16, r_ikj)),
         mm_bpf_tiled=f"{mm.BYTES_PER_FLOP['tiled']:.2f}",
         mm_shared_gbs=f0(mm.BETA * mm.BW_ONE_CORE / 1e9),
         mm_bw1=f1(mm.BW_ONE_CORE / 1e9), m_beta=str(mm.BETA))
# ---- scan and histogram (Chapter 8 expansion)
if os.path.exists(os.path.join(DST, "scan.csv")):
    sc = rows("scan.csv")
    v["scan_errors"] = str(sum(int(r["errors"]) for r in sc))
    v["scan_threads"] = ", ".join(r["threads"] for r in sc)
    hg = {}
    for r in rows("histogram.csv"):
        hg.setdefault((int(r["threads"]), r["method"]), []).append(r)
    for mth in ("critical", "atomic", "private", "reduction"):
        v[f"h_{mth}"] = f"{st.median(float(r['ns_per_update']) for r in hg[(1, mth)]):.2f}"
    v["h_all_ok"] = "yes" if all(r["ok"] == "yes" for rs in hg.values() for r in rs) else "no"
    v["h_crit_vs_priv"] = f"{float(v['h_critical']) / float(v['h_private']):.0f}"

json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in v if not k.startswith("red_") or k in ("red_rel",)}))
