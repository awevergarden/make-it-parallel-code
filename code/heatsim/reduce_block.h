/*
 * reduce_block.h -- per-thread work of Chapter 14's tree reduction,
 * shared by reduce_gpu.cu and the CPU emulator.
 * Make It Parallel, companion code (Chapter 14).
 *
 * A block of RT threads first sums its share of the input with a
 * grid-stride loop, then halves the number of active threads at each
 * level of a tree in shared memory until thread 0 holds the block's sum.
 */
#ifndef REDUCE_BLOCK_H
#define REDUCE_BLOCK_H

#if defined(__CUDACC__) || defined(__CUDA__)
#define HD __host__ __device__
#else
#define HD
#endif

#define RT 256                          /* threads per block */

/* Phase 1: each thread adds up every (blocks * RT)-th element. */
HD static inline void reduce_load(const double *x, long n, double *sh,
                                  int b, int blocks, int t)
{
    double s = 0.0;
    for (long i = (long)b * RT + t; i < n; i += (long)blocks * RT)
        s += x[i];
    sh[t] = s;
}

/* One tree level: threads below `half` add in the partner's value. */
HD static inline void reduce_level(double *sh, int half, int t)
{
    if (t < half)
        sh[t] += sh[t + half];
}

#endif
