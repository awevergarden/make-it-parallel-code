/*
 * timer_res.c -- how fine and how costly is the timer?
 * Make It Parallel, Chapter 3.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o timer_res timer_res.c
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <time.h>
#include "../common/timer.h"

#define CALLS 1000000

int main(void)
{
    struct timespec res;
    if (clock_getres(CLOCK_MONOTONIC, &res) != 0) {
        perror("clock_getres");
        return 1;
    }

    /* Smallest nonzero difference between consecutive readings. */
    double smallest = 1.0;
    for (int k = 0; k < CALLS; k++) {
        double a = now_seconds(), b = now_seconds();
        if (b > a && b - a < smallest)
            smallest = b - a;
    }

    /* Average cost of one reading. */
    double t0 = now_seconds();
    double sink = 0.0;
    for (int k = 0; k < CALLS; k++)
        sink += now_seconds();
    double per_call = (now_seconds() - t0) / CALLS;

    printf("reported resolution: %ld ns\n", res.tv_nsec);
    printf("smallest observed step: %.0f ns\n", smallest * 1e9);
    printf("cost per reading: %.1f ns\n", per_call * 1e9);
    return sink > 0.0 ? 0 : 1;     /* use sink so it is kept */
}
