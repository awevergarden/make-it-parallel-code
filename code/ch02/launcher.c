/*
 * launcher.c -- function pointers and void * arguments.
 * Make It Parallel, Chapter 2.
 *
 * run_all() calls a worker function once per task, passing each
 * call a pointer to its own arguments. The worker has exactly the
 * signature Pthreads expects (Chapter 7); here the calls simply
 * run one after another.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o launcher launcher.c
 */
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

/* Count the rows in this task's share; a stand-in for real work. */
static void *count_rows(void *arg)
{
    struct task *t = arg;          /* recover the real type */
    t->result = t->last_row - t->first_row;
    printf("task %d: rows %d to %d\n",
           t->id, t->first_row, t->last_row - 1);
    return NULL;
}

/* Call fn once for each task. Chapter 7 replaces the call with
   pthread_create so that the tasks run at the same time. */
static void run_all(worker_fn fn, struct task tasks[], int count)
{
    for (int k = 0; k < count; k++)
        fn(&tasks[k]);
}

int main(void)
{
    int n = 10;                   /* rows to share out */
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
