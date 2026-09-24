/*
 * launcher_threads.c -- Chapter 2's launcher, now with real threads.
 * Make It Parallel, Chapter 7.
 *
 * The worker function and its struct are unchanged from
 * code/ch02/launcher.c; only run_all() differs. It starts one thread
 * per task with pthread_create and waits for all of them with
 * pthread_join, so the tasks may run at the same time.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -pthread \
 *             -o launcher_threads launcher_threads.c
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

#define NUM_TASKS 4

struct task {
    int id;           /* which task this is            */
    int first_row;    /* first row this task handles   */
    int last_row;     /* one past the last row         */
    double result;    /* filled in by the worker       */
};

typedef void *(*worker_fn)(void *);

static void *count_rows(void *arg)
{
    struct task *t = arg;
    t->result = t->last_row - t->first_row;
    printf("task %d: rows %d to %d\n",
           t->id, t->first_row, t->last_row - 1);
    return NULL;
}

/* Start one thread per task, then wait for them all. */
static void run_all(worker_fn fn, struct task tasks[], int count)
{
    pthread_t tid[NUM_TASKS];
    for (int k = 0; k < count; k++) {
        int rc = pthread_create(&tid[k], NULL, fn, &tasks[k]);
        if (rc != 0) {
            fprintf(stderr, "error: pthread_create (code %d)\n", rc);
            exit(1);
        }
    }
    for (int k = 0; k < count; k++) {
        int rc = pthread_join(tid[k], NULL);
        if (rc != 0) {
            fprintf(stderr, "error: pthread_join (code %d)\n", rc);
            exit(1);
        }
    }
}

int main(void)
{
    int n = 10;
    struct task tasks[NUM_TASKS];
    for (int k = 0; k < NUM_TASKS; k++) {
        tasks[k].id = k;
        tasks[k].first_row = k * n / NUM_TASKS;
        tasks[k].last_row = (k + 1) * n / NUM_TASKS;
        tasks[k].result = 0.0;
    }
    run_all(count_rows, tasks, NUM_TASKS);

    double total = 0.0;
    for (int k = 0; k < NUM_TASKS; k++)
        total += tasks[k].result;
    printf("total rows: %.0f\n", total);
    return 0;
}
