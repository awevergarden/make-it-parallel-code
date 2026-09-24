/*
 * reduce_omp.c -- a parallel sum, two ways.
 * Make It Parallel, Chapter 8.
 *
 * sum_reduction() uses "reduction(+:s)": each thread sums its share,
 * and OpenMP combines the partial sums. The result can change in the
 * last digits with the number of threads. sum_reproducible() always
 * splits the array into the same CHUNKS pieces and adds the pieces'
 * sums in a fixed order, so its result never depends on the number
 * of threads.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp -Wall -Wextra -o reduce_omp reduce_omp.c
 * Run:    OMP_NUM_THREADS=4 ./reduce_omp
 */
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

#define N 10000000L
#define CHUNKS 64

static double sum_reduction(const double *x, long n)
{
    double s = 0.0;
    #pragma omp parallel for reduction(+:s) schedule(static)
    for (long i = 0; i < n; i++)
        s += x[i];
    return s;
}

static double sum_reproducible(const double *x, long n)
{
    double part[CHUNKS];
    #pragma omp parallel for schedule(static)
    for (int c = 0; c < CHUNKS; c++) {
        double s = 0.0;
        for (long i = c * n / CHUNKS; i < (c + 1) * n / CHUNKS; i++)
            s += x[i];
        part[c] = s;
    }
    double s = 0.0;
    for (int c = 0; c < CHUNKS; c++)       /* fixed order */
        s += part[c];
    return s;
}

int main(void)
{
    double *x = malloc(N * sizeof *x);
    if (x == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    for (long i = 0; i < N; i++)
        x[i] = 1.0 / (double)(i + 1);
    double seq = 0.0;
    for (long i = 0; i < N; i++)
        seq += x[i];
    printf("threads,%d\nsequential,%.17g\nreduction,%.17g\nreproducible,%.17g\n",
           omp_get_max_threads(), seq, sum_reduction(x, N),
           sum_reproducible(x, N));
    free(x);
    return 0;
}
