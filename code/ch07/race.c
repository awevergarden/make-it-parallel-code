/*
 * race.c -- several threads increment one shared counter.
 * Make It Parallel, Chapter 7.
 *
 * MODE plain   counter++ with no protection (a data race!)
 * MODE atomic  atomic_fetch_add from <stdatomic.h>
 * MODE mutex   counter++ inside a pthread mutex
 * "volatile" makes the compiler load and store the plain counter on
 * every iteration, as a loop with real work in it would; it does NOT
 * make the increment atomic.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -pthread -o race race.c
 * Run:    ./race MODE THREADS INCREMENTS_PER_THREAD
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../common/barrier.h"
#include "../common/timer.h"

#define MAX_THREADS 64

static volatile long plain_counter = 0;
static atomic_long atomic_counter = 0;
static long mutex_counter = 0;
static pthread_mutex_t counter_lock = PTHREAD_MUTEX_INITIALIZER;
static long increments;
static int mode;                 /* 0 plain, 1 atomic, 2 mutex */

static void *worker(void *arg)
{
    (void)arg;
    for (long k = 0; k < increments; k++) {
        if (mode == 0) {
            plain_counter++;                       /* racy */
        } else if (mode == 1) {
            atomic_fetch_add(&atomic_counter, 1);
        } else {
            pt_check(pthread_mutex_lock(&counter_lock), "lock");
            mutex_counter++;
            pt_check(pthread_mutex_unlock(&counter_lock), "unlock");
        }
    }
    return NULL;
}

int main(int argc, char *argv[])
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s plain|atomic|mutex THREADS INCREMENTS\n",
                argv[0]);
        return 1;
    }
    mode = strcmp(argv[1], "plain") == 0 ? 0
         : strcmp(argv[1], "atomic") == 0 ? 1 : 2;
    int p = atoi(argv[2]);
    increments = atol(argv[3]);
    if (p < 1 || p > MAX_THREADS || increments < 1) {
        fprintf(stderr, "error: need 1 <= THREADS <= %d, INCREMENTS >= 1\n",
                MAX_THREADS);
        return 1;
    }
    pthread_t tid[MAX_THREADS];
    double t0 = now_seconds();
    for (int k = 0; k < p; k++)
        pt_check(pthread_create(&tid[k], NULL, worker, NULL), "create");
    for (int k = 0; k < p; k++)
        pt_check(pthread_join(tid[k], NULL), "join");
    double t = now_seconds() - t0;
    long got = mode == 0 ? plain_counter
             : mode == 1 ? atomic_load(&atomic_counter) : mutex_counter;
    printf("%s: expected %ld, got %ld (%.2f ns per increment)\n", argv[1],
           (long)p * increments, got, t / ((double)p * increments) * 1e9);
    return 0;
}
