/*
 * parse_args.c -- checked conversion of command-line arguments.
 * Make It Parallel, Chapter 2.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o parse_args parse_args.c
 * Run:    ./parse_args 128 20000
 */
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

/* Convert text to an int in [lo, hi]. Returns 0 on success. */
static int parse_int(const char *text, int lo, int hi, int *out)
{
    char *end;
    errno = 0;
    long v = strtol(text, &end, 10);
    if (end == text || *end != '\0')
        return -1;                     /* not a whole number */
    if (errno == ERANGE || v < lo || v > hi)
        return -1;                     /* out of range */
    *out = (int)v;
    return 0;
}

int main(int argc, char *argv[])
{
    int n, steps;
    if (argc != 3
        || parse_int(argv[1], 3, 100000, &n) != 0
        || parse_int(argv[2], 0, INT_MAX, &steps) != 0) {
        fprintf(stderr, "usage: %s N STEPS\n", argv[0]);
        return 1;
    }
    printf("grid %d x %d, %d steps\n", n, n, steps);
    return 0;
}
