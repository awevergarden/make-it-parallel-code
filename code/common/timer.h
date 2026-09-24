/*
 * timer.h -- wall-clock timing for Make It Parallel.
 *
 * now_seconds() reads a monotonic clock: it never jumps backward
 * when the system clock is adjusted, so the difference between two
 * readings is a true elapsed time. Every source file that includes
 * this header must first define _POSIX_C_SOURCE (see heatsim_seq.c).
 */
#ifndef TIMER_H
#define TIMER_H

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static inline double now_seconds(void)
{
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        perror("clock_gettime");
        exit(1);
    }
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec;
}

#endif
