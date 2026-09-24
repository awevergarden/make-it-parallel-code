/*
 * costs.c -- what basic thread operations cost, uncontended.
 * Make It Parallel, Chapter 7.
 *
 * Measures, with a single thread doing the work: creating and joining
 * a thread, a mutex lock/unlock pair, an atomic add, and a plain add.
 * With no other thread competing, these are best-case costs.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -pthread -o costs costs.c
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include "../common/barrier.h"
#include "../common/timer.h"

#define CREATES 2000
#define OPS 20000000L

static void *nothing(void *arg)
{
    return arg;
}

int main(void)
{
    double t0 = now_seconds();
    for (int k = 0; k < CREATES; k++) {
        pthread_t tid;
        pt_check(pthread_create(&tid, NULL, nothing, NULL), "create");
        pt_check(pthread_join(tid, NULL), "join");
    }
    printf("create_join_us,%.2f\n", (now_seconds() - t0) / CREATES * 1e6);

    pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;
    volatile long x = 0;
    t0 = now_seconds();
    for (long k = 0; k < OPS; k++) {
        pt_check(pthread_mutex_lock(&m), "lock");
        x++;
        pt_check(pthread_mutex_unlock(&m), "unlock");
    }
    printf("mutex_ns,%.2f\n", (now_seconds() - t0) / OPS * 1e9);

    atomic_long a = 0;
    t0 = now_seconds();
    for (long k = 0; k < OPS; k++)
        atomic_fetch_add(&a, 1);
    printf("atomic_ns,%.2f\n", (now_seconds() - t0) / OPS * 1e9);

    t0 = now_seconds();
    for (long k = 0; k < OPS; k++)
        x++;
    printf("plain_ns,%.2f\n", (now_seconds() - t0) / OPS * 1e9);
    return (x > 0 && atomic_load(&a) > 0) ? 0 : 1;
}
