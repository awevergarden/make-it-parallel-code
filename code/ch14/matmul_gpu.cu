/*
 * matmul_gpu.cu -- a tiled matrix product in CUDA shared memory.
 * Make It Parallel, Chapter 14.
 *
 * Build:  nvcc -O2 -arch=sm_80 -o matmul_gpu matmul_gpu.cu
 * The per-thread code is in ../heatsim/matmul_tile.h (shared with the
 * CPU emulator). For real work, call cuBLAS (cublasDgemm) instead.
 */
#include <cuda_runtime.h>
#include "../heatsim/matmul_tile.h"

__global__ void matmul_tiled(const double *A, const double *B, double *C, int n)
{
    __shared__ double As[T * T], Bs[T * T];
    int tx = threadIdx.x, ty = threadIdx.y;
    double acc = 0.0;
    for (int t = 0; t < (n + T - 1) / T; t++) {
        mm_load(A, B, As, Bs, n, t, blockIdx.x, blockIdx.y, tx, ty);
        __syncthreads();                /* both tiles loaded */
        acc = mm_partial(As, Bs, tx, ty, acc);
        __syncthreads();                /* done reading them */
    }
    int row = blockIdx.y * T + ty, col = blockIdx.x * T + tx;
    if (row < n && col < n)
        C[row * n + col] = acc;
}

/* Host wrapper: C = A * B for n x n matrices already in GPU memory. */
void matmul(const double *A, const double *B, double *C, int n)
{
    dim3 block(T, T), grid((n + T - 1) / T, (n + T - 1) / T);
    matmul_tiled<<<grid, block>>>(A, B, C, n);
}
