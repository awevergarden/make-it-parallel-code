"""aimodel.py -- Chapter 15's back-of-the-envelope models for training at
scale (MODELS, not measurements).
"""
BYTES_PER_PARAM = 16      # mixed-precision Adam: 2 (weights) + 2 (gradients)
                          # + 4 (fp32 master weights) + 8 (two Adam moments)
GPU_MEMORY = 80e9         # an 80 GB accelerator
NVLINK = 450e9            # bytes/s each way (H100 NVLink: 900 GB/s total)
NETWORK = 50e9            # bytes/s each way (a 400 Gb/s network card, assumed)
ALPHA = 2e-6

def states_bytes(params):
    return params * BYTES_PER_PARAM

def ring_allreduce(nbytes, p, beta, alpha=ALPHA):
    return 2 * (p - 1) * (alpha + nbytes / (p * beta))

def bubble(stages, microbatches):
    """Idle fraction of a simple (GPipe-style) pipeline schedule."""
    return (stages - 1) / (microbatches + stages - 1)
