"""values_ch15.py -- Chapter 15 values: systolic simulation, precision
experiment, data-parallel training (all real), and MODEL arithmetic.

Usage (from the book root):
    python3 kit/values_ch15.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aimodel as am

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch15")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
v = {"provisional": a.provisional, "machine_desc": a.machine}
f0 = lambda x: f"{x:,.0f}"

sy = rows("systolic.csv")
v["sys_all_exact"] = "yes" if all(r["wrong"] == "0" for r in sy) else "no"
for r in sy:
    if r["mode"] == "os":
        v[f"os_cycles_{r['n']}"] = f0(int(r["cycles"]))
        v[f"os_util_{r['n']}"] = f"{float(r['utilization']) * 100:.0f}"
    else:
        v[f"ws_util_{r['m']}"] = f"{float(r['utilization']) * 100:.1f}"
        v[f"ws_cycles_{r['m']}"] = f0(int(r["cycles"]))
pr = rows("precision.csv")
for r in pr:
    key = f"pe_{r['format']}_{'own' if r['accumulate'] == r['format'] else 'wide'}"
    v[key] = r["relative_error"]
v["pe_ratio_fp16"] = f"{float(v['pe_float16_own']) / float(v['pe_float16_wide']):.0f}"
v["pe_ratio_bf16"] = f"{float(v['pe_bfloat16_own']) / float(v['pe_bfloat16_wide']):.0f}"

tr = open(os.path.join(DST, "train.txt")).read()
loss = {}
for m in re.finditer(r"loss,(\w+),(\d+),(\d+),([\d.e+-]+)", tr):
    loss[(m.group(1), int(m.group(2)), int(m.group(3)))] = m.group(4)
v["tr_loss0"] = f"{float(loss[('mpi', 1, 0)]):.2f}"
v["tr_loss_end"] = f"{float(loss[('mpi', 1, 300)]):.2e}"
finals = [float(loss[(md, p, 300)]) for md in ("mpi", "ring") for p in (1, 2, 4, 8)]
v["tr_spread"] = f"{(max(finals) - min(finals)) / min(finals):.0e}"
wts = re.findall(r"weights,(\w+),(\d+),([\d.e+-]+),([\d.e+-]+)", tr)
v["tr_werr"] = f"{float(wts[0][3]):.4f}"
rb = {int(m.group(1)): (int(m.group(2)), int(m.group(3)))
      for m in re.finditer(r"ringbytes,(\d+),(\d+),(\d+)", tr)}
for p in (2, 4, 8):
    v[f"rb_{p}"] = f0(rb[p][0])
v["rb_match"] = "yes" if all(rb[p][0] == rb[p][1] for p in (2, 4, 8)) else "no"

for name, P in (("1b", 1e9), ("7b", 7e9), ("70b", 70e9), ("405b", 405e9)):
    s = am.states_bytes(P)
    v[f"mem_{name}"] = f"{s / 1e9:,.0f}"
    v[f"gpus_{name}"] = f0(-(-s // am.GPU_MEMORY))
for m in (1, 4, 16, 64):
    v[f"bub_{m}"] = f0(am.bubble(4, m) * 100)
grad = 2 * 7e9                                          # 7B parameters, 2-byte gradients
v["ar_nvlink_ms"] = f0(am.ring_allreduce(grad, 8, am.NVLINK) * 1e3)
v["ar_net_ms"] = f0(am.ring_allreduce(grad, 64, am.NETWORK) * 1e3)
v["grad_gb"] = f0(grad / 1e9)
json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in v if k not in ("provisional", "machine_desc")}))
