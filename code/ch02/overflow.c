/*
 * overflow.c -- counting the cells of an n x n grid.
 * Make It Parallel, Chapter 2.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o overflow overflow.c
 * Check:  gcc -std=c17 -O1 -g -fsanitize=undefined \
 *             -o overflow_ub overflow.c && ./overflow_ub 50000
 */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    int n = argc > 1 ? atoi(argv[1]) : 50000;

    int bad = n * n;              /* overflows for n > 46340 */
    size_t good = (size_t)n * n;  /* converts before multiplying */

    printf("n = %d\n", n);
    printf("int    n * n = %d\n", bad);
    printf("size_t n * n = %zu\n", good);
    return 0;
}
