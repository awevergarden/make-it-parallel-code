/*
 * emulate_matmul.c -- run matmul_gpu.cu's kernel on the CPU and check it
 * exactly. Make It Parallel, Chapter 14.
 *
 * Replays every block and thread with the shared per-thread functions in
 * matmul_tile.h; barriers become the boundaries between phases. The
 * matrices hold irregular small integers (Chapter 13), so the product
 * must match exactly.
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o emulate_matmul emulate_matmul.c
 * Run:    ./emulate_matmul N
 */
#include <stdio.h>
#include <stdlib.h>
#include "../heatsim/matmul_tile.h"

static double a_val(long i, long j) { return (double)((i * 31 + j * 17 + (i * j) % 13) % 11 - 5); }
static double b_val(long i, long j) { return (double)((i * 19 + j * 23 + (i * j) % 7) % 9 - 4); }

int main(int argc, char *argv[])
{
    int n = argc > 1 ? atoi(argv[1]) : 100;
    if (n < 1) {
        fprintf(stderr, "usage: %s N\n", argv[0]);
        return 1;
    }
    double *A = malloc((size_t)n * n * sizeof *A), *B = malloc((size_t)n * n * sizeof *B);
    double *C = calloc((size_t)n * n, sizeof *C);
    if (A == NULL || B == NULL || C == NULL)
        return 1;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            A[i * n + j] = a_val(i, j);
            B[i * n + j] = b_val(i, j);
        }
    int g = (n + T - 1) / T;
    double As[T * T], Bs[T * T], acc[T * T];
    for (int by = 0; by < g; by++)
        for (int bx = 0; bx < g; bx++) {
            for (int k = 0; k < T * T; k++)
                acc[k] = 0.0;
            for (int t = 0; t < g; t++) {
                for (int ty = 0; ty < T; ty++)
                    for (int tx = 0; tx < T; tx++)
                        mm_load(A, B, As, Bs, n, t, bx, by, tx, ty);
                /* __syncthreads() */
                for (int ty = 0; ty < T; ty++)
                    for (int tx = 0; tx < T; tx++)
                        acc[ty * T + tx] = mm_partial(As, Bs, tx, ty, acc[ty * T + tx]);
                /* __syncthreads() */
            }
            for (int ty = 0; ty < T; ty++)
                for (int tx = 0; tx < T; tx++) {
                    int row = by * T + ty, col = bx * T + tx;
                    if (row < n && col < n)
                        C[row * n + col] = acc[ty * T + tx];
                }
        }
    long wrong = 0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            double s = 0.0;
            for (int k = 0; k < n; k++)
                s += a_val(i, k) * b_val(k, j);
            wrong += C[i * n + j] != s;
        }
    printf("n %d: %ld wrong of %ld\n", n, wrong, (long)n * n);
    free(A); free(B); free(C);
    return wrong ? 1 : 0;
}
