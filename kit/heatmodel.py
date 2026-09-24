"""heatmodel.py -- the HeatSim v4 speedup model of Chapter 7 (a MODEL,
not a measurement). Used by values_ch07.py and figs_ch07.py so that the
text and the figures always agree.

Time per step with p threads on p cores:
    T(p) = max(compute, memory) + barrier
    compute = cells / (p * R_ws)          R_ws: measured one-core rate for
                                          the level each thread's share fits
    memory  = 24 * cells / (min(p, beta) * b1)   (only when the grids are
                                          too big for any cache; b1 is one
                                          core's bandwidth, 24 * R_mem)
    barrier = T_BARRIER (assumed)
Speedup is measured against HeatSim v1 on one core (the book's baseline).
"""
L2_PER_CORE = 2 * 1024 ** 2   # bytes, as on the test machine (assumed per core)
L2_USABLE = 0.75 * L2_PER_CORE  # share of L2 a thread's grid rows can use (assumed)
L3_USABLE = 32 * 1024 ** 2    # bytes the test VM's L3 behaved like (Ch. 5)
T_BARRIER = 5e-6              # seconds per barrier (assumed)
BETA = 4                      # memory supplies about 4 cores' worth (assumed)

def step_time(n, p, R):
    """R: dict with measured one-core v4 rates (cells/s): 'l2', 'l3', 'mem'."""
    cells = (n - 2) ** 2
    share = 16 * n * n / p                      # bytes of both grids per thread
    if share <= L2_USABLE:
        compute = cells / (p * R["l2"])
        memory = 0.0
    elif 16 * n * n <= L3_USABLE:
        compute = cells / (p * R["l3"])
        memory = 0.0
    else:
        compute = cells / (p * R["l2"])
        memory = cells / (min(p, BETA) * R["mem"])
    return max(compute, memory) + (T_BARRIER if p > 1 else 0.0)

def speedup(n, p, R, r_v1):
    """Predicted speedup of v4 on p cores over v1 (rate r_v1) on one core."""
    return ((n - 2) ** 2 / r_v1) / step_time(n, p, R)
