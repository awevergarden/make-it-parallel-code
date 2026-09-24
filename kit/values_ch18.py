"""values_ch18.py -- Chapter 18 values: election message counts
(simulated), two-phase commit (real MPI runs), and the Raft simulation.

Usage (from the book root):
    python3 kit/values_ch18.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, os, re, shutil, statistics as st

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch18")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
v = {"provisional": a.provisional, "machine_desc": a.machine}
f0 = lambda x: f"{x:,.0f}"

for r in csv.DictReader(open(os.path.join(DST, "elect.csv"))):
    n = r["n"]
    for k in ("ring_best", "ring_worst", "ring_random", "bully_lowest_detects", "bully_second_detects"):
        v[f"el_{k}_{n}"] = f0(float(r[k]))

tp = open(os.path.join(DST, "twopc.txt")).read()
v["tp_msgs_commit"] = re.search(r"coordinator,commit,messages,(\d+)", tp).group(1)
v["tp_msgs_crash"] = re.search(r"coordinator,crash,messages,(\d+)", tp).group(1)
crash_waits = [float(x) for x in re.findall(r"participant,\d+,commit,was_blocked,([\d.]+)", tp)]
v["tp_blocked_n"] = str(len(crash_waits))
v["tp_blocked_s"] = f"{max(crash_waits):.2f}" if crash_waits else "0"
v["tp_abort_all"] = "yes" if len(re.findall(r"participant,\d+,abort,", tp)) == 3 else "no"

for m in ("raft", "fixed", "nocheck"):
    txt = open(os.path.join(DST, f"raft_{m}.txt")).read()
    d = dict(l.split(",", 1) for l in txt.strip().splitlines())
    for k in ("runs", "election_safety_violations", "apply_violations", "runs_with_apply_violation",
              "leaders_elected", "leader_crashes", "jobs_submitted", "jobs_committed"):
        v[f"rf_{m}_{k}"] = f0(float(d[k]))
    v[f"rf_{m}_recovery"] = f0(float(d["mean_recovery_ms"]))
    v[f"rf_{m}_commit_pct"] = f"{float(d['jobs_committed']) / float(d['jobs_submitted']) * 100:.1f}"
    x = sorted(float(l) for l in open(os.path.join(DST, f"recovery_{m}.txt")))
    v[f"rc_{m}_median"] = f0(st.median(x))
    v[f"rc_{m}_p90"] = f0(x[int(0.9 * len(x))])
    v[f"rc_{m}_max"] = f0(x[-1])
v["rf_sim_seconds"] = f0(int(v["rf_raft_runs"]) * 10)
json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in v if k.startswith(("rf_", "rc_", "tp_"))}))
