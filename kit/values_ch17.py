"""values_ch17.py -- Chapter 17 values: mutual exclusion, deadlock
detection, failure detection, and leases (all real runs).

Usage (from the book root):
    python3 kit/values_ch17.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, os, re, shutil

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch17")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
v = {"provisional": a.provisional, "machine_desc": a.machine}
f0 = lambda x: f"{x:,.0f}"

mx = rows("mutex.csv")
for r in mx:
    k = f"{r['mode']}_{r['processes']}"
    v[f"mx_ent_{k}"] = f0(int(r["entries"]))
    v[f"mx_viol_{k}"] = f0(int(r["violations"]))
    v[f"mx_mpe_{k}"] = r["msgs_per_entry"]
v["mx_safe"] = "yes" if all(r["violations"] == "0" for r in mx if r["mode"] != "none") else "no"
v["mx_none_total"] = f0(sum(int(r["violations"]) for r in mx if r["mode"] == "none"))
v["mx_none_entries"] = f0(sum(int(r["entries"]) for r in mx if r["mode"] == "none"))

cm = open(os.path.join(DST, "cmh.txt")).read().splitlines()
cyc = [l for l in cm if l.startswith("cycle")]
v["cmh_runs"] = str(len(cyc))
v["cmh_found"] = re.search(r"deadlocked:([\d ]*)", cyc[0]).group(1).strip()
v["cmh_consistent"] = "yes" if len(set(cyc)) == 1 else "no"
v["cmh_probes"] = re.search(r"probes,(\d+)", cyc[0]).group(1)
nc = [l for l in cm if l.startswith("nocycle")][0]
v["cmh_nocycle_found"] = re.search(r"deadlocked:([\d ]*)", nc).group(1).strip() or "none"
v["cmh_nocycle_probes"] = re.search(r"probes,(\d+)", nc).group(1)

hb = open(os.path.join(DST, "heartbeat.txt")).read()
v["hb_beats"] = re.search(r"heartbeats,(\d+)", hb).group(1)
v["hb_longest"] = re.search(r"longest_gap_ms,([\d.]+)", hb).group(1)
for m in re.finditer(r"^(\d+),(\d+),([\d.]+)$", hb, flags=re.M):
    v[f"hb_false_{m.group(1)}"] = m.group(2)
    v[f"hb_det_{m.group(1)}"] = m.group(3)

ls = rows("lease.csv")
for r in ls:
    k = "fence" if r["fencing"] == "yes" else "nofence"
    v[f"ls_{k}_expired"] = r["a_lease_expired_before_write"]
    v[f"ls_{k}_accepted"] = r["stale_writes_accepted"]
    v[f"ls_{k}_rejected"] = r["stale_writes_rejected"]
v["ls_trials"] = ls[0]["trials"]
bk = open(os.path.join(DST, "banker.txt")).read()
v["bk_order"] = ", ".join(re.search(r"safe, order ([J\d ]+)", bk).group(1).split())
v["bk_r1"] = re.search(r"J1 asks for \(1,0,0\): (\w+)", bk).group(1)
v["bk_r2"] = re.search(r"J3 asks for \(0,1,1\): (\w+)", bk).group(1)
v["bk_r3"] = re.search(r"J0 asks for \(1,0,1\): (\w+)", bk).group(1)
json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in v if k not in ("provisional", "machine_desc")}))
