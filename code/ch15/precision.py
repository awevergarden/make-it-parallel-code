"""precision.py -- how much accuracy does a matrix product lose in
low-precision formats? Make It Parallel, Chapter 15.

Rounds the inputs of C = A B to each format, multiplies them with either
32-bit accumulation (as tensor cores and TPUs do) or accumulation in the
format itself, and reports the relative error against the float64
product of the original matrices (Frobenius norm). float16 uses NumPy's
native type; bfloat16 and FP8 (E4M3) are emulated by rounding; int8 uses
symmetric per-matrix scaling.
Run:  python3 precision.py      (prints CSV)
"""
import numpy as np

def round_float(x, mant, emin, emax_value):
    """Round to a binary format with `mant` stored fraction bits, smallest
    normal exponent emin, and largest finite value emax_value (to nearest,
    ties to even; subnormals kept; overflow saturates)."""
    x = np.asarray(x, dtype=np.float64)
    m, e = np.frexp(x)                       # x = m * 2**e, 0.5 <= |m| < 1
    e = np.maximum(e, emin + 1)              # below the normal range: subnormal steps
    step = np.ldexp(1.0, e - (mant + 1))
    y = np.round(x / step) * step
    return np.clip(y, -emax_value, emax_value)

FORMATS = {
    "float32":  lambda x: x.astype(np.float32).astype(np.float64),
    "bfloat16": lambda x: round_float(x, 7, -126, 3.39e38),
    "float16":  lambda x: x.astype(np.float16).astype(np.float64),
    "fp8_e4m3": lambda x: round_float(x, 3, -6, 448.0),
}

def int8(x):
    scale = np.max(np.abs(x)) / 127.0
    return np.clip(np.round(x / scale), -127, 127) * scale

rng = np.random.default_rng(2026)
m, k, n = 64, 4096, 64                       # a long inner dimension
A = rng.standard_normal((m, k))
B = rng.standard_normal((k, n))
exact = A @ B
rel = lambda C: np.linalg.norm(C - exact) / np.linalg.norm(exact)

print("format,bits,accumulate,relative_error")
for name, f in FORMATS.items():
    bits = {"float32": 32, "bfloat16": 16, "float16": 16, "fp8_e4m3": 8}[name]
    Ar, Br = f(A), f(B)
    C32 = (Ar.astype(np.float32) @ Br.astype(np.float32)).astype(np.float64)
    print(f"{name},{bits},float32,{rel(C32):.2e}")
    if name in ("float16", "bfloat16"):
        C = np.zeros((m, n))                 # accumulate in the format itself
        for p in range(k):
            C = f(C + f(np.outer(Ar[:, p], Br[p, :])))
        print(f"{name},{bits},{name},{rel(C):.2e}")
Aq, Bq = int8(A), int8(B)
print(f"int8,8,int32 (exact),{rel(Aq @ Bq):.2e}")
