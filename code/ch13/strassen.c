/*
 * strassen.c -- Strassen's algorithm versus the ordinary product.
 * Make It Parallel, Chapter 13.
 *
 * Multiplies two N x N matrices (N a power of two) of random values in
 * [-1, 1) with the ikj loop and with Strassen's recursion, which uses
 * 7 half-size products instead of 8 and switches to the ikj loop below
 * CUTOFF. Reports both times and the largest difference between them.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp-simd -Wall -Wextra -o strassen strassen.c -lm
 * Run:    ./strassen N [CUTOFF]
 */
#define _POSIX_C_SOURCE 200809L
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../common/timer.h"

static int cutoff = 128;

/* C = A * B for n x n blocks with row strides la, lb, lc (C zeroed first). */
static void ikj(const double *A, int la, const double *B, int lb,
                double *C, int lc, int n)
{
    for (int i = 0; i < n; i++) {
        memset(&C[(size_t)i * lc], 0, n * sizeof *C);
        for (int k = 0; k < n; k++) {
            double a = A[(size_t)i * la + k];
            const double *restrict b = &B[(size_t)k * lb];
            double *restrict c = &C[(size_t)i * lc];
            #pragma omp simd
            for (int j = 0; j < n; j++)
                c[j] += a * b[j];
        }
    }
}

/* Z = X + s*Y on h x h blocks (Z is contiguous with stride h). */
static void addsub(const double *X, int lx, const double *Y, int ly,
                   double s, double *Z, int h)
{
    for (int i = 0; i < h; i++)
        for (int j = 0; j < h; j++)
            Z[(size_t)i * h + j] = X[(size_t)i * lx + j] + s * Y[(size_t)i * ly + j];
}

static double *scratch(size_t count)
{
    double *x = malloc(count * sizeof *x);
    if (x == NULL) {
        fprintf(stderr, "error: out of memory\n");
        exit(1);
    }
    return x;
}

static void strassen(const double *A, int la, const double *B, int lb,
                     double *C, int lc, int n)
{
    if (n <= cutoff) {
        ikj(A, la, B, lb, C, lc, n);
        return;
    }
    int h = n / 2;
    size_t hh = (size_t)h * h;
    const double *A11 = A, *A12 = A + h, *A21 = A + (size_t)h * la, *A22 = A21 + h;
    const double *B11 = B, *B12 = B + h, *B21 = B + (size_t)h * lb, *B22 = B21 + h;
    double *T1 = scratch(hh), *T2 = scratch(hh), *M[7];
    for (int k = 0; k < 7; k++)
        M[k] = scratch(hh);
    addsub(A11, la, A22, la, 1, T1, h); addsub(B11, lb, B22, lb, 1, T2, h);
    strassen(T1, h, T2, h, M[0], h, h);              /* M1 = (A11+A22)(B11+B22) */
    addsub(A21, la, A22, la, 1, T1, h);
    strassen(T1, h, B11, lb, M[1], h, h);            /* M2 = (A21+A22)B11 */
    addsub(B12, lb, B22, lb, -1, T2, h);
    strassen(A11, la, T2, h, M[2], h, h);            /* M3 = A11(B12-B22) */
    addsub(B21, lb, B11, lb, -1, T2, h);
    strassen(A22, la, T2, h, M[3], h, h);            /* M4 = A22(B21-B11) */
    addsub(A11, la, A12, la, 1, T1, h);
    strassen(T1, h, B22, lb, M[4], h, h);            /* M5 = (A11+A12)B22 */
    addsub(A21, la, A11, la, -1, T1, h); addsub(B11, lb, B12, lb, 1, T2, h);
    strassen(T1, h, T2, h, M[5], h, h);              /* M6 = (A21-A11)(B11+B12) */
    addsub(A12, la, A22, la, -1, T1, h); addsub(B21, lb, B22, lb, 1, T2, h);
    strassen(T1, h, T2, h, M[6], h, h);              /* M7 = (A12-A22)(B21+B22) */
    for (int i = 0; i < h; i++)
        for (int j = 0; j < h; j++) {
            size_t k = (size_t)i * h + j;
            C[(size_t)i * lc + j] = M[0][k] + M[3][k] - M[4][k] + M[6][k];
            C[(size_t)i * lc + j + h] = M[2][k] + M[4][k];
            C[(size_t)(i + h) * lc + j] = M[1][k] + M[3][k];
            C[(size_t)(i + h) * lc + j + h] = M[0][k] - M[1][k] + M[2][k] + M[5][k];
        }
    free(T1); free(T2);
    for (int k = 0; k < 7; k++)
        free(M[k]);
}

int main(int argc, char *argv[])
{
    int n = argc > 1 ? atoi(argv[1]) : 1024;
    if (argc > 2)
        cutoff = atoi(argv[2]);
    if (n < 2 || (n & (n - 1)) || cutoff < 1) {
        fprintf(stderr, "usage: %s N [CUTOFF]   (N a power of two)\n", argv[0]);
        return 1;
    }
    size_t nn = (size_t)n * n;
    double *A = scratch(nn), *B = scratch(nn), *C1 = scratch(nn), *C2 = scratch(nn);
    srand(12345);
    for (size_t k = 0; k < nn; k++) {
        A[k] = 2.0 * rand() / ((double)RAND_MAX + 1) - 1.0;
        B[k] = 2.0 * rand() / ((double)RAND_MAX + 1) - 1.0;
    }
    double t0 = now_seconds();
    ikj(A, n, B, n, C1, n, n);
    double t1 = now_seconds();
    strassen(A, n, B, n, C2, n, n);
    double t2 = now_seconds();
    double diff = 0.0, big = 0.0;
    for (size_t k = 0; k < nn; k++) {
        diff = fmax(diff, fabs(C1[k] - C2[k]));
        big = fmax(big, fabs(C1[k]));
    }
    printf("n,%d\ncutoff,%d\nikj_s,%.3f\nstrassen_s,%.3f\nmax_diff,%.3g\nmax_entry,%.3g\n",
           n, cutoff, t1 - t0, t2 - t1, diff, big);
    free(A); free(B); free(C1); free(C2);
    return 0;
}
