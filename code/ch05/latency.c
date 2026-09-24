/*
 * latency.c -- memory latency versus working-set size (pointer chasing).
 * Make It Parallel, Chapter 5.
 *
 * Builds a random cycle through one slot per 64-byte cache line and
 * follows it. Each load needs the previous load's result, so the time
 * per load is the latency of wherever the data lives.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o latency latency.c
 * Run:    ./latency            (prints: bytes,ns_per_load)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "../common/timer.h"

#define STEP 8                 /* 8 size_t = one 64-byte line */
#define LOADS 4000000L

static uint64_t rng = 88172645463325252ULL;
static uint64_t next_random(void)          /* xorshift64 */
{
    rng ^= rng << 13;
    rng ^= rng >> 7;
    rng ^= rng << 17;
    return rng;
}

int main(void)
{
    printf("bytes,ns_per_load\n");
    for (size_t bytes = 4096; bytes <= (1UL << 30); bytes *= 2) {
        size_t slots = bytes / 64;
        size_t *a = malloc(bytes);
        size_t *order = malloc(slots * sizeof *order);
        if (a == NULL || order == NULL) {
            fprintf(stderr, "error: out of memory\n");
            return 1;
        }
        for (size_t k = 0; k < slots; k++)
            order[k] = k;
        for (size_t k = slots - 1; k > 0; k--) {    /* Sattolo */
            size_t r = next_random() % k;
            size_t t = order[k]; order[k] = order[r]; order[r] = t;
        }
        for (size_t k = 0; k < slots; k++)          /* one cycle */
            a[order[k] * STEP] = order[(k + 1) % slots] * STEP;

        size_t p = 0;
        for (long k = 0; k < LOADS / 4; k++)        /* warm up */
            p = a[p];
        double t0 = now_seconds();
        for (long k = 0; k < LOADS; k++)
            p = a[p];
        double t = now_seconds() - t0;
        printf("%zu,%.3f\n", bytes, t / LOADS * 1e9 + (p == 1 ? 1e-9 : 0));
        free(a);
        free(order);
    }
    return 0;
}
