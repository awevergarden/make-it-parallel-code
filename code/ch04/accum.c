/*
 * accum.c -- dependency chains: summing with 1, 2, 4, or 8 accumulators.
 * Make It Parallel, Chapter 4.
 *
 * Every version adds the same numbers. With one accumulator, each
 * addition must wait for the previous one; with k accumulators, k
 * independent chains can overlap in the pipeline.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o accum accum.c
 * Run:    ./accum        (prints: accumulators,ns_per_add,sum)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include "../common/timer.h"

#define N 4096                 /* 32 KB of doubles: stays in cache */
#define REPS 50000             /* about 200 million additions      */

static double sum1(const double *a)
{
    double s0 = 0.0;
    for (int i = 0; i < N; i++)
        s0 += a[i];
    return s0;
}

static double sum2(const double *a)
{
    double s0 = 0.0, s1 = 0.0;
    for (int i = 0; i < N; i += 2) {
        s0 += a[i];
        s1 += a[i + 1];
    }
    return s0 + s1;
}

static double sum4(const double *a)
{
    double s0 = 0.0, s1 = 0.0, s2 = 0.0, s3 = 0.0;
    for (int i = 0; i < N; i += 4) {
        s0 += a[i];
        s1 += a[i + 1];
        s2 += a[i + 2];
        s3 += a[i + 3];
    }
    return (s0 + s1) + (s2 + s3);
}

static double sum8(const double *a)
{
    double s0 = 0.0, s1 = 0.0, s2 = 0.0, s3 = 0.0;
    double s4 = 0.0, s5 = 0.0, s6 = 0.0, s7 = 0.0;
    for (int i = 0; i < N; i += 8) {
        s0 += a[i];
        s1 += a[i + 1];
        s2 += a[i + 2];
        s3 += a[i + 3];
        s4 += a[i + 4];
        s5 += a[i + 5];
        s6 += a[i + 6];
        s7 += a[i + 7];
    }
    return ((s0 + s1) + (s2 + s3)) + ((s4 + s5) + (s6 + s7));
}

int main(void)
{
    double *a = malloc(N * sizeof *a);
    if (a == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    for (int i = 0; i < N; i++)
        a[i] = 1.0 / (i + 1);

    double (*fn[])(const double *) = {sum1, sum2, sum4, sum8};
    int acc[] = {1, 2, 4, 8};
    printf("accumulators,ns_per_add,sum\n");
    for (int v = 0; v < 4; v++) {
        double total = 0.0;
        double t0 = now_seconds();
        for (int r = 0; r < REPS; r++)
            total += fn[v](a);
        double t = now_seconds() - t0;
        printf("%d,%.4f,%.6f\n", acc[v], t / ((double)N * REPS) * 1e9,
               total / REPS);
    }
    free(a);
    return 0;
}
