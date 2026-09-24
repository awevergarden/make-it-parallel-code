/*
 * sem_queue.c -- the bounded queue again, with counting semaphores.
 * Make It Parallel, Chapter 7.
 *
 * `empty` counts free slots and `full` counts waiting items; a mutex
 * still protects the slots themselves. Unnamed POSIX semaphores
 * (sem_init) work on Linux but not on macOS.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -pthread -o sem_queue sem_queue.c
 * Run:    ./sem_queue CONSUMERS
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <semaphore.h>
#include <stdio.h>
#include <stdlib.h>
#include "../common/barrier.h"

#define CAPACITY 64
#define ITEMS 1000000L
#define MAX_CONSUMERS 64

static long items[CAPACITY];
static int head, tail;
static sem_t empty, full;               /* free slots; waiting items */
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

static void put(long v)
{
    if (sem_wait(&empty) != 0) {        /* claim a free slot */
        perror("sem_wait");
        exit(1);
    }
    pt_check(pthread_mutex_lock(&lock), "lock");
    items[tail] = v;
    tail = (tail + 1) % CAPACITY;
    pt_check(pthread_mutex_unlock(&lock), "unlock");
    sem_post(&full);                    /* announce an item */
}

static long take(void)
{
    if (sem_wait(&full) != 0) {         /* claim an item */
        perror("sem_wait");
        exit(1);
    }
    pt_check(pthread_mutex_lock(&lock), "lock");
    long v = items[head];
    head = (head + 1) % CAPACITY;
    pt_check(pthread_mutex_unlock(&lock), "unlock");
    sem_post(&empty);                   /* free the slot */
    return v;
}

struct result { long taken, sum; };

static void *consumer(void *arg)
{
    struct result *r = arg;
    for (long v; (v = take()) != 0; ) {
        r->taken++;
        r->sum += v;
    }
    return NULL;
}

int main(int argc, char *argv[])
{
    int c = argc > 1 ? atoi(argv[1]) : 3;
    if (c < 1 || c > MAX_CONSUMERS) {
        fprintf(stderr, "usage: %s CONSUMERS (1..%d)\n", argv[0], MAX_CONSUMERS);
        return 1;
    }
    if (sem_init(&empty, 0, CAPACITY) != 0 || sem_init(&full, 0, 0) != 0) {
        perror("sem_init");
        return 1;
    }
    pthread_t tid[MAX_CONSUMERS];
    struct result res[MAX_CONSUMERS] = {{0, 0}};
    for (int k = 0; k < c; k++)
        pt_check(pthread_create(&tid[k], NULL, consumer, &res[k]), "create");
    for (long v = 1; v <= ITEMS; v++)
        put(v);
    for (int k = 0; k < c; k++)
        put(0);                         /* poison pills */
    long taken = 0, sum = 0;
    for (int k = 0; k < c; k++) {
        pt_check(pthread_join(tid[k], NULL), "join");
        taken += res[k].taken;
        sum += res[k].sum;
    }
    printf("consumers %d: took %ld items, sum %ld (expected %ld)\n",
           c, taken, sum, ITEMS * (ITEMS + 1) / 2);
    return sum == ITEMS * (ITEMS + 1) / 2 && taken == ITEMS ? 0 : 1;
}
