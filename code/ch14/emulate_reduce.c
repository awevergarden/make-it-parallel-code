/*
 * emulate_reduce.c -- run reduce_gpu.cu's tree reduction on the CPU.
 * Make It Parallel, Chapter 14.
 *
 * Checks the reduction exactly on positive, irregular integers (so a
 * missed or doubled element changes the total), then compares its
 * floating-point result with a sequential sum (Chapters 8 and 10).
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o emulate_reduce emulate_reduce.c
 */
#include <stdio.h>
#include <stdlib.h>
#include "../heatsim/reduce_block.h"

static double tree_sum(const double *x, long n, int blocks)
{
    double *partial = malloc(blocks * sizeof *partial), sh[RT];
    if (partial == NULL)
        exit(1);
    for (int pass = 0; pass < 2; pass++) {    /* two launches */
        const double *in = pass == 0 ? x : partial;
        long len = pass == 0 ? n : blocks;
        int nb = pass == 0 ? blocks : 1;
        for (int b = 0; b < nb; b++) {
            for (int t = 0; t < RT; t++)
                reduce_load(in, len, sh, b, nb, t);
            for (int half = RT / 2; half > 0; half /= 2)
                for (int t = 0; t < RT; t++)  /* then __syncthreads() */
                    reduce_level(sh, half, t);
            partial[b] = sh[0];
        }
    }
    double s = partial[0];
    free(partial);
    return s;
}

int main(void)
{
    long n = 10000000L;
    double *x = malloc(n * sizeof *x);
    if (x == NULL)
        return 1;
    long exact = 0;
    for (long i = 0; i < n; i++) {
        long v = (i * 7919 + (i * i) % 997) % 1001 + 1;   /* positive, irregular */
        x[i] = (double)v;
        exact += v;
    }
    for (int blocks = 1; blocks <= 1024; blocks *= 8)
        printf("integers,%d,%.0f,%ld,%s\n", blocks, tree_sum(x, n, blocks), exact,
               tree_sum(x, n, blocks) == (double)exact ? "exact" : "WRONG");
    double seq = 0.0;
    for (long i = 0; i < n; i++) {
        x[i] = 1.0 / (double)(i + 1);
        seq += x[i];
    }
    printf("harmonic,sequential,%.17g\n", seq);
    for (int blocks = 1; blocks <= 1024; blocks *= 8)
        printf("harmonic,%d,%.17g\n", blocks, tree_sum(x, n, blocks));
    free(x);
    return 0;
}
