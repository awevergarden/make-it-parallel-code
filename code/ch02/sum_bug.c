/*
 * sum_bug.c -- Bug Hunt program for Chapter 2 (contains a bug!).
 * Make It Parallel, Chapter 2.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o sum_bug sum_bug.c
 * Check:  gcc -std=c17 -O1 -g -fsanitize=address \
 *             -o sum_bug_asan sum_bug.c && ./sum_bug_asan
 */
#include <stdio.h>
#include <stdlib.h>

/* Average temperature of one row of the plate. */
static double row_average(const double *row, int n)
{
    double sum = 0.0;
    for (int j = 0; j <= n; j++)
        sum += row[j];
    return sum / n;
}

int main(void)
{
    int n = 8;
    double *row = malloc((size_t)n * sizeof *row);
    if (row == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    for (int j = 0; j < n; j++)
        row[j] = 100.0;

    printf("average = %.2f\n", row_average(row, n));
    free(row);
    return 0;
}
