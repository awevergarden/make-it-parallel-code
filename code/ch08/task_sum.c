/*
 * task_sum.c -- a recursive sum with OpenMP tasks.
 * Make It Parallel, Chapter 8.
 *
 * Splits the array in half recursively; each half becomes a task
 * that any idle thread may run. Below CUTOFF elements, it sums
 * sequentially, because a task costs far more than a few additions.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp -Wall -Wextra -o task_sum task_sum.c
 */
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

#define N 10000000L
#define CUTOFF 100000L

static double tsum(const double *x, long lo, long hi)
{
    if (hi - lo <= CUTOFF) {
        double s = 0.0;
        for (long i = lo; i < hi; i++)
            s += x[i];
        return s;
    }
    long mid = lo + (hi - lo) / 2;
    double left, right;
    #pragma omp task shared(left)
    left = tsum(x, lo, mid);
    #pragma omp task shared(right)
    right = tsum(x, mid, hi);
    #pragma omp taskwait
    return left + right;
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
    double s = 0.0;
    #pragma omp parallel
    #pragma omp single
    s = tsum(x, 0, N);
    printf("threads,%d\ntask_sum,%.17g\n", omp_get_max_threads(), s);
    free(x);
    return 0;
}
