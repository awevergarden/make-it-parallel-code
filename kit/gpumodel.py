"""gpumodel.py -- Chapter 14's model of HeatSim v8 on a GPU (a MODEL; the
book's test machine has no GPU). Bandwidths and peaks are published
datasheet values; the launch overhead is an assumption.
"""
GPUS = {                         # memory GB/s, FP64 TFLOPS (vector, Tensor Core)
    "A100": {"bw": 2039e9, "fp64": 9.7e12, "fp64_tc": 19.5e12},
    "H100": {"bw": 3350e9, "fp64": 34e12, "fp64_tc": 67e12},
}
PCIE_GEN4_ONE_WAY = 32e9         # half of the A100 datasheet's 64 GB/s (both ways)
LAUNCH = 5e-6                    # seconds per kernel launch (assumed)
BX, BY = 32, 8
BYTES_TILED = 8 * (BX + 2) * (BY + 2) / (BX * BY) + 8   # read tile + halo, write
BYTES_SIMPLE_WORST = 48          # 5 reads + 1 write, no cache reuse at all

def step_time(n, gpu="A100", bytes_per_cell=BYTES_TILED, copy_each_step=False):
    cells = (n - 2) ** 2
    t = cells * bytes_per_cell / GPUS[gpu]["bw"] + LAUNCH
    if copy_each_step:                           # grid to host and back
        t += 2 * 8 * n * n / PCIE_GEN4_ONE_WAY
    return t

def rate(n, **kw):
    return (n - 2) ** 2 / step_time(n, **kw)

# SM limits for occupancy (A100, compute capability 8.0)
SM_WARPS, SM_REGS, SM_SMEM = 64, 65536, 164 * 1024

def blocks_per_sm(threads, regs, smem):
    return min(SM_WARPS * 32 // threads, SM_REGS // (regs * threads),
               SM_SMEM // smem if smem else 10 ** 9)
