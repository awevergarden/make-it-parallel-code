/*
 * sum_bug.c -- Bug Hunt program for Chapter 8 (contains a bug!).
 * Make It Parallel, Chapter 8.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp -Wall -Wextra -o sum_bug sum_bug.c
 * Run:    OMP_NUM_THREADS=4 ./sum_bug
 */
#include <omp.h>
#include <stdio.h>

#define N 100000000L

int main(void)
{
    long count = 0;
    #pragma omp parallel for
    for (long i = 0; i < N; i++)
        if (i % 3 == 0)
            count++;
    printf("multiples of 3 below %ld: %ld (expected %ld)\n",
           N, count, (N + 2) / 3);
    return 0;
}
