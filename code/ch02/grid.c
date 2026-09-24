/*
 * grid.c -- a two-dimensional grid stored in one block of memory.
 * Make It Parallel, Chapter 2.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o grid grid.c
 * Run:    ./grid 4
 */
#include <stdio.h>
#include <stdlib.h>

/* Row-major position of cell (i, j) in an n x n grid. */
static inline size_t idx(int i, int j, int n)
{
    return (size_t)i * n + j;
}

/* Allocate an n x n grid of zeros; returns NULL on failure. */
static double *alloc_grid(int n)
{
    return calloc((size_t)n * n, sizeof(double));
}

int main(int argc, char *argv[])
{
    int n = argc > 1 ? atoi(argv[1]) : 4;
    if (n < 3 || n > 12) {
        fprintf(stderr, "usage: %s N   (3 <= N <= 12)\n", argv[0]);
        return 1;
    }
    double *grid = alloc_grid(n);
    if (grid == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }

    /* Store each cell's own index so the layout is visible. */
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            grid[idx(i, j, n)] = (double)idx(i, j, n);

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++)
            printf("%4.0f", grid[idx(i, j, n)]);
        printf("\n");
    }

    int i = 1, j = 2;
    size_t k = idx(i, j, n);
    printf("cell (%d,%d) is element %zu; neighbors: "
           "up %zu, down %zu, left %zu, right %zu\n",
           i, j, k, k - n, k + n, k - 1, k + 1);
    printf("address step: right %td bytes, down %td bytes\n",
           (char *)&grid[k + 1] - (char *)&grid[k],
           (char *)&grid[k + n] - (char *)&grid[k]);

    free(grid);
    return 0;
}
