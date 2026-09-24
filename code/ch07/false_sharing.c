/*
 * false_sharing.c -- per-thread counters, packed versus padded.
 * Make It Parallel, Chapter 7.
 *
 * Each thread increments only its OWN counter. In the packed layout,
 * neighboring threads' counters share a 64-byte cache line; in the
 * padded layout, each counter has a line to itself. On a multicore
 * machine the packed version is typically much slower; on a
 * single-core machine the two run at the same speed.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -pthread \
 *             -o false_sharing false_sharing.c
 * Run:    ./false_sharing THREADS
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdalign.h>
#include <stdio.h>
#include <stdlib.h>
#include "../common/barrier.h"
#include "../common/timer.h"

#define MAX_THREADS 64
#define INCREMENTS 100000000L

static volatile long packed[MAX_THREADS];         /* 8 per line */
static struct {
    alignas(64) volatile long value;              /* 1 per line */
} padded[MAX_THREADS];

struct arg { int id; int use_padded; };

static void *worker(void *p)
{
    const struct arg *a = p;
    volatile long *c = a->use_padded ? &padded[a->id].value
                                     : &packed[a->id];
    for (long k = 0; k < INCREMENTS; k++)
        (*c)++;
    return NULL;
}

int main(int argc, char *argv[])
{
    int p = argc > 1 ? atoi(argv[1]) : 4;
    if (p < 1 || p > MAX_THREADS) {
        fprintf(stderr, "usage: %s THREADS   (1..%d)\n", argv[0], MAX_THREADS);
        return 1;
    }
    for (int layout = 0; layout < 2; layout++) {
        pthread_t tid[MAX_THREADS];
        struct arg args[MAX_THREADS];
        double t0 = now_seconds();
        for (int k = 0; k < p; k++) {
            args[k] = (struct arg){k, layout};
            pt_check(pthread_create(&tid[k], NULL, worker, &args[k]), "create");
        }
        for (int k = 0; k < p; k++)
            pt_check(pthread_join(tid[k], NULL), "join");
        printf("%s,%.3f\n", layout ? "padded" : "packed", now_seconds() - t0);
    }
    return 0;
}
