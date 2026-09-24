/*
 * stride.c -- how access order changes speed.
 * Make It Parallel, Chapter 5.
 *
 * 1. Sums every s-th element of a 1 GiB array, for s = 1 to 64.
 * 2. Sums an 8,192 x 16,384 matrix row by row, then column by column.
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o stride stride.c
 * Run:    ./stride         (prints: kind,param,ns_per_element)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include "../common/timer.h"

#define ROWS 8192L
#define COLS 16384L
#define N (ROWS * COLS)        /* 2^27 doubles = 1 GiB */

int main(void)
{
    double *a = malloc(N * sizeof *a);
    if (a == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    for (long i = 0; i < N; i++)
        a[i] = 1.0;
    printf("kind,param,ns_per_element\n");

    double check = 0.0;
    for (long s = 1; s <= 64; s *= 2) {
        long count = N / s;
        double sum = 0.0, t0 = now_seconds();
        for (long k = 0; k < count; k++)
            sum += a[k * s];
        double t = now_seconds() - t0;
        check += sum;
        printf("stride,%ld,%.3f\n", s, t / count * 1e9);
    }

    double sum = 0.0, t0 = now_seconds();
    for (long i = 0; i < ROWS; i++)            /* row by row */
        for (long j = 0; j < COLS; j++)
            sum += a[i * COLS + j];
    printf("order,row,%.3f\n", (now_seconds() - t0) / N * 1e9);
    check += sum;

    sum = 0.0;
    t0 = now_seconds();
    for (long j = 0; j < COLS; j++)            /* column by column */
        for (long i = 0; i < ROWS; i++)
            sum += a[i * COLS + j];
    printf("order,column,%.3f\n", (now_seconds() - t0) / N * 1e9);
    check += sum;

    fprintf(stderr, "check %.0f\n", check);    /* keep every sum */
    free(a);
    return 0;
}
