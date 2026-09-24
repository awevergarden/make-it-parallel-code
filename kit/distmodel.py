"""distmodel.py -- Chapter 10's model of HeatSim v6 on a cluster (a MODEL,
not a measurement). One process per node; each node has its own memory,
so there is no shared-bandwidth cap. Per step:
    T(p) = cells / (p * R_share) + 2 * (ALPHA + 8 n / BETA_NET)
R_share: measured one-process rate for the cache level that one process's
share of the grids (about 16 n^2 / p bytes) fits in (thresholds from
heatmodel.py). Two MPI_Sendrecv calls per step, each moving one row.
"""
import heatmodel as hm

ALPHA = 2e-6          # seconds per message (assumed network latency)
BETA_NET = 10e9       # bytes/s per link (assumed network bandwidth)

def rate(n, p, R):
    share = 16 * n * n / p
    if share <= hm.L2_USABLE:
        return R["l2"]
    if share <= hm.L3_USABLE:
        return R["l3"]
    return R["mem"]

def comm_time(n, p):
    return 0.0 if p == 1 else 2 * (ALPHA + 8 * n / BETA_NET)

def step_time(n, p, R):
    cells = (n - 2) ** 2
    return cells / (p * rate(n, p, R)) + comm_time(n, p)

def speedup(n, p, R, r_v1):
    return ((n - 2) ** 2 / r_v1) / step_time(n, p, R)
