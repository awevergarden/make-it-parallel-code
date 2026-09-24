"""mmdistmodel.py -- Chapter 13's model of distributed matrix
multiplication (a MODEL, not a measurement). One process per node;
F is a measured one-core rate; the network uses Chapter 10's alpha, beta.
    compute  = 2 n^3 / (p F)
    1D ring  : (p - 1) messages of n^2/p values
    Cannon   : 2 sqrt(p) messages of n^2/p values (skew included)
    2.5D (c) : 2 sqrt(p/c^3) shifts of c n^2/p values, plus about
               3 log2(c) messages of c n^2/p to replicate A, B and reduce C
"""
import math
import distmodel as dm

def comm(n, p, alg, c=4):
    a, b = dm.ALPHA, dm.BETA_NET
    if p == 1:
        return 0.0
    blk = 8 * n * n / p                               # bytes in one n^2/p block
    if alg == "1d":
        return (p - 1) * (a + blk / b)
    if alg == "cannon":
        return 2 * math.sqrt(p) * (a + blk / b)
    steps = 2 * math.sqrt(p / c ** 3)
    return steps * (a + c * blk / b) + 3 * math.log2(c) * (a + c * blk / b)

def compute(n, p, F):
    return 2.0 * n ** 3 / (p * F)

def share(n, p, alg, F, c=4):
    t = comm(n, p, alg, c)
    return t / (t + compute(n, p, F))

def memory_values(n, p, alg, c=4):
    """Matrix values stored per process (A, B, C blocks and copies)."""
    return 3 * n * n / p * (c if alg == "2.5d" else 1)
