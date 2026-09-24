/*
 * matmul_omp.c -- matrix multiplication with OpenMP.
 * Make It Parallel, Chapter 8.
 *
 * Both versions divide the rows of C among the threads and vectorize
 * the inner loop. Each C[i][j] still adds its terms in the order
 * k = 0, 1, 2, ..., so both give bit-identical results for any number
 * of threads.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp -Wall -Wextra -o matmul_omp matmul_omp.c
 * Run:    OMP_NUM_THREADS=4 ./matmul_omp ikj|tiled N
 */
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BS 64

static int min(int a, int b)
{
    return a < b ? a : b;
}

static void mm_ikj(const double *restrict A, const double *restrict B,
                   double *restrict C, int n)
{
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < n; i++)
        for (int k = 0; k < n; k++) {
            double a = A[i * n + k];
            #pragma omp simd
            for (int j = 0; j < n; j++)
                C[i * n + j] += a * B[k * n + j];
        }
}

static void mm_tiled(const double *restrict A, const double *restrict B,
                     double *restrict C, int n)
{
    #pragma omp parallel for schedule(static)
    for (int ii = 0; ii < n; ii += BS)
        for (int kk = 0; kk < n; kk += BS)
            for (int jj = 0; jj < n; jj += BS) {
                int imax = min(ii + BS, n), kmax = min(kk + BS, n);
                int jmax = min(jj + BS, n);
                for (int i = ii; i < imax; i++)
                    for (int k = kk; k < kmax; k++) {
                        double a = A[i * n + k];
                        #pragma omp simd
                        for (int j = jj; j < jmax; j++)
                            C[i * n + j] += a * B[k * n + j];
                    }
            }
}

int main(int argc, char *argv[])
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s ikj|tiled N\n", argv[0]);
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
    for (size_t k = 0; k < nn; k++) {        /* same data as Chapter 5 */
        A[k] = (double)(k % 7) - 3.0;
        B[k] = (double)(k % 5) * 0.5;
    }
    double t0 = omp_get_wtime();
    if (strcmp(argv[1], "ikj") == 0)
        mm_ikj(A, B, C, n);
    else
        mm_tiled(A, B, C, n);
    double t = omp_get_wtime() - t0;
    double check = 0.0;
    for (size_t k = 0; k < nn; k++)
        check += C[k] * (double)(k % 3 + 1);
    printf("GFLOPs,%.3f\nchecksum,%.6f\n", 2.0 * n * n * (double)n / t / 1e9,
           check);
    free(A); free(B); free(C);
    return 0;
}
