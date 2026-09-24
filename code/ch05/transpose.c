/*
 * transpose.c -- B = A^T for an N x N matrix, naive and tiled.
 * Make It Parallel, Chapter 5.
 *
 * The naive loop reads A along rows but writes B down columns
 * (stride N). The tiled loop transposes 32 x 32 blocks, so the
 * lines of both matrices it touches stay in the cache.
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o transpose transpose.c
 * Run:    ./transpose naive|tiled N     (prints ns per element)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../common/timer.h"

#define TS 32

static void naive(const double *restrict A, double *restrict B, int n)
{
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            B[(size_t)j * n + i] = A[(size_t)i * n + j];
}

static void tiled(const double *restrict A, double *restrict B, int n)
{
    for (int ii = 0; ii < n; ii += TS)
        for (int jj = 0; jj < n; jj += TS)
            for (int i = ii; i < ii + TS && i < n; i++)
                for (int j = jj; j < jj + TS && j < n; j++)
                    B[(size_t)j * n + i] = A[(size_t)i * n + j];
}

int main(int argc, char *argv[])
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s naive|tiled N\n", argv[0]);
        return 1;
    }
    int n = atoi(argv[2]);
    if (n < 1 || n > 16384) {
        fprintf(stderr, "error: 1 <= N <= 16384\n");
        return 1;
    }
    size_t nn = (size_t)n * n;
    double *A = malloc(nn * sizeof *A), *B = malloc(nn * sizeof *B);
    if (A == NULL || B == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    for (size_t k = 0; k < nn; k++) {
        A[k] = (double)k;
        B[k] = 0.0;                      /* touch every page first */
    }
    int use_tiled = strcmp(argv[1], "tiled") == 0;
    double best = 1e30;
    for (int r = 0; r < 3; r++) {
        double t0 = now_seconds();
        if (use_tiled)
            tiled(A, B, n);
        else
            naive(A, B, n);
        double t = now_seconds() - t0;
        if (t < best)
            best = t;
    }
    for (int i = 0; i < n; i += n / 7 + 1)   /* spot-check the result */
        for (int j = 0; j < n; j += n / 5 + 1)
            if (B[(size_t)j * n + i] != A[(size_t)i * n + j]) {
                fprintf(stderr, "error: wrong result\n");
                return 1;
            }
    printf("%.3f ns per element\n", best / nn * 1e9);
    free(A);
    free(B);
    return 0;
}
