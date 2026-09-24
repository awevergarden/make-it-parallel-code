"""values_ch16.py -- Chapter 16 values: logical clocks vs skewed wall
clocks, Cristian's algorithm (simulated server clock), and totally
ordered multicast (all real runs).

Usage (from the book root):
    python3 kit/values_ch16.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, os, shutil, statistics as st

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch16")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
v = {"provisional": a.provisional, "machine_desc": a.machine}
f0 = lambda x: f"{x:,.0f}"

ev = {}
for r in rows("events.csv"):
    ev.setdefault(r["skew_ms"], {})[r["key"]] = int(r["value"])
e2, e0 = ev["2"], ev["0"]
v.update(ev_events=f0(e2["events"]), ev_msgs=f0(e2["messages"]), ev_hb=f0(e2["happened_before_pairs"]),
         ev_lviol=f0(e2["lamport_violations"]), ev_conc=f0(e2["concurrent_pairs"]),
         ev_conc_pct=f0(e2["concurrent_with_different_lamport"] / e2["concurrent_pairs"] * 100),
         ev_back_2=f0(e2["received_before_sent_by_wall_clock"]),
         ev_back_0=f0(e0["received_before_sent_by_wall_clock"]),
         ev_back_20=f0(ev["20"]["received_before_sent_by_wall_clock"]),
         ev_lviol_all=f0(sum(x["lamport_violations"] for x in ev.values())),
         hlc_viol=f0(sum(x["hlc_violations"] for x in ev.values())),
         hlc_ahead_2=f"{e2['hlc_max_ahead_us'] / 1000:.1f}",
         hlc_ahead_20=f"{ev['20']['hlc_max_ahead_us'] / 1000:.1f}",
         hlc_maxc=f0(max(x["hlc_max_counter"] for x in ev.values())))

cr = rows("cristian.csv")
err = [abs(float(r["error_ms"])) for r in cr]
viol = sum(abs(float(r["error_ms"])) > float(r["bound_ms"]) + 1e-9 for r in cr)
best = min(cr, key=lambda r: float(r["rtt_ms"]))
v.update(cr_trials=str(len(cr)), cr_viol=str(viol), cr_mean=f"{st.mean(err):.1f}",
         cr_max=f"{max(err):.1f}", cr_best_rtt=f"{float(best['rtt_ms']):.2f}",
         cr_best_err=f"{abs(float(best['error_ms'])):.3f}",
         cr_best_bound=f"{float(best['bound_ms']):.2f}")

tb = rows("tobcast.csv")
v["tob_runs"] = str(len(tb))
v["tob_all"] = "yes" if all(r["identical"] == "yes" for r in tb) else "no"
v["tob_formula"] = "yes" if all(int(r["messages"]) == int(r["processes"]) * 20 * (int(r["processes"]) ** 2 - 1)
                                 for r in tb) else "no"
for p in (2, 4, 6):
    v[f"tob_msgs_{p}"] = f0(next(int(r["messages"]) for r in tb if r["processes"] == str(p)))
    v[f"tob_per_job_{p}"] = str(p * p - 1)
for ppm in (20, 50):
    v[f"drift_{ppm}_s_day"] = f"{ppm * 1e-6 * 86400:.1f}"
json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in v if k not in ("provisional", "machine_desc")}))
