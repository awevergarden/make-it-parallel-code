/*
 * daxpy.c -- y = a * x + y at three array sizes.
 * Make It Parallel, Chapter 6.
 *
 * The same source is built several ways (see run_ch06.sh): without
 * vectorization, and with 128-, 256-, and 512-bit vectors. On x86-64,
 * -DUSE_INTRINSICS selects a version written with SSE2 intrinsics.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp-simd -Wall -Wextra -o daxpy daxpy.c
 * Run:    ./daxpy          (prints: level,n,GFLOPs)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include "../common/timer.h"
#if defined(USE_INTRINSICS) && defined(__SSE2__)
#include <emmintrin.h>
#endif

#if defined(USE_INTRINSICS) && defined(__SSE2__)
/* Two doubles per instruction, written by hand. */
static void daxpy(long n, double a, const double *restrict x,
                  double *restrict y)
{
    __m128d va = _mm_set1_pd(a);            /* {a, a} */
    long i = 0;
    for (; i + 2 <= n; i += 2) {
        __m128d vx = _mm_loadu_pd(&x[i]);   /* x[i], x[i+1] */
        __m128d vy = _mm_loadu_pd(&y[i]);
        vy = _mm_add_pd(_mm_mul_pd(va, vx), vy);
        _mm_storeu_pd(&y[i], vy);
    }
    for (; i < n; i++)                      /* leftover element */
        y[i] = a * x[i] + y[i];
}
#else
static void daxpy(long n, double a, const double *restrict x,
                  double *restrict y)
{
    #pragma omp simd
    for (long i = 0; i < n; i++)
        y[i] = a * x[i] + y[i];
}
#endif

int main(void)
{
    const char *level[] = {"L1", "L2", "memory"};
    long sizes[] = {1024, 32768, 16777216};
    printf("level,n,GFLOPs\n");
    for (int k = 0; k < 3; k++) {
        long n = sizes[k];
        double *x = malloc(n * sizeof *x), *y = malloc(n * sizeof *y);
        if (x == NULL || y == NULL) {
            fprintf(stderr, "error: out of memory\n");
            return 1;
        }
        for (long i = 0; i < n; i++) {
            x[i] = 1.0;
            y[i] = 0.0;
        }
        long reps = (long)(4e9 / (2.0 * n)) + 1;
        double best = 1e30;
        for (int trial = 0; trial < 3; trial++) {
            double t0 = now_seconds();
            for (long r = 0; r < reps; r++)
                daxpy(n, 1e-9, x, y);
            double t = now_seconds() - t0;
            if (t < best)
                best = t;
        }
        printf("%s,%ld,%.2f\n", level[k], n, 2.0 * n * reps / best / 1e9);
        fprintf(stderr, "check %.6f\n", y[n / 2]);
        free(x);
        free(y);
    }
    return 0;
}
