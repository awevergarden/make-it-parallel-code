"""values_ch11.py -- Chapter 11 values: computed topology properties, the
measured internet connection, and cross-references to Chapters 9-10.

Usage (from the book root):
    python3 kit/values_ch11.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, os, shutil, statistics as st

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch11")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
v = {"provisional": a.provisional, "machine_desc": a.machine}
for r in rows("topology.csv"):
    k = r["topology"].split()[0]
    for f in ("degree", "links", "diameter", "avg_distance", "bisection"):
        v[f"t_{k}_{f}"] = (f"{int(r[f]):,}" if f == "links" else
                           r[f].replace("-", "\u2013") if f == "degree" else r[f])
w = rows("wan.csv")
rtt = [float(r["value"]) for r in w if r["kind"] == "rtt_ms"]
bw = [float(r["value"]) for r in w if r["kind"] == "download_MBps"]
v["wan_rtt_ms"] = f"{st.median(rtt):.0f}"
v["wan_rtt_lo"], v["wan_rtt_hi"] = f"{min(rtt):.0f}", f"{max(rtt):.0f}"
v["wan_alpha_ms"] = f"{st.median(rtt) / 2:.0f}"
v["wan_mbps"] = f"{st.median(bw):.0f}"
# cross-chapter measured values (final data of Chapters 9 and 10)
c9 = json.load(open(os.path.join(ROOT, "data", "ch09", "values.json")))
c10 = json.load(open(os.path.join(ROOT, "data", "ch10", "values.json")))
v.update(a_pipe=c9["a_pipe"], b_pipe=c9["b_pipe"], a_tcp=c9["a_tcp"], b_tcp=c9["b_tcp"],
         a_mpi=c10["a_mpi"], b_mpi=c10["b_mpi"])
# how much computation fits in one message latency (HeatSim, one core, ~2e9 updates/s)
R = 2e9
v["cells_wan"] = f"{st.median(rtt) / 2 / 1000 * R / 1e6:,.0f}"      # millions
v["cells_cluster"] = f"{2e-6 * R:,.0f}"
v["wan_vs_cluster"] = f"{st.median(rtt) / 2 / 1000 / 2e-6:,.0f}"
if os.path.exists(os.path.join(DST, "files.csv")):
    fl = rows("files.csv")
    many = [float(r["us_per_record"]) for r in fl if r["layout"] == "many"]
    one = [float(r["us_per_record"]) for r in fl if r["layout"] == "one"]
    v.update(sf_many=f"{st.median(many):.0f}", sf_many_lo=f"{min(many):.0f}",
             sf_many_hi=f"{max(many):.0f}", sf_one=f"{st.median(one):.2f}",
             sf_ratio=f"{st.median(many) / st.median(one):.0f}")
json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in v if k.startswith(("wan", "cells", "t_ring", "t_hyper"))}))
