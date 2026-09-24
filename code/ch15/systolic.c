/*
 * systolic.c -- a cycle-by-cycle simulation of a systolic array.
 * Make It Parallel, Chapter 15.
 *
 * An N x N grid of processing elements (PEs) computes C = A * B. Row i
 * of A enters the left edge, delayed by i cycles; column j of B enters
 * the top edge, delayed by j cycles. Each cycle, every PE multiplies
 * the pair of values it holds, adds the product to its own element of
 * C, and passes A right and B down. Each value is read from memory once
 * and used by N PEs. Irregular integer data makes the check exact.
 *
 * Mode ws ("weight-stationary", as in Google's first TPU) instead keeps
 * B in the PEs and streams the M rows of a tall matrix A through them;
 * partial sums flow down and rows of C leave the bottom edge.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o systolic systolic.c
 * Run:    ./systolic os N        or        ./systolic ws N M
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static double a_val(long i, long j) { return (double)((i * 31 + j * 17 + (i * j) % 13) % 11 - 5); }
static double b_val(long i, long j) { return (double)((i * 19 + j * 23 + (i * j) % 7) % 9 - 4); }

/* Weight-stationary: PE (k, j) holds B[k][j]; row r of A enters row k at
   cycle r + k; C[r][j] leaves the bottom of column j at cycle r + n-1 + j. */
static int weight_stationary(int n, int m)
{
    size_t nn = (size_t)n * n;
    double *w = malloc(nn * sizeof *w), *a = calloc(nn, sizeof *a);
    double *ps = calloc(nn, sizeof *ps), *a2 = calloc(nn, sizeof *a2);
    double *ps2 = calloc(nn, sizeof *ps2), *c = calloc((size_t)m * n, sizeof *c);
    if (!w || !a || !ps || !a2 || !ps2 || !c)
        return 1;
    for (int k = 0; k < n; k++)
        for (int j = 0; j < n; j++)
            w[k * n + j] = b_val(k, j);
    long cycles = 0;
    for (int t = 0; t < m + 2 * n - 2; t++) {
        for (int k = 0; k < n; k++)
            for (int j = 0; j < n; j++) {
                int r = t - k;
                a2[k * n + j] = j > 0 ? a[k * n + j - 1]
                              : (r >= 0 && r < m ? a_val(r, k) : 0.0);
                ps2[k * n + j] = (k > 0 ? ps[(k - 1) * n + j] : 0.0)
                               + a2[k * n + j] * w[k * n + j];
            }
        memcpy(a, a2, nn * sizeof *a);
        memcpy(ps, ps2, nn * sizeof *ps);
        for (int j = 0; j < n; j++) {               /* results leaving the bottom */
            int r = t - (n - 1) - j;
            if (r >= 0 && r < m)
                c[(size_t)r * n + j] = ps[(n - 1) * n + j];
        }
        cycles++;
    }
    long wrong = 0;
    for (int r = 0; r < m; r++)
        for (int j = 0; j < n; j++) {
            double s = 0.0;
            for (int k = 0; k < n; k++)
                s += a_val(r, k) * b_val(k, j);
            wrong += c[(size_t)r * n + j] != s;
        }
    printf("mode,ws\nn,%d\nm,%d\ncycles,%ld\nwrong,%ld\nutilization,%.3f\n", n, m,
           cycles, wrong, (double)m * n * n / ((double)nn * cycles));
    free(w); free(a); free(ps); free(a2); free(ps2); free(c);
    return wrong ? 1 : 0;
}

int main(int argc, char *argv[])
{
    if (argc > 1 && strcmp(argv[1], "ws") == 0) {
        int n = argc > 2 ? atoi(argv[2]) : 16, m = argc > 3 ? atoi(argv[3]) : 1000;
        if (n < 1 || m < 1)
            return 1;
        return weight_stationary(n, m);
    }
    int n = argc > 2 ? atoi(argv[2]) : 16;
    if (n < 1 || n > 1024) {
        fprintf(stderr, "usage: %s os N | ws N M\n", argv[0]);
        return 1;
    }
    size_t nn = (size_t)n * n;
    double *a_reg = calloc(nn, sizeof *a_reg), *b_reg = calloc(nn, sizeof *b_reg);
    double *a_new = calloc(nn, sizeof *a_new), *b_new = calloc(nn, sizeof *b_new);
    double *c = calloc(nn, sizeof *c);
    if (!a_reg || !b_reg || !a_new || !b_new || !c)
        return 1;
    long macs = 0, cycles = 0;
    for (int t = 0; t < 3 * n - 2; t++) {          /* the last product lands at 3n-3 */
        for (int i = 0; i < n; i++)                 /* values move one PE per cycle */
            for (int j = 0; j < n; j++) {
                /* A from the left neighbor, or from the edge: row i, element t-i */
                int k = t - i;
                a_new[i * n + j] = j > 0 ? a_reg[i * n + j - 1]
                                 : (k >= 0 && k < n ? a_val(i, k) : 0.0);
                k = t - j;                          /* B: column j, element t-j */
                b_new[i * n + j] = i > 0 ? b_reg[(i - 1) * n + j]
                                 : (k >= 0 && k < n ? b_val(k, j) : 0.0);
            }
        for (size_t p = 0; p < nn; p++) {            /* every PE: one multiply-add */
            a_reg[p] = a_new[p];
            b_reg[p] = b_new[p];
            if (a_reg[p] != 0.0 || b_reg[p] != 0.0)
                macs++;
            c[p] += a_reg[p] * b_reg[p];
        }
        cycles++;
    }
    long wrong = 0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            double s = 0.0;
            for (int k = 0; k < n; k++)
                s += a_val(i, k) * b_val(k, j);
            wrong += c[(size_t)i * n + j] != s;
        }
    long useful = (long)n * n * n;
    printf("mode,os\nn,%d\ncycles,%ld\nwrong,%ld\nuseful_macs,%ld\npe_cycles,%ld\nutilization,%.3f\n",
           n, cycles, wrong, useful, (long)nn * cycles, (double)useful / ((double)nn * cycles));
    (void)macs;
    free(a_reg); free(b_reg); free(a_new); free(b_new); free(c);
    return wrong ? 1 : 0;
}
