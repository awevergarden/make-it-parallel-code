/*
 * pattern.c -- how long a pattern can the branch predictor learn?
 * Make It Parallel, Chapter 4.
 *
 * The branch outcome follows a random sequence of taken/not-taken
 * decisions that repeats every PERIOD elements. Short periods are
 * learned perfectly; once PERIOD exceeds what the predictor can
 * remember, the branch becomes as costly as a random one.
 *
 * Build:  gcc -std=c17 -O2 -fno-if-conversion -fno-if-conversion2 \
 *             -fno-tree-vectorize -Wall -Wextra -o pattern pattern.c
 * Run:    ./pattern PERIOD         (prints ns per element)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include "../common/timer.h"

#define N (1 << 20)
#define REPS 50

static long long conditional_sum(const int *data)
{
    long long sum = 0;
    for (int i = 0; i < N; i++)
        if (data[i] >= 128)
            sum += data[i];
    return sum;
}

int main(int argc, char *argv[])
{
    long period = argc > 1 ? atol(argv[1]) : 16;
    if (period < 1 || period > N) {
        fprintf(stderr, "usage: %s PERIOD (1..%d)\n", argv[0], N);
        return 1;
    }
    int *data = malloc(N * sizeof *data);
    if (data == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    srand(777);
    for (int i = 0; i < period; i++)
        data[i] = (rand() & 1) ? 255 : 0;       /* the random pattern */
    for (int i = period; i < N; i++)
        data[i] = data[i % period];             /* repeated */
    long long total = 0;
    double t0 = now_seconds();
    for (int r = 0; r < REPS; r++)
        total += conditional_sum(data);
    double t = now_seconds() - t0;
    printf("%.4f ns per element (sum %lld)\n", t / ((double)N * REPS) * 1e9,
           total / REPS);
    free(data);
    return 0;
}
