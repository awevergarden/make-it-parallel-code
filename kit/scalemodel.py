"""scalemodel.py -- Chapter 12's models of HeatSim on a cluster (MODELS,
not measurements). One process per node, as in Chapter 10, but with row
or square-block decomposition. Rates R come from measured one-process
runs; the network uses Chapter 10's alpha and beta (checked in Ch. 11).
"""
import math
import heatmodel as hm
import distmodel as dm

def dims(p):
    """A near-square process grid, as MPI_Dims_create gives for powers of two."""
    k = int(round(math.log2(p)))
    return 2 ** ((k + 1) // 2), 2 ** (k // 2)       # (rows of processes, columns)

def rate(n, p, R):
    share = 16 * n * n / p
    if share <= hm.L2_USABLE:
        return R["l2"]
    if share <= hm.L3_USABLE:
        return R["l3"]
    return R["mem"]

def comm(n, p, layout):
    if p == 1:
        return 0.0
    a, b = dm.ALPHA, dm.BETA_NET
    if layout == "rows":
        return 2 * (a + 8 * n / b)
    py, px = dims(p)
    t = 0.0
    if py > 1:
        t += 2 * (a + 8 * (n / px) / b)             # up and down: rows of n/px values
    if px > 1:
        t += 2 * (a + 8 * (n / py) / b)             # left and right: columns
    return t

def step_time(n, p, R, layout):
    return (n - 2) ** 2 / (p * rate(n, p, R)) + comm(n, p, layout)

def speedup(n, p, R, r_v1, layout):
    return ((n - 2) ** 2 / r_v1) / step_time(n, p, R, layout)

def weak_efficiency(m, p, R, layout):
    """Each process keeps an m x m block; the grid grows as m * sqrt(p)."""
    n = int(round(m * math.sqrt(p))) + 2           # +2: the fixed edge rows/columns
    return step_time(m + 2, 1, R, layout) / step_time(n, p, R, layout)

def halo_bytes(n_interior, p, layout):
    """Bytes the busiest process sends per step (exact, for even splits)."""
    if p == 1:
        return 0
    if layout == "rows":
        return 8 * n_interior * min(2, p - 1)
    py, px = dims(p)
    return (8 * (n_interior // px) * min(2, py - 1)
            + 8 * (n_interior // py) * min(2, px - 1))
