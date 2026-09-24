/*
 * conflict.c -- conflict misses from a power-of-two row length.
 * Make It Parallel, Chapter 5.
 *
 * Sums a ROWS x COLS block of a matrix column by column, where each
 * row of the matrix is WIDTH doubles long. With WIDTH = 4096 (32 KB,
 * a power of two), every element of a column maps to the same few
 * cache sets; padding the rows to 4104 spreads them out.
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o conflict conflict.c
 * Run:    ./conflict WIDTH            (prints ns per element)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include "../common/timer.h"

#define ROWS 256
#define COLS 4096
#define REPS 20

int main(int argc, char *argv[])
{
    long width = argc > 1 ? atol(argv[1]) : 4096;
    if (width < COLS) {
        fprintf(stderr, "error: WIDTH must be at least %d\n", COLS);
        return 1;
    }
    double *a = malloc((size_t)ROWS * width * sizeof *a);
    if (a == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    for (size_t k = 0; k < (size_t)ROWS * width; k++)
        a[k] = 1.0;
    double sum = 0.0, best = 1e30;
    for (int r = 0; r < REPS; r++) {
        double t0 = now_seconds();
        for (int j = 0; j < COLS; j++)          /* column by column */
            for (int i = 0; i < ROWS; i++)
                sum += a[(size_t)i * width + j];
        double t = now_seconds() - t0;
        if (t < best)
            best = t;
    }
    printf("%.3f ns per element (sum %.0f)\n",
           best / ((double)ROWS * COLS) * 1e9, sum);
    free(a);
    return 0;
}
