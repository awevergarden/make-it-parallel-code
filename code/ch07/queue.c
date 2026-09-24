/*
 * queue.c -- a bounded producer-consumer queue.
 * Make It Parallel, Chapter 7.
 *
 * One producer puts the numbers 1..ITEMS into a queue that holds at
 * most CAPACITY items; CONSUMERS threads take them out and add them
 * up. A mutex protects the queue, and two condition variables let a
 * thread sleep until the queue is not full (producer) or not empty
 * (consumers). Each consumer stops when it takes the value 0.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -pthread -o queue queue.c
 * Run:    ./queue CONSUMERS
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include "../common/barrier.h"
#include "../common/timer.h"

#define CAPACITY 64
#define ITEMS 1000000L
#define MAX_CONSUMERS 64

struct queue {
    long items[CAPACITY];
    int head, count;                    /* next to take; how many */
    pthread_mutex_t lock;
    pthread_cond_t not_full, not_empty;
};

static void queue_put(struct queue *q, long v)
{
    pt_check(pthread_mutex_lock(&q->lock), "lock");
    while (q->count == CAPACITY)        /* full: wait for a taker */
        pt_check(pthread_cond_wait(&q->not_full, &q->lock), "wait");
    q->items[(q->head + q->count) % CAPACITY] = v;
    q->count++;
    pt_check(pthread_cond_signal(&q->not_empty), "signal");
    pt_check(pthread_mutex_unlock(&q->lock), "unlock");
}

static long queue_take(struct queue *q)
{
    pt_check(pthread_mutex_lock(&q->lock), "lock");
    while (q->count == 0)               /* empty: wait for a putter */
        pt_check(pthread_cond_wait(&q->not_empty, &q->lock), "wait");
    long v = q->items[q->head];
    q->head = (q->head + 1) % CAPACITY;
    q->count--;
    pt_check(pthread_cond_signal(&q->not_full), "signal");
    pt_check(pthread_mutex_unlock(&q->lock), "unlock");
    return v;
}

static struct queue q;

struct result { long taken, sum; };

static void *consumer(void *arg)
{
    struct result *r = arg;
    for (;;) {
        long v = queue_take(&q);
        if (v == 0)                     /* the stop signal */
            return NULL;
        r->taken++;
        r->sum += v;
    }
}

int main(int argc, char *argv[])
{
    int c = argc > 1 ? atoi(argv[1]) : 3;
    if (c < 1 || c > MAX_CONSUMERS) {
        fprintf(stderr, "usage: %s CONSUMERS (1..%d)\n", argv[0], MAX_CONSUMERS);
        return 1;
    }
    pt_check(pthread_mutex_init(&q.lock, NULL), "mutex init");
    pt_check(pthread_cond_init(&q.not_full, NULL), "cond init");
    pt_check(pthread_cond_init(&q.not_empty, NULL), "cond init");
    pthread_t tid[MAX_CONSUMERS];
    struct result res[MAX_CONSUMERS] = {{0, 0}};
    double t0 = now_seconds();
    for (int k = 0; k < c; k++)
        pt_check(pthread_create(&tid[k], NULL, consumer, &res[k]), "create");
    for (long v = 1; v <= ITEMS; v++)   /* this thread is the producer */
        queue_put(&q, v);
    for (int k = 0; k < c; k++)
        queue_put(&q, 0);               /* one stop signal per consumer */
    long taken = 0, sum = 0;
    for (int k = 0; k < c; k++) {
        pt_check(pthread_join(tid[k], NULL), "join");
        taken += res[k].taken;
        sum += res[k].sum;
    }
    double t = now_seconds() - t0;
    printf("consumers %d: took %ld items, sum %ld (expected %ld), %.2f us per item\n",
           c, taken, sum, ITEMS * (ITEMS + 1) / 2, t / ITEMS * 1e6);
    return sum == ITEMS * (ITEMS + 1) / 2 && taken == ITEMS ? 0 : 1;
}
