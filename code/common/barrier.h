/*
 * barrier.h -- a reusable thread barrier built from a mutex and a
 * condition variable. Make It Parallel, Chapter 7.
 *
 * POSIX defines pthread_barrier_t, but some systems (macOS among
 * them) don't provide it, so the book uses this portable version.
 * Every thread that calls barrier_wait() blocks until COUNT threads
 * have arrived; then all are released and the barrier resets.
 * Include after defining _POSIX_C_SOURCE; link with -pthread.
 */
#ifndef BARRIER_H
#define BARRIER_H

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

/* Pthreads functions return an error number instead of setting errno. */
static inline void pt_check(int rc, const char *what)
{
    if (rc != 0) {
        fprintf(stderr, "error: %s failed (code %d)\n", what, rc);
        exit(1);
    }
}

typedef struct {
    pthread_mutex_t lock;
    pthread_cond_t all_here;
    int count;                  /* threads that must arrive      */
    int waiting;                /* threads arrived so far        */
    unsigned long generation;   /* bumped each time it opens     */
} barrier_t;

static inline void barrier_init(barrier_t *b, int count)
{
    pt_check(pthread_mutex_init(&b->lock, NULL), "mutex init");
    pt_check(pthread_cond_init(&b->all_here, NULL), "cond init");
    b->count = count;
    b->waiting = 0;
    b->generation = 0;
}

static inline void barrier_wait(barrier_t *b)
{
    pt_check(pthread_mutex_lock(&b->lock), "mutex lock");
    unsigned long gen = b->generation;
    if (++b->waiting == b->count) {            /* last to arrive */
        b->waiting = 0;
        b->generation++;
        pt_check(pthread_cond_broadcast(&b->all_here), "broadcast");
    } else {
        while (gen == b->generation)           /* guards against */
            pt_check(pthread_cond_wait(&b->all_here, &b->lock),
                     "cond wait");             /* spurious wakeups */
    }
    pt_check(pthread_mutex_unlock(&b->lock), "mutex unlock");
}

static inline void barrier_destroy(barrier_t *b)
{
    pt_check(pthread_cond_destroy(&b->all_here), "cond destroy");
    pt_check(pthread_mutex_destroy(&b->lock), "mutex destroy");
}

#endif
