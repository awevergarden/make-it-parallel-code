/*
 * matmul.c -- C = A * B three ways: ijk, ikj, and tiled.
 * Make It Parallel, Chapter 5.
 *
 * All three add each C[i][j]'s terms in the same order (k = 0, 1,
 * 2, ...), so they produce bit-identical results.
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o matmul matmul.c
 * Run:    ./matmul VARIANT N    (VARIANT: ijk, ikj, tiled)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../common/timer.h"

#define BS 64                  /* tile size */

static void mm_ijk(const double *A, const double *B, double *C, int n)
{
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            double sum = 0.0;
            for (int k = 0; k < n; k++)
                sum += A[i * n + k] * B[k * n + j];
            C[i * n + j] = sum;
        }
}

static void mm_ikj(const double *A, const double *B, double *C, int n)
{
    for (int i = 0; i < n; i++)
        for (int k = 0; k < n; k++) {
            double a = A[i * n + k];
            for (int j = 0; j < n; j++)
                C[i * n + j] += a * B[k * n + j];
        }
}

static int min(int a, int b)
{
    return a < b ? a : b;
}

/* Work on BS x BS tiles so that a tile of B is reused for BS rows
   of C while it is still in the cache. The loop bounds are computed
   once per tile, which keeps the inner loop simple to vectorize. */
static void mm_tiled(const double *A, const double *B, double *C, int n)
{
    for (int ii = 0; ii < n; ii += BS)
        for (int kk = 0; kk < n; kk += BS)
            for (int jj = 0; jj < n; jj += BS) {
                int imax = min(ii + BS, n), kmax = min(kk + BS, n);
                int jmax = min(jj + BS, n);
                for (int i = ii; i < imax; i++)
                    for (int k = kk; k < kmax; k++) {
                        double a = A[i * n + k];
                        for (int j = jj; j < jmax; j++)
                            C[i * n + j] += a * B[k * n + j];
                    }
            }
}

int main(int argc, char *argv[])
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s ijk|ikj|tiled N\n", argv[0]);
        return 1;
    }
    int n = atoi(argv[2]);
    if (n < 1 || n > 8192) {
        fprintf(stderr, "error: 1 <= N <= 8192\n");
        return 1;
    }
    size_t nn = (size_t)n * n;
    double *A = malloc(nn * sizeof *A), *B = malloc(nn * sizeof *B);
    double *C = calloc(nn, sizeof *C);
    if (A == NULL || B == NULL || C == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    for (size_t k = 0; k < nn; k++) {
        A[k] = (double)(k % 7) - 3.0;
        B[k] = (double)(k % 5) * 0.5;
    }
    double t0 = now_seconds();
    if (strcmp(argv[1], "ijk") == 0)
        mm_ijk(A, B, C, n);
    else if (strcmp(argv[1], "ikj") == 0)
        mm_ikj(A, B, C, n);
    else
        mm_tiled(A, B, C, n);
    double t = now_seconds() - t0;
    double check = 0.0;
    for (size_t k = 0; k < nn; k++)
        check += C[k] * (double)(k % 3 + 1);
    printf("GFLOPs,%.3f\nchecksum,%.6f\n", 2.0 * n * n * (double)n / t / 1e9,
           check);
    free(A); free(B); free(C);
    return 0;
}
