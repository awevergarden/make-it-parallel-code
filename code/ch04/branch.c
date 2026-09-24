/*
 * branch.c -- the cost of unpredictable branches.
 * Make It Parallel, Chapter 4.
 *
 * Sums the elements of a random array that are at least THRESHOLD.
 * The branch is taken with probability (256 - THRESHOLD) / 256.
 * With "sorted", the array is sorted first, so the branch outcome
 * changes only once and is easy to predict.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o branch branch.c
 * Run:    ./branch THRESHOLD [sorted]   (prints ns per element)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../common/timer.h"

#define N (1 << 20)
#define REPS 50

static int cmp(const void *x, const void *y)
{
    int a = *(const int *)x, b = *(const int *)y;
    return (a > b) - (a < b);
}

static long long conditional_sum(const int *data, int threshold)
{
    long long sum = 0;
    for (int i = 0; i < N; i++)
        if (data[i] >= threshold)
            sum += data[i];
    return sum;
}

int main(int argc, char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s THRESHOLD [sorted]\n", argv[0]);
        return 1;
    }
    int threshold = atoi(argv[1]);
    int *data = malloc(N * sizeof *data);
    if (data == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    srand(12345);                       /* same data every run */
    for (int i = 0; i < N; i++)
        data[i] = rand() % 256;
    if (argc > 2 && strcmp(argv[2], "sorted") == 0)
        qsort(data, N, sizeof *data, cmp);

    long long total = 0;
    double t0 = now_seconds();
    for (int r = 0; r < REPS; r++)
        total += conditional_sum(data, threshold);
    double t = now_seconds() - t0;

    printf("%.4f ns per element (sum %lld)\n",
           t / ((double)N * REPS) * 1e9, total / REPS);
    free(data);
    return 0;
}
