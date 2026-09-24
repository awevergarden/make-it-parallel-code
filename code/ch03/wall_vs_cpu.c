/*
 * wall_vs_cpu.c -- wall-clock time versus CPU time.
 * Make It Parallel, Chapter 3.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o wall_vs_cpu wall_vs_cpu.c
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <time.h>
#include "../common/timer.h"

static void report(const char *what, double w0, clock_t c0)
{
    double wall = now_seconds() - w0;
    double cpu = (double)(clock() - c0) / CLOCKS_PER_SEC;
    printf("%-10s wall %.3f s   cpu %.3f s\n", what, wall, cpu);
}

int main(void)
{
    /* 1: sleep for one second -- the CPU does nothing. */
    double w0 = now_seconds();
    clock_t c0 = clock();
    struct timespec one = {1, 0};
    if (nanosleep(&one, NULL) != 0) {
        perror("nanosleep");
        return 1;
    }
    report("sleeping", w0, c0);

    /* 2: keep the CPU busy for about one second. */
    w0 = now_seconds();
    c0 = clock();
    volatile double x = 0.0;
    while (now_seconds() - w0 < 1.0)
        x += 1.0;
    report("computing", w0, c0);
    return 0;
}
