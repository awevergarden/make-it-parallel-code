"""blas_rate.py -- one-core speed of a tuned BLAS matrix product.
Make It Parallel, Chapter 13.

Times NumPy's matrix product, which calls an optimized dgemm from a BLAS
library such as OpenBLAS, restricted to one thread, for several sizes.
Run:  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 blas_rate.py
Prints: n,GFLOPs (best of 3)
"""
import os, time
import numpy as np

print("n,GFLOPs")
rng = np.random.default_rng(1)
for n in (512, 1024, 2048, 4096):
    A = rng.uniform(-1, 1, (n, n))
    B = rng.uniform(-1, 1, (n, n))
    best = 1e30
    for _ in range(3):
        t0 = time.perf_counter()
        C = A @ B
        best = min(best, time.perf_counter() - t0)
    print(f"{n},{2 * n ** 3 / best / 1e9:.1f}")
