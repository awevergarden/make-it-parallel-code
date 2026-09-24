/*
 * scan.c -- a parallel prefix sum (inclusive scan) with OpenMP.
 * Make It Parallel, Chapter 8.
 *
 * out[i] = in[0] + in[1] + ... + in[i]. Each thread scans its own
 * block; one thread then scans the block totals; finally every thread
 * adds its offset. Integer data makes the check exact.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp -Wall -Wextra -o scan scan.c
 * Run:    OMP_NUM_THREADS=4 ./scan
 */
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

#define N 10000000L
#define MAX_THREADS 256

static void scan_parallel(const long *in, long *out, long n)
{
    long block_sum[MAX_THREADS + 1] = {0};
    #pragma omp parallel
    {
        int t = omp_get_thread_num(), p = omp_get_num_threads();
        long lo = t * n / p, hi = (t + 1) * n / p;
        long s = 0;
        for (long i = lo; i < hi; i++) {      /* pass 1: local scan */
            s += in[i];
            out[i] = s;
        }
        block_sum[t + 1] = s;
        #pragma omp barrier
        #pragma omp single
        for (int k = 1; k <= p; k++)          /* scan the block totals */
            block_sum[k] += block_sum[k - 1];
        /* implicit barrier after single */
        long offset = block_sum[t];
        for (long i = lo; i < hi; i++)        /* pass 2: add the offset */
            out[i] += offset;
    }
}

int main(void)
{
    long *in = malloc(N * sizeof *in), *out = malloc(N * sizeof *out);
    if (in == NULL || out == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    for (long i = 0; i < N; i++)
        in[i] = (i * 7919) % 13 - 6;          /* small integers, some negative */
    if (omp_get_max_threads() > MAX_THREADS) {
        fprintf(stderr, "error: at most %d threads\n", MAX_THREADS);
        return 1;
    }
    scan_parallel(in, out, N);
    long s = 0, errors = 0;                   /* check against a plain scan */
    for (long i = 0; i < N; i++) {
        s += in[i];
        errors += out[i] != s;
    }
    printf("threads,%d\nlast,%ld\nerrors,%ld\n", omp_get_max_threads(), out[N - 1], errors);
    free(in);
    free(out);
    return errors ? 1 : 0;
}
