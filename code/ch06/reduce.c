/*
 * reduce.c -- vectorizing a sum, with and without permission.
 * Make It Parallel, Chapter 6.
 *
 * sum_plain() is an ordinary loop; the compiler may vectorize it only
 * if allowed to reorder floating-point additions (-ffast-math).
 * sum_simd() grants that permission for this one loop, with
 * "#pragma omp simd reduction(+:s)".
 *
 * Build:  gcc -std=c17 -O2 -fopenmp-simd -Wall -Wextra -o reduce reduce.c
 * Run:    ./reduce         (prints: function,ns_per_add,sum)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include "../common/timer.h"

#define N 4096
#define REPS 100000

static double sum_plain(const double *x, long n)
{
    double s = 0.0;
    for (long i = 0; i < n; i++)
        s += x[i];
    return s;
}

static double sum_simd(const double *x, long n)
{
    double s = 0.0;
    #pragma omp simd reduction(+:s)
    for (long i = 0; i < n; i++)
        s += x[i];
    return s;
}

int main(void)
{
    double *x = malloc(N * sizeof *x);
    if (x == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    for (long i = 0; i < N; i++)
        x[i] = 1.0 / (double)(i + 1);

    double (*fn[])(const double *, long) = {sum_plain, sum_simd};
    const char *name[] = {"plain", "simd"};
    printf("function,ns_per_add,sum\n");
    for (int v = 0; v < 2; v++) {
        double s = 0.0, t0 = now_seconds();
        for (int r = 0; r < REPS; r++)
            s = fn[v](x, N);
        double t = now_seconds() - t0;
        printf("%s,%.4f,%.17g\n", name[v], t / ((double)N * REPS) * 1e9, s);
    }
    free(x);
    return 0;
}
