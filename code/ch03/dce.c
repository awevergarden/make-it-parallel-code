/*
 * dce.c -- a benchmark the compiler can delete.
 * Make It Parallel, Chapter 3.
 *
 * sum_unused() computes a sum and throws it away, so an optimizing
 * compiler may remove the loop entirely. sum_used() prints its
 * result, so the loop must run.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o dce dce.c
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include "../common/timer.h"

#define N 300000000L

static void sum_unused(long n)
{
    double sum = 0.0;
    for (long k = 0; k < n; k++)
        sum += 1.0 / (double)(k + 1);
}

static double sum_used(long n)
{
    double sum = 0.0;
    for (long k = 0; k < n; k++)
        sum += 1.0 / (double)(k + 1);
    return sum;
}

int main(void)
{
    double t0 = now_seconds();
    sum_unused(N);
    double t_unused = now_seconds() - t0;

    t0 = now_seconds();
    double s = sum_used(N);
    double t_used = now_seconds() - t0;

    printf("result discarded: %.6f s\n", t_unused);
    printf("result printed:   %.6f s  (sum = %.6f)\n", t_used, s);
    return 0;
}
