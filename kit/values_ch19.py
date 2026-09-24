"""values_ch19.py -- Chapter 19 values, derived from earlier chapters'
measurements (data/chNN/values.json) plus a few published or assumed
costs, each labeled. No new experiment: the chapter collects the book's.

Usage (from the book root):
    python3 kit/values_ch19.py --machine "..."
"""
import argparse, json, math, os

ap = argparse.ArgumentParser()
ap.add_argument("--machine", required=True)
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch19")
os.makedirs(DST, exist_ok=True)
V = lambda n: json.load(open(os.path.join(ROOT, "data", f"ch{n:02d}", "values.json")))
num = lambda x: float(str(x).replace(",", ""))
c4, c5, c7, c8, c9, c10, c11, c14 = (V(n) for n in (4, 5, 7, 8, 9, 10, 11, 14))

# (key, label, seconds, source) -- source: measured | published | assumed
costs = [
    ("l1", "L1 cache hit", num(c5["lat_l1"]) * 1e-9, "measured", "5"),
    ("atomic", "atomic increment", num(c7["cost_atomic_ns"]) * 1e-9, "measured", "7"),
    ("branch", "branch misprediction", num(c4["br_penalty_ns"]) * 1e-9, "measured", "4"),
    ("mutex", "mutex lock and unlock", num(c7["cost_mutex_ns"]) * 1e-9, "measured", "7"),
    ("mem", "main-memory access", num(c5["lat_mem"]) * 1e-9, "measured", "5"),
    ("mpi", "MPI message, same machine", num(c10["a_mpi"]) * 1e-6, "measured", "10"),
    ("pipe", "pipe message", num(c9["a_pipe"]) * 1e-6, "measured", "9"),
    ("cluster", "cluster network message", 2.5e-6, "published", "11"),
    ("tcp", "TCP message, same machine", num(c9["a_tcp"]) * 1e-6, "measured", "9"),
    ("fork", "OpenMP fork or barrier", num(c8["m_fork_us"]) * 1e-6, "assumed", "8"),
    ("launch", "GPU kernel launch", num(c14["launch_us"]) * 1e-6, "assumed", "14"),
    ("thread", "create and join a thread", num(c7["cost_create_us"]) * 1e-6, "measured", "7"),
    ("wan", "internet message (one way)", num(c11["wan_alpha_ms"]) * 1e-3, "measured", "11"),
]
cell = 1.0 / (num(c10["r_v1_4096"]) * 1e6)       # seconds per HeatSim update, one core, memory-bound
v = {"provisional": False, "machine_desc": a.machine, "cell_ns": f"{cell * 1e9:.1f}",
     "cpu_rate": c10["r_v1_4096"]}
rows = []
for key, label, sec, src, ch in costs:
    cells = 10 * sec / cell                      # overhead under 10 percent
    side = math.sqrt(cells)
    v[f"cost_{key}"] = (f"{sec * 1e9:.1f} ns" if sec < 1e-6 else
                        f"{sec * 1e6:.1f} µs" if sec < 1e-3 else f"{sec * 1e3:.0f} ms")
    v[f"min_{key}"] = f"{cells:,.0f}" if cells < 1e6 else f"{cells / 1e6:,.1f} million"
    v[f"side_{key}"] = f"{side:,.0f}"
    rows.append({"key": key, "label": label, "seconds": sec, "source": src, "chapter": ch})
json.dump(rows, open(os.path.join(DST, "costs.json"), "w"), indent=1)
v["ratio_wan_l1"] = f"{costs[-1][2] / costs[0][2]:.0e}".replace("e+0", " × 10^").replace("e+", " × 10^") + "^"
v["gpu_min_cells"] = f"{10 * 5e-6 * 106e9 / 1e6:.1f}"       # at Ch14's modeled A100 rate
v["gpu_min_side"] = f"{math.sqrt(10 * 5e-6 * 106e9):,.0f}"
# ---- case studies (arithmetic on measured one-core rates and Ch. 13-14 figures)
r1024 = num(c10["r_v1_1024"]) * 1e6
run_s = (1022 ** 2) * 10000 / r1024                 # one 1,024-grid run, 10,000 steps
v["cs_a_run_s"] = f"{run_s:.0f}"
v["cs_a_total_h"] = f"{10000 * run_s / 3600:,.0f}"
v["cs_a_ratio"] = f"{run_s / num(c11['wan_alpha_ms']) * 1e3:,.0f}"
upd = 32766 ** 2 * 1e5                               # 32,768 grid, 100,000 steps
v["cs_b_core_h"] = f"{upd / (num(c10['r_v1_4096']) * 1e6) / 3600:,.0f}"
v["cs_b_gpu_min"] = f"{upd / 106e9 / 60:,.0f}"
v["cs_b_gb"] = f"{2 * 8 * 32768 ** 2 / 1e9:.0f}"
c13 = V(13)
flops = 2 * 64 ** 3
v["cs_c_kflop"] = f"{flops / 1e3:,.0f}"
v["cs_c_loop_us"] = f"{flops / (num(c13['F_gflops']) * 1e9) * 1e6:.0f}"
v["cs_c_blas_us"] = f"{flops / (num(c13['blas_2048']) * 1e9) * 1e6:.0f}"
json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print({k: v[k] for k in v if k.startswith(("cost_", "min_", "side_", "cell", "ratio", "gpu"))})
