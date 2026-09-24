"""values_ch20.py -- Chapter 20 values: doubling times fitted to published
data, the queue simulation against Erlang C, and capacity planning.

Usage (from the book root):
    python3 kit/values_ch20.py RESULTS_DIR --machine "..."
"""
import argparse, csv, json, math, os, shutil

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch20")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
v = {"provisional": False, "machine_desc": a.machine}

fits = {r["series"]: r for r in rows("fits.csv")}
key = {"transistors all": "tr_all", "transistors to 2006": "tr_early", "transistors 2006 on": "tr_late",
       "top500 all": "t5_all", "top500 1993-2013": "t5_early", "top500 2013-2026": "t5_late"}
for name, k in key.items():
    d = float(fits[name]["doubling_years"])
    v[f"{k}_years"] = f"{d:.2f}"
    v[f"{k}_months"] = f"{d * 12:.0f}"
    v[f"{k}_factor10"] = f"{2 ** (10 / d):,.0f}"          # growth per decade
    v[f"{k}_worst"] = fits[name]["worst_factor"]
data = rows("growth_data.csv")
tr = [r for r in data if r["kind"] == "transistors"]
v["tr_n"] = str(len(tr))
_r = float(tr[-1]['value']) / float(tr[0]['value'])
_e = int(math.floor(math.log10(_r)))
v["tr_ratio"] = f"{_r / 10 ** _e:.1f} × 10^{_e}^"
t5 = [r for r in data if r["kind"] == "top500"]
v["t5_n"] = str(len(t5))
v["t5_ratio"] = f"about {float(t5[-1]['value']) / float(t5[0]['value']) / 1e6:.0f} million"

def erlang_c_wait(c, rho, mean=10.0):
    lam, mu = rho * c / mean, 1 / mean
    A = lam / mu
    s = sum(A ** k / math.factorial(k) for k in range(c))
    top = A ** c / math.factorial(c) * c / (c - A)
    return top / (s + top) / (c * mu - lam)

q = rows("queue.csv")
exp_ = {float(r["utilization"]): float(r["mean_wait_min"]) for r in q if r["jobs"] == "exp"}
worst_err = 0
for rho, w in exp_.items():
    th = erlang_c_wait(8, rho)
    worst_err = max(worst_err, abs(w - th) / th)
    k = f"{int(round(rho * 100))}"
    v[f"q_sim_{k}"] = f"{w:.2f}"
    v[f"q_th_{k}"] = f"{th:.2f}"
v["q_worst_err"] = f"{worst_err * 100:.0f}"
v["q_fixed_80"] = f"{float(next(r['mean_wait_min'] for r in q if r['jobs'] == 'fixed')):.2f}"
v["q_mixed_80"] = f"{float(next(r['mean_wait_min'] for r in q if r['jobs'] == 'mixed')):.2f}"
cs2 = (0.9 * 2 * 5 ** 2 + 0.1 * 2 * 55 ** 2 - 100) / 100             # mixed jobs: squared CV
v["q_mixed_cs2"] = f"{cs2:.1f}"
v["q_kingman_mixed"] = f"{(1 + cs2) / 2 * exp_[0.8]:.1f}"
v["q_kingman_fixed"] = f"{0.5 * exp_[0.8]:.1f}"

# capacity planning: 8 workers at 50% today, arrivals +5% per month, target mean wait 5 min
target, growth = 5.0, 1.05
base_lambda = 0.5 * 8 / 10.0
def wait_at(month, c):
    rho = base_lambda * growth ** month * 10.0 / c
    return erlang_c_wait(c, rho) if rho < 1 else float("inf")
m = 0
while wait_at(m, 8) <= target:
    m += 1
v["plan_month_8"] = str(m)
v["plan_rho_at_month"] = f"{base_lambda * growth ** m * 10 / 8 * 100:.0f}"
for months in (12, 24, 36):
    c = 1
    while wait_at(months, c) > target:
        c += 1
    v[f"plan_workers_{months}"] = str(c)
v["plan_doubling_months"] = f"{math.log(2) / math.log(growth):.1f}"
# how far one exponential fitted to all the TOP500 data overshoots in 2026,
# starting from the 2013 system (what a 2013 planner using it would expect)
f_all = fits["top500 all"]
d_all = float(f_all["doubling_years"])
t2013 = next(r for r in t5 if r["name"] == "Tianhe-2")
t2026 = t5[-1]
expected = float(t2013["value"]) * 2 ** ((float(t2026["year"]) - float(t2013["year"])) / d_all)
v["t5_overshoot"] = f"{expected / float(t2026['value']):.0f}"
early = next(r for r in t5 if r["name"] == "CM-5")
v["t5_ratio_1993_2013"] = f"{float(t2013['value']) / float(early['value']):,.0f}"
v["t5_ratio_2013_2026"] = f"{float(t2026['value']) / float(t2013['value']):,.0f}"
v["t5_pred_1993_2013"] = f"{2 ** ((float(t2013['year']) - float(early['year'])) / float(fits['top500 1993-2013']['doubling_years'])):,.0f}"
v["t5_pred_2013_2026"] = f"{2 ** ((float(t2026['year']) - float(t2013['year'])) / float(fits['top500 2013-2026']['doubling_years'])):,.0f}"
for r in rows("pool.csv"):
    c = int(r["workers"])
    v[f"pool_sim_{c}"] = f"{float(r['mean_wait_min']):.2f}"
    v[f"pool_th_{c}"] = f"{erlang_c_wait(c, 0.8):.2f}"
v["pool_ratio"] = f"{float(v['pool_sim_4']) / float(v['pool_sim_32']):.0f}"
raw = fits["top500 raw-scale fit"]
v["raw_years"] = f"{float(raw['doubling_years']):.2f}"
v["raw_miss"] = f"{float(raw['worst_factor']):,.0f}"
json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print({k: v[k] for k in v if k.startswith(("tr_", "t5_", "q_", "plan"))})
