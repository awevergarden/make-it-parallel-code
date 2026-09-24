/*
 * swap.c -- passing values, pointers, and pointers to pointers.
 * Make It Parallel, Chapter 2.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o swap swap.c
 */
#include <stdio.h>

/* Receives copies: swaps the copies, not the caller's variables. */
static void swap_copies(double a, double b)
{
    double tmp = a;
    a = b;
    b = tmp;
}

/* Receives addresses: swaps the caller's variables. */
static void swap_values(double *a, double *b)
{
    double tmp = *a;
    *a = *b;
    *b = tmp;
}

/* Swaps two pointers -- the trick HeatSim uses for cur and next. */
static void swap_ptrs(double **a, double **b)
{
    double *tmp = *a;
    *a = *b;
    *b = tmp;
}

int main(void)
{
    double x = 1.0, y = 2.0;
    swap_copies(x, y);
    printf("after swap_copies: x = %.1f, y = %.1f\n", x, y);
    swap_values(&x, &y);
    printf("after swap_values: x = %.1f, y = %.1f\n", x, y);

    double grid_a[4] = {0.0}, grid_b[4] = {9.0, 9.0, 9.0, 9.0};
    double *cur = grid_a, *next = grid_b;
    swap_ptrs(&cur, &next);
    printf("after swap_ptrs:   cur[0] = %.1f, next[0] = %.1f\n",
           cur[0], next[0]);
    return 0;
}
