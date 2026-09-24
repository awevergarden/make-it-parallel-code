/*
 * peak.c -- a compute ceiling: arithmetic on registers only.
 * Make It Parallel, Chapter 5.
 *
 * 24 independent chains of x = x * m + d, with no memory traffic in
 * the loop. Reports billions of floating-point operations per second.
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o peak peak.c
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include "../common/timer.h"

#define CHAINS 24
#define ROUNDS 20000000L

int main(void)
{
    double x[CHAINS];
    for (int k = 0; k < CHAINS; k++)
        x[k] = 1.0 + k * 1e-3;
    double m = 0.999999, d = 1e-6;
    double t0 = now_seconds();
    for (long r = 0; r < ROUNDS; r++)
        for (int k = 0; k < CHAINS; k++)
            x[k] = x[k] * m + d;
    double t = now_seconds() - t0;
    double sum = 0.0;
    for (int k = 0; k < CHAINS; k++)
        sum += x[k];
    printf("GFLOPs,%.2f\ncheck,%.6f\n", 2.0 * CHAINS * ROUNDS / t / 1e9, sum);
    return 0;
}
