"""values_ch12.py -- Chapter 12 values: real correctness and halo-byte
counts for HeatSim v7, one-process rates, and MODEL predictions.

Usage (from the book root):
    python3 kit/values_ch12.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, math, os, shutil, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scalemodel as sm, distmodel as dm

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch12")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
v = {"provisional": a.provisional, "machine_desc": a.machine}
f1 = lambda x: f"{x:.1f}"
f0 = lambda x: f"{x:,.0f}"

ck = rows("checks.csv")
v["v7_configs"] = str(len(ck))
v["v7_all_identical"] = "yes" if all(r["result"] == "identical" for r in ck) else "no"
halo = {(int(r["processes"]), r["layout"]): r for r in rows("halo.csv")}
for p in (16, 64):
    for l in ("rows", "squares"):
        v[f"hb_{l}_{p}"] = f0(int(halo[(p, l)]["max_bytes"]))
        v[f"hbt_{l}_{p}"] = f0(int(halo[(p, l)]["total_bytes"]))
v["hb_ratio_64"] = f1(int(halo[(64, "rows")]["total_bytes"]) / int(halo[(64, "squares")]["total_bytes"]))

rt = {}
for r in rows("rates.csv"):
    rt.setdefault(int(r["n"]), []).append(float(r["mlups"]))
R = {"l2": st.median(rt[256]) * 1e6, "l3": st.median(rt[1024]) * 1e6, "mem": st.median(rt[4096]) * 1e6}
for k, n in (("l2", 256), ("l3", 1024), ("mem", 4096)):
    v[f"r_v7_{k}"] = f0(R[k] / 1e6)
c10 = json.load(open(os.path.join(ROOT, "data", "ch10", "values.json")))
r_v1 = float(c10["r_v1_4096"].replace(",", "")) * 1e6
v["r_v1"] = c10["r_v1_4096"]

for n in (4096, 16384):
    for p in (64, 256, 1024, 4096):
        for l in ("rows", "squares"):
            v[f"s_{l}_{n}_{p}"] = f0(sm.speedup(n, p, R, r_v1, l))
            t = sm.step_time(n, p, R, l)
            v[f"c_{l}_{n}_{p}"] = f0(sm.comm(n, p, l) / t * 100)
# Karp-Flatt serial fraction from the model, rows, n = 4096 (relative to one process)
def kf(n, p, l):
    s = sm.step_time(n, 1, R, l) / sm.step_time(n, p, R, l)
    return (1 / s - 1 / p) / (1 - 1 / p)
v["kf_rows_4096_64"] = f"{kf(4096, 64, 'rows'):.4f}"
v["kf_rows_4096_1024"] = f"{kf(4096, 1024, 'rows'):.4f}"
for p in (64, 1024, 4096):
    for l in ("rows", "squares"):
        v[f"w_{l}_{p}"] = f0(sm.weak_efficiency(1024, p, R, l) * 100)

# all-to-all lower bound on 64 nodes, 1 MB to every other node, 25 GB/s links
topo = {r["topology"].split()[0]: int(r["bisection"]) for r in
        csv.DictReader(open(os.path.join(ROOT, "data", "ch11", "topology.csv")))}
p_, m_, b_ = 64, 1e6, 25e9
for k in ("ring", "torus", "hypercube", "fully"):
    v[f"a2a_{k}_ms"] = f"{p_ * p_ * m_ / (4 * topo[k] * b_) * 1e3:.2f}"
v["a2a_inject_ms"] = f"{(p_ - 1) * m_ / b_ * 1e3:.2f}"      # each node's own link

# hybrid versus pure MPI on 16 nodes x 64 cores, n = 16384 (counts + alpha-beta)
n, nodes, cores = 16384, 16, 64
pure_side = int(math.sqrt(nodes * cores)); hyb_side = int(math.sqrt(nodes))
blk_pure, blk_hyb = n // pure_side, n // hyb_side
per_node_side = pure_side // hyb_side                   # ranks along a node's edge
v.update(hy_ranks_pure=f0(nodes * cores), hy_ranks_hyb=f0(nodes),
         hy_blk_pure=f0(blk_pure), hy_blk_hyb=f0(blk_hyb),
         hy_msgs_pure=f0(4 * per_node_side), hy_msgs_hyb="4",
         hy_intra_pure=f0(2 * 2 * per_node_side * (per_node_side - 1)),
         hy_kb_pure=f0(8 * blk_pure / 1024), hy_kb_hyb=f0(8 * blk_hyb / 1024),
         hy_node_kb=f0(4 * per_node_side * 8 * blk_pure / 1024))
a_, b2 = dm.ALPHA, dm.BETA_NET
v["hy_t_pure_us"] = f0(4 * per_node_side * (a_ + 8 * blk_pure / b2) * 1e6)
v["hy_t_hyb_us"] = f0(4 * (a_ + 8 * blk_hyb / b2) * 1e6)
v.update(m_alpha_us=f0(dm.ALPHA * 1e6), m_beta_gbs=f0(dm.BETA_NET / 1e9))
# sensitivity: communication share with a worse network
base_a, base_b = dm.ALPHA, dm.BETA_NET
for tag, (fa, fb) in (("base", (1, 1)), ("a2", (2, 1)), ("b2", (1, 0.5))):
    dm.ALPHA, dm.BETA_NET = base_a * fa, base_b * fb
    for n, p in ((4096, 1024), (16384, 4096)):
        t = sm.step_time(n, p, R, "squares")
        v[f"sens_{tag}_{n}_{p}"] = f0(sm.comm(n, p, "squares") / t * 100)
dm.ALPHA, dm.BETA_NET = base_a, base_b
json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in v if k.startswith(("s_", "c_", "w_", "kf", "a2a", "hy_", "hb"))}))
