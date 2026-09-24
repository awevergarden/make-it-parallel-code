"""values_ch07.py -- Chapter 7 values: real single-core measurements,
correctness results, and MODEL predictions (see heatmodel.py).

Usage (from the book root):
    python3 kit/values_ch07.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, os, re, shutil, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heatmodel as hm

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch07")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):     # else: already in place
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
v = {"provisional": a.provisional, "machine_desc": a.machine}
f1 = lambda x: f"{x:.1f}"
f0 = lambda x: f"{x:,.0f}"

race = rows("race.csv")
plain = [int(r["got"]) for r in race if r["mode"] == "plain"]
exp = int(race[0]["expected"])
v.update(race_expected=f0(exp), race_min=f0(min(plain)), race_max=f0(max(plain)),
         race_lost_min=f0((1 - max(plain) / exp) * 100),
         race_lost_max=f0((1 - min(plain) / exp) * 100),
         race_runs=str(len(plain)))
ns = {m: st.median(float(r["ns"]) for r in race if r["mode"] == m)
      for m in ("plain", "atomic", "mutex")}
v.update(race_ns_plain=f"{ns['plain']:.1f}", race_ns_atomic=f"{ns['atomic']:.1f}",
         race_ns_mutex=f"{ns['mutex']:.1f}")
c = dict(l.strip().split(",") for l in open(os.path.join(DST, "costs.csv")))
v.update(cost_create_us=f1(float(c["create_join_us"])), cost_mutex_ns=f0(float(c["mutex_ns"])),
         cost_atomic_ns=f1(float(c["atomic_ns"])), cost_plain_ns=f"{float(c['plain_ns']):.2f}")
fs = dict(l.strip().split(",") for l in open(os.path.join(DST, "false_sharing.csv")))
v.update(fs_packed=f"{float(fs['packed']):.2f}", fs_padded=f"{float(fs['padded']):.2f}")

rate = {}
for r in rows("rates.csv"):
    rate.setdefault((r["version"], int(r["n"])), []).append(float(r["mlups"]))
rate = {k: st.median(x) * 1e6 for k, x in rate.items()}
R = {"l2": rate[("v4", 256)], "l3": rate[("v4", 1024)], "mem": rate[("v4", 4096)]}
for n in (256, 1024, 4096):
    v[f"r_v1_{n}"] = f0(rate[("v1", n)] / 1e6)
    v[f"r_v4_{n}"] = f0(rate[("v4", n)] / 1e6)
    for p in (1, 2, 4, 8, 16):
        v[f"s_{n}_{p}"] = f1(hm.speedup(n, p, R, rate[("v1", n)]))
    v[f"step_us_{n}_1"] = f1(hm.step_time(n, 1, R) * 1e6)
    v[f"step_us_{n}_16"] = f1(hm.step_time(n, 16, R) * 1e6)
v["v4_1_over_v1_4096"] = f"{rate[('v4', 4096)] / rate[('v1', 4096)]:.2f}"
v.update(m_barrier_us=f0(hm.T_BARRIER * 1e6), m_beta=str(hm.BETA),
         m_l2_mb=f0(hm.L2_PER_CORE / 2 ** 20), m_l3_mb=f0(hm.L3_USABLE / 2 ** 20))
# superlinear check at n = 1024: v4 on p cores versus v4 on one core
v["s1024_16_vs_v4"] = f1(hm.step_time(1024, 1, R) / hm.step_time(1024, 16, R))
v["s1024_8_vs_v4"] = f1(hm.step_time(1024, 1, R) / hm.step_time(1024, 8, R))
v["m_l2_usable_mb"] = f1(hm.L2_USABLE / 2 ** 20)
# ---- lock ordering and the bounded queue (Chapter 7 expansion)
if os.path.exists(os.path.join(DST, "queue.csv")):
    lo = dict(l.strip().split(",") for l in open(os.path.join(DST, "lock_order.csv")))
    v["lo_opposite"], v["lo_ordered"] = lo["opposite"], lo["ordered"]
    qd = {}
    for r in rows("queue.csv"):
        qd.setdefault(int(r["consumers"]), []).append(r)
    v["q_all_correct"] = "yes" if all(int(r["taken"]) == 1000000 and
                                      int(r["sum"]) == 500000500000
                                      for rs in qd.values() for r in rs) else "no"
    for c_ in (1, 3, 8):
        v[f"q_us_{c_}"] = f"{st.median(float(r['us_per_item']) for r in qd[c_]):.2f}"
    ck = open(os.path.join(DST, "checks.txt")).read()
    m_ = re.search(r"tsan_queue_warnings,(\d+)", ck)
    v["q_tsan"] = m_.group(1) if m_ else "?"

json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in v if k.startswith(("race", "cost", "fs", "r_", "s_", "step", "s1024", "v4_"))}))
