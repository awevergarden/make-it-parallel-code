"""values_ch14.py -- Chapter 14 values: real emulation checks and compile
reports, and MODEL predictions (gpumodel.py) from published GPU specs.

Usage (from the book root):
    python3 kit/values_ch14.py RESULTS_DIR --machine "..." [--provisional]
"""
import argparse, csv, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gpumodel as gm, distmodel as dm

ap = argparse.ArgumentParser()
ap.add_argument("results")
ap.add_argument("--machine", required=True)
ap.add_argument("--provisional", action="store_true")
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "data", "ch14")
os.makedirs(DST, exist_ok=True)
if os.path.abspath(a.results) != os.path.abspath(DST):
    for f in os.listdir(a.results):
        if f.endswith((".csv", ".txt")):
            shutil.copy(os.path.join(a.results, f), DST)
rows = lambda n: list(csv.DictReader(open(os.path.join(DST, n))))
v = {"provisional": a.provisional, "machine_desc": a.machine}
f0 = lambda x: f"{x:,.0f}"

em = rows("emulation.csv")
v["emu_all"] = "yes" if all(r["result"] in ("identical", "25C ok") for r in em) else "no"
v["emu_sizes"] = ", ".join(sorted({r["n"] for r in em if r["n"] != "129"}, key=int))
mm = rows("matmul.csv")
v["mm_all_exact"] = "yes" if all(r["result"].startswith("0 wrong") for r in mm) else "no"
v["mm_sizes"] = ", ".join(r["n"] for r in mm)
bug = open(os.path.join(DST, "bug.txt")).read()
m = re.search(r"bug: center temperature after \d+ steps: (-?[\d.]+)", bug)
v["bug_value_exp"] = str(len(m.group(1).split(".")[0].lstrip("-")) - 1)

cur_fn = cur_arch = None
spills = 0
for line in open(os.path.join(DST, "ptxas.txt")):
    m1 = re.search(r"entry function '(\w+)' for '(sm_\d+)'", line)
    if m1:
        cur_fn, cur_arch = m1.groups()
        continue
    m2 = re.search(r"(\d+) bytes spill stores", line)
    if m2:
        spills += int(m2.group(1))
    m3 = re.search(r"Used (\d+) registers(?:, used \d+ barriers)?(?:, (\d+) bytes smem)?", line)
    if m3 and cur_fn:
        k = ("mm" if "matmul" in cur_fn else "red" if "block_sums" in cur_fn
             else "tiled" if "tiled" in cur_fn else "simple")
        v[f"regs_{k}_{cur_arch}"] = m3.group(1)
        v[f"smem_{k}_{cur_arch}"] = f0(int(m3.group(2))) if m3.group(2) else "0"
v["spills"] = str(spills)
occ = gm.blocks_per_sm(256, int(v["regs_tiled_sm_80"]), int(v["smem_tiled_sm_80"].replace(",", "")))
v["occ_blocks"] = str(occ)
v["occ_warps"] = str(occ * 8)
v["occ_pct"] = f0(min(occ * 8, gm.SM_WARPS) / gm.SM_WARPS * 100)
v["occ_reg_limit"] = str(gm.SM_REGS // (int(v["regs_tiled_sm_80"]) * 256))
v["occ_smem_limit"] = str(gm.SM_SMEM // int(v["smem_tiled_sm_80"].replace(",", "")))

c10 = json.load(open(os.path.join(ROOT, "data", "ch10", "values.json")))
cpu = {n: float(c10[f"r_v1_{n}"].replace(",", "")) * 1e6 for n in (256, 1024, 4096)}
v["bytes_tiled"] = f"{gm.BYTES_TILED:.1f}"
for gpu in ("A100", "H100"):
    r = gm.rate(4096, gpu=gpu)
    v[f"g_{gpu}_4096"] = f"{r / 1e9:.0f}"
    v[f"g_{gpu}_vs_cpu"] = f0(r / cpu[4096])
v["g_A100_256"] = f"{gm.rate(256) / 1e9:.1f}"
v["g_A100_256_nolaunch"] = f"{(254 ** 2) / ((254 ** 2) * gm.BYTES_TILED / gm.GPUS['A100']['bw']) / 1e9:.0f}"
v["g_A100_copy_4096"] = f"{gm.rate(4096, copy_each_step=True) / 1e9:.1f}"
v["g_copy_slowdown"] = f0(gm.step_time(4096, copy_each_step=True) / gm.step_time(4096))
v["step_us_4096"] = f"{gm.step_time(4096) * 1e6:.0f}"
v["copy_ms_4096"] = f"{2 * 8 * 4096 ** 2 / gm.PCIE_GEN4_ONE_WAY * 1e3:.1f}"
v["cpu_4096"] = c10["r_v1_4096"]
v["launch_us"] = f0(gm.LAUNCH * 1e6)
# matrix product tiles: intensity T/8 flop/byte
for t in (16, 32):
    inten = t / 8
    v[f"mm_int_{t}"] = f"{inten:.0f}"
    v[f"mm_bound_{t}"] = f"{min(inten * gm.GPUS['A100']['bw'], gm.GPUS['A100']['fp64']) / 1e12:.1f}"
v["ridge_A100"] = f"{gm.GPUS['A100']['fp64'] / gm.GPUS['A100']['bw']:.1f}"
# four GPUs, one MPI rank each, n = 16384 in row blocks
n, g = 16384, 4
row = 8 * n
t_comp = (n * n / g) * gm.BYTES_TILED / gm.GPUS["A100"]["bw"]
t_host = 2 * row / gm.PCIE_GEN4_ONE_WAY + dm.ALPHA + row / dm.BETA_NET
t_aware = dm.ALPHA + row / dm.BETA_NET
v.update(mg_comp_ms=f"{t_comp * 1e3:.2f}", mg_host_us=f"{t_host * 1e6:.0f}",
         mg_aware_us=f"{t_aware * 1e6:.0f}", mg_row_kb=f0(row / 1024),
         mg_host_pct=f"{2 * t_host / (t_comp + 2 * t_host) * 100:.0f}",
         mg_aware_pct=f"{2 * t_aware / (t_comp + 2 * t_aware) * 100:.0f}")
rd = [l.strip().split(",") for l in open(os.path.join(DST, "reduce.csv"))]
ints = [r for r in rd if r[0] == "integers"]
v["red_int_exact"] = "yes" if all(r[4] == "exact" for r in ints) else "no"
v["red_int_total"] = f0(int(ints[0][3]))
v["red_blocks"] = ", ".join(r[1] for r in ints)
harm = {r[1]: r[2] for r in rd if r[0] == "harmonic"}
v["red_seq"] = harm["sequential"]
v["red_tree_1"], v["red_tree_512"] = harm["1"], harm["512"]
v["red_rel"] = f"{abs(float(harm['512']) - float(harm['sequential'])) / float(harm['sequential']):.1e}".replace("e-", " × 10^−").replace("e+", " × 10^") + "^"
json.dump(v, open(os.path.join(DST, "values.json"), "w"), indent=1)
print(json.dumps({k: v[k] for k in v if k not in ("provisional", "machine_desc")}))
