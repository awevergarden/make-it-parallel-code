/*
 * reduce_gpu.cu -- a tree reduction in CUDA shared memory, and
 * overlapping transfers with streams.
 * Make It Parallel, Chapter 14.
 *
 * Build:  nvcc -O2 -arch=sm_80 -c reduce_gpu.cu
 * The per-thread code is in ../heatsim/reduce_block.h (shared with the
 * CPU emulator). Libraries such as CUB provide tuned reductions.
 */
#include <cuda_runtime.h>
#include "../heatsim/reduce_block.h"

__global__ void block_sums(const double *x, long n, double *partial)
{
    __shared__ double sh[RT];
    reduce_load(x, n, sh, blockIdx.x, gridDim.x, threadIdx.x);
    __syncthreads();
    for (int half = RT / 2; half > 0; half /= 2) {
        reduce_level(sh, half, threadIdx.x);
        __syncthreads();                /* this level is finished */
    }
    if (threadIdx.x == 0)
        partial[blockIdx.x] = sh[0];
}

/* Sum x[0..n) on the GPU: one launch for block sums, one to add them. */
double gpu_sum(const double *x, long n, double *partial, int blocks)
{
    block_sums<<<blocks, RT>>>(x, n, partial);
    block_sums<<<1, RT>>>(partial, blocks, partial);
    double s = 0.0;
    cudaMemcpy(&s, partial, sizeof s, cudaMemcpyDeviceToHost);
    return s;
}

/* Process a large array in chunks, overlapping each chunk's copy with
   the previous chunk's kernel by alternating two streams. The host
   buffer must be page-locked (cudaMallocHost) for copies to overlap. */
void chunked_sums(const double *host, double *dev, double *partial,
                  long n, long chunk, int blocks)
{
    cudaStream_t st[2];
    cudaStreamCreate(&st[0]);
    cudaStreamCreate(&st[1]);
    for (long off = 0, k = 0; off < n; off += chunk, k++) {
        long len = n - off < chunk ? n - off : chunk;
        cudaStream_t s = st[k % 2];
        cudaMemcpyAsync(dev + off, host + off, len * sizeof *host,
                        cudaMemcpyHostToDevice, s);
        block_sums<<<blocks, RT, 0, s>>>(dev + off, len,
                                         partial + (k % 2) * blocks);
    }
    cudaStreamSynchronize(st[0]);
    cudaStreamSynchronize(st[1]);
    cudaStreamDestroy(st[0]);
    cudaStreamDestroy(st[1]);
}
