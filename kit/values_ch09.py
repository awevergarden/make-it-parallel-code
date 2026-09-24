"""values_ch09.py -- Chapter 9 values: real local-IPC measurements and the
alpha-beta (latency-bandwidth) model fitted to them.

Usage (from the book root):
    python3 kit/values_ch09.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, os, re, shutil, statistics as st
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch09")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):     # else: already in place
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
v = {"provisional": a.provisional, "machine_desc": a.machine}
text = lambda n: open(os.path.join(DST, n)).read()
v["pipe_cap"] = f"{int(re.search(r'(\d+) bytes', text('pipe_capacity.txt')).group(1)):,}"
v["pipe_cap_plus1"] = f"{int(v['pipe_cap'].replace(',', '')) + 1:,}"
dl = {(r["mode"], int(r["bytes"])): r["result"]
      for r in csv.DictReader(open(os.path.join(DST, "deadlock.csv")))}
cap = int(v["pipe_cap"].replace(",", ""))
v["dl_at_cap"], v["dl_above_cap"] = dl[("both-write", cap)], dl[("both-write", cap + 1)]
v["dl_ordered"] = dl[("ordered", 1000000)]
v["shm_line"] = text("shm_demo.txt").strip()

def fit(kind):
    d = {}
    for r in csv.DictReader(open(os.path.join(DST, "pingpong.csv"))):
        if r["kind"] == kind:
            d.setdefault(int(r["bytes"]), []).append(float(r["microseconds"]))
    n = np.array(sorted(d))
    t = np.array([st.median(d[k]) for k in n])
    # least squares on relative error: minimize sum(((alpha + n/beta) - t) / t)^2
    A = np.vstack([1 / t, n / t]).T
    alpha, inv_beta = np.linalg.lstsq(A, np.ones_like(t), rcond=None)[0]
    return n, t, alpha, 1 / inv_beta           # microseconds, bytes/us
for k in ("pipe", "unix", "tcp"):
    n, t, al, be = fit(k)
    v[f"a_{k}"] = f"{al:.1f}"                 # microseconds
    v[f"b_{k}"] = f"{be / 1000:.1f}"          # bytes/us / 1000 = GB/s
    v[f"nhalf_{k}"] = f"{al * be / 1024:,.0f}"  # KB
    v[f"t8_{k}"] = f"{t[0]:.1f}"
    v[f"t2m_{k}"] = f"{t[-1]:,.0f}"
    v[f"fiterr_{k}"] = f"{max(abs(al + n / be - t) / t) * 100:.0f}"
    small = n <= 524288
    v[f"fiterr_small_{k}"] = f"{max(abs(al + n[small] / be - t[small]) / t[small]) * 100:.0f}"
# HeatSim halo example from the model (pipe numbers)
al, be = float(v["a_pipe"]), float(v["b_pipe"]) * 1000
for n_ in (1024, 8192):
    v[f"halo_{n_}"] = f"{al + 8 * n_ / be:.1f}"
# ---- one server, many clients (Chapter 9 expansion)
if os.path.exists(os.path.join(DST, "server.csv")):
    sv = list(csv.DictReader(open(os.path.join(DST, "server.csv"))))
    v["srv_all_correct"] = "yes" if all(r["result"] == "correct" for r in sv) else "no"
    v["srv_us"] = f"{st.median(float(r['us_per_request']) for r in sv):.1f}"

json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps(v))
