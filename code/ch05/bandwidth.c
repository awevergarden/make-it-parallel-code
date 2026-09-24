/*
 * bandwidth.c -- the triad a[i] = b[i] + q * c[i] at four sizes.
 * Make It Parallel, Chapter 5.
 *
 * Bandwidth is reported the way the STREAM benchmark counts it:
 * 24 bytes per iteration (two 8-byte reads, one 8-byte write).
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o bandwidth bandwidth.c
 * Run:    ./bandwidth      (prints: level,bytes_per_array,GBps)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include "../common/timer.h"

static double triad(long n, int reps)
{
    double *a = malloc(n * sizeof *a), *b = malloc(n * sizeof *b);
    double *c = malloc(n * sizeof *c);
    if (a == NULL || b == NULL || c == NULL) {
        fprintf(stderr, "error: out of memory\n");
        exit(1);
    }
    for (long i = 0; i < n; i++) {
        a[i] = 0.0; b[i] = 1.0; c[i] = 2.0;
    }
    double q = 3.0, best = 1e30;
    for (int trial = 0; trial < 3; trial++) {
        double t0 = now_seconds();
        for (int r = 0; r < reps; r++) {
            for (long i = 0; i < n; i++)
                a[i] = b[i] + q * c[i];
            q += 1e-9 * a[r % n];              /* keep each pass */
        }
        double t = now_seconds() - t0;
        if (t < best)
            best = t;
    }
    free(a); free(b); free(c);
    return 24.0 * n * reps / best / 1e9;
}

int main(void)
{
    const char *level[] = {"L1", "L2", "L3", "memory"};
    long bytes[] = {8192, 262144, 33554432, 268435456};
    printf("level,bytes_per_array,GBps\n");
    for (int k = 0; k < 4; k++) {
        long n = bytes[k] / 8;
        int reps = (int)(3e9 / (24.0 * n)) + 1;
        printf("%s,%ld,%.1f\n", level[k], bytes[k], triad(n, reps));
    }
    return 0;
}
