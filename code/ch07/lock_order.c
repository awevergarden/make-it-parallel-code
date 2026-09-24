/*
 * lock_order.c -- two locks, two threads, two orders.
 * Make It Parallel, Chapter 7.
 *
 * Thread A locks `accounts` then `log`; thread B locks them in the
 * opposite order (mode "opposite") or in the same order (mode
 * "ordered"). A barrier makes both threads hold their first lock
 * before reaching for the second, so the opposite order deadlocks
 * every time. An alarm reports the deadlock after 3 seconds.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -pthread -o lock_order lock_order.c
 * Run:    ./lock_order opposite|ordered
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "../common/barrier.h"

static pthread_mutex_t accounts = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t log_lock = PTHREAD_MUTEX_INITIALIZER;
static barrier_t both_hold_one;
static int ordered;

static void on_alarm(int sig)
{
    (void)sig;
    static const char msg[] = "no progress for 3 s: deadlock\n";
    (void)!write(2, msg, sizeof msg - 1);
    _exit(2);
}

static void *thread_a(void *arg)
{
    (void)arg;
    pt_check(pthread_mutex_lock(&accounts), "lock");
    barrier_wait(&both_hold_one);
    pt_check(pthread_mutex_lock(&log_lock), "lock");
    /* ... update an account and log it ... */
    pt_check(pthread_mutex_unlock(&log_lock), "unlock");
    pt_check(pthread_mutex_unlock(&accounts), "unlock");
    return NULL;
}

static void *thread_b(void *arg)
{
    (void)arg;
    pthread_mutex_t *first = ordered ? &accounts : &log_lock;
    pthread_mutex_t *second = ordered ? &log_lock : &accounts;
    if (ordered) {                      /* same order as thread A */
        barrier_wait(&both_hold_one);
        pt_check(pthread_mutex_lock(first), "lock");
    } else {
        pt_check(pthread_mutex_lock(first), "lock");
        barrier_wait(&both_hold_one);
    }
    pt_check(pthread_mutex_lock(second), "lock");
    pt_check(pthread_mutex_unlock(second), "unlock");
    pt_check(pthread_mutex_unlock(first), "unlock");
    return NULL;
}

int main(int argc, char *argv[])
{
    ordered = argc > 1 && strcmp(argv[1], "ordered") == 0;
    signal(SIGALRM, on_alarm);
    alarm(3);
    barrier_init(&both_hold_one, 2);
    pthread_t a, b;
    pt_check(pthread_create(&a, NULL, thread_a, NULL), "create");
    pt_check(pthread_create(&b, NULL, thread_b, NULL), "create");
    pt_check(pthread_join(a, NULL), "join");
    pt_check(pthread_join(b, NULL), "join");
    printf("%s order: both threads finished\n", ordered ? "same" : "opposite");
    return 0;
}
