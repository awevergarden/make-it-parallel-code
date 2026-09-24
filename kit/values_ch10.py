"""values_ch10.py -- Chapter 10 values: real MPI behavior on one machine,
one-process rates, and MODEL predictions (distmodel.py, heatmodel.py).

Usage (from the book root):
    python3 kit/values_ch10.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, os, re, shutil, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import distmodel as dm, heatmodel as hm

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch10")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):     # else: already in place
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
v = {"provisional": a.provisional, "machine_desc": a.machine}
f1 = lambda x: f"{x:.1f}"
f0 = lambda x: f"{x:,.0f}"
m = open(os.path.join(DST, "machine.txt")).read()
v["mpi_version"] = re.search(r"mpi: .*?\(Open MPI\) ([\d.]+)", m).group(1)

eg = dict(l.strip().split(",") for l in open(os.path.join(DST, "eager.txt")))
v.update(eager_ok=f0(int(eg["largest_ok"])), eager_hang=f0(int(eg["smallest_hang"])),
         ssend_8=eg["ssend_8"], sendrecv_1m=eg["sendrecv_1M"],
         eager_header=str(4096 - int(eg["largest_ok"])),
         barrier_bug=eg.get("barrier_bug", "?"))
d_ = 1e8; p_ = 64                               # ring vs tree allreduce example (model)
v["ring_ms"] = f"{2 * (p_ - 1) * (dm.ALPHA + d_ / (p_ * dm.BETA_NET)) * 1e3:.1f}"
v["tree_ms"] = f"{2 * 6 * (dm.ALPHA + d_ / dm.BETA_NET) * 1e3:.0f}"

red = {int(r["processes"]): r["sum"] for r in rows("reduce.csv")}
for p in (1, 2, 3, 4, 8):
    v[f"red_{p}"] = red[p]

d = {}
for r in rows("pingpong.csv"):
    d.setdefault(int(r["bytes"]), []).append(float(r["microseconds"]))
n = np.array(sorted(d)); t = np.array([st.median(d[k]) for k in n])
A = np.vstack([1 / t, n / t]).T
al, ib = np.linalg.lstsq(A, np.ones_like(t), rcond=None)[0]
be = 1 / ib
v.update(a_mpi=f1(al), b_mpi=f1(be / 1000), t8_mpi=f1(t[0]), t2m_mpi=f0(t[-1]),
         fiterr_mpi=f0(max(abs(al + n / be - t) / t) * 100))

rate = {}
for r in rows("rates.csv"):
    rate.setdefault((r["version"], int(r["n"])), []).append(float(r["mlups"]))
rate = {k: st.median(x) * 1e6 for k, x in rate.items()}
for nn in (256, 1024, 4096):
    v[f"r_v1_{nn}"] = f0(rate[("v1", nn)] / 1e6)
    v[f"r_v6_{nn}"] = f0(rate[("v6", nn)] / 1e6)
R = {"l2": rate[("v6", 256)], "l3": rate[("v6", 1024)], "mem": rate[("v6", 4096)]}
r1 = rate[("v1", 4096)]            # v1 baseline: memory-bound rate, used for both sizes
for nn in (4096, 16384):
    for p in (1, 4, 16, 64, 256):
        v[f"s6_{nn}_{p}"] = f1(dm.speedup(nn, p, R, r1))
        cm, tot = dm.comm_time(nn, p), dm.step_time(nn, p, R)
        v[f"comm_{nn}_{p}"] = f0(cm / tot * 100) if p > 1 else "0"
v["comm_us_4096"] = f1(dm.comm_time(4096, 2) * 1e6)
v["comp_us_4096_256"] = f1((4094 ** 2 / 256) / dm.rate(4096, 256, R) * 1e6)
v["shared_4096_16"] = f1(hm.speedup(4096, 16, R, r1))
v.update(m_alpha_us=f0(dm.ALPHA * 1e6), m_beta_gbs=f0(dm.BETA_NET / 1e9))
json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in v if not k.startswith("red_")}))
