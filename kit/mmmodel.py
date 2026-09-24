"""mmmodel.py -- Chapter 8's model of parallel matrix multiplication
(a MODEL, not a measurement).

Each version's speed on p cores is capped twice:
    rate(p) = min(p * R1, B_shared / bytes_per_flop)
R1: measured one-core rate. bytes_per_flop: traffic to the shared cache
and memory, from counting loads and stores (see Chapter 8, Table 8.4).
B_shared: bandwidth all cores share, assumed to be BETA times one
core's measured memory bandwidth (Chapter 5).
"""
import heatmodel as hm

BW_ONE_CORE = 16.3e9          # bytes/s, one core from memory (Chapter 5, measured)
BETA = hm.BETA                # same assumption as the HeatSim model
BS = 64                       # tile size
BYTES_PER_FLOP = {
    "ikj": 4.0,               # one 8-byte element of B per 2 flops
    "tiled": 12.0 / BS,       # B, C tiles reused BS times (0.19 B/flop)
}

def rate(version, p, r1):
    shared = BETA * BW_ONE_CORE
    return min(p * r1, shared / BYTES_PER_FLOP[version])
