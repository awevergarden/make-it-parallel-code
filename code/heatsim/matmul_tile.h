/*
 * matmul_tile.h -- per-thread work of Chapter 14's tiled GPU matrix
 * product, shared by matmul_gpu.cu and the CPU emulator.
 * Make It Parallel, companion code (Chapter 14).
 *
 * A block of T x T threads computes a T x T tile of C. For each of the
 * n / T steps along k, every thread loads one element of A and one of B
 * into shared tiles; after a barrier, each thread multiplies its row of
 * the A tile by its column of the B tile.
 */
#ifndef MATMUL_TILE_H
#define MATMUL_TILE_H

#if defined(__CUDACC__) || defined(__CUDA__)
#define HD __host__ __device__
#else
#define HD
#endif

#define T 16

HD static inline void mm_load(const double *A, const double *B, double *As,
                              double *Bs, int n, int t, int bx, int by,
                              int tx, int ty)
{
    int row = by * T + ty, col = bx * T + tx;
    int ka = t * T + tx, kb = t * T + ty;
    As[ty * T + tx] = (row < n && ka < n) ? A[row * n + ka] : 0.0;
    Bs[ty * T + tx] = (kb < n && col < n) ? B[kb * n + col] : 0.0;
}

HD static inline double mm_partial(const double *As, const double *Bs,
                                   int tx, int ty, double acc)
{
    for (int k = 0; k < T; k++)
        acc += As[ty * T + k] * Bs[k * T + tx];
    return acc;
}

#endif
