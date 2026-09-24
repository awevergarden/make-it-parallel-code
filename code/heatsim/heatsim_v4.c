/*
 * heatsim_v4.c -- HeatSim version 4 (Pthreads)
 * Make It Parallel, companion code (Chapter 7).
 *
 * The interior rows are divided into THREADS contiguous blocks. Each
 * thread updates its own rows with version 3's vectorized kernel,
 * then waits at a barrier so that no thread starts step s + 1 until
 * every thread has finished step s. One time step per sweep (version
 * 2's two-step sweep would cross block boundaries). Results are
 * bit-identical to version 1 for any number of threads.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp-simd -pthread -Wall -Wextra \
 *             -o heatsim_v4 heatsim_v4.c
 * Run:    ./heatsim_v4 N STEPS THREADS [SNAPSHOT_STEP ...]
 *         Snapshots are written as in version 1; benchmark runs
 *         should request none.
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include "../common/barrier.h"
#include "../common/timer.h"

#define HOT  100.0
#define COLD   0.0
#define MAX_THREADS 256

static int parse_long(const char *text, long lo, long hi, long *out)
{
    char *end;
    errno = 0;
    long v = strtol(text, &end, 10);
    if (end == text || *end != '\0' || errno == ERANGE
        || v < lo || v > hi)
        return -1;
    *out = v;
    return 0;
}

static void set_edges(double *g, int n)
{
    for (int j = 0; j < n; j++) {
        g[j] = HOT;
        g[(n - 1) * n + j] = COLD;
    }
    for (int i = 1; i < n - 1; i++) {
        g[i * n] = COLD;
        g[i * n + n - 1] = COLD;
    }
}

/* Version 3's kernel: update interior row i of dst from src. */
static void update_row(const double *restrict src, double *restrict dst,
                       int i, int n)
{
    #pragma omp simd
    for (int j = 1; j < n - 1; j++)
        dst[i * n + j] = 0.25 * (src[(i - 1) * n + j]
                               + src[(i + 1) * n + j]
                               + src[i * n + j - 1]
                               + src[i * n + j + 1]);
}

struct task {
    int first_row, last_row;    /* this thread's rows: [first, last) */
    int n;
    long steps;
    double *cur, *next;         /* each thread swaps its own copies */
    barrier_t *bar;
};

static void *worker(void *arg)
{
    struct task *t = arg;
    double *cur = t->cur, *next = t->next;
    for (long s = 0; s < t->steps; s++) {
        for (int i = t->first_row; i < t->last_row; i++)
            update_row(cur, next, i, t->n);
        barrier_wait(t->bar);   /* everyone finished step s */
        double *tmp = cur;
        cur = next;
        next = tmp;
    }
    return NULL;
}

/* Run STEPS time steps with P threads, starting from *cur. */
static void run_steps(double **cur, double **next, int n, long steps, int p)
{
    pthread_t tid[MAX_THREADS];
    struct task tasks[MAX_THREADS];
    barrier_t bar;
    barrier_init(&bar, p);
    int rows = n - 2;                           /* interior rows */
    for (int k = 0; k < p; k++) {
        tasks[k] = (struct task){
            .first_row = 1 + (int)((long)k * rows / p),
            .last_row = 1 + (int)((long)(k + 1) * rows / p),
            .n = n, .steps = steps, .cur = *cur, .next = *next,
            .bar = &bar};
        pt_check(pthread_create(&tid[k], NULL, worker, &tasks[k]),
                 "pthread_create");
    }
    for (int k = 0; k < p; k++)
        pt_check(pthread_join(tid[k], NULL), "pthread_join");
    barrier_destroy(&bar);
    if (steps % 2 == 1) {                       /* match the threads */
        double *tmp = *cur;
        *cur = *next;
        *next = tmp;
    }
}

static int write_grid(const char *path, const double *g, int n)
{
    FILE *f = fopen(path, "wb");
    if (f == NULL)
        return -1;
    size_t count = (size_t)n * n;
    size_t written = fwrite(g, sizeof *g, count, f);
    if (fclose(f) != 0)
        return -1;
    return written == count ? 0 : -1;
}

int main(int argc, char *argv[])
{
    long n_arg, steps, p_arg;
    if (argc < 4
        || parse_long(argv[1], 3, 46340, &n_arg) != 0
        || parse_long(argv[2], 0, 1000000000L, &steps) != 0
        || parse_long(argv[3], 1, MAX_THREADS, &p_arg) != 0
        || p_arg > n_arg - 2) {
        fprintf(stderr, "usage: %s N STEPS THREADS [SNAPSHOT_STEP ...]\n"
                "       3 <= N <= 46340, 1 <= THREADS <= min(%d, N - 2)\n",
                argv[0], MAX_THREADS);
        return 1;
    }
    int n = (int)n_arg, p = (int)p_arg;
    double *cur = calloc((size_t)n * n, sizeof *cur);
    double *next = calloc((size_t)n * n, sizeof *next);
    if (cur == NULL || next == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    set_edges(cur, n);
    set_edges(next, n);

    double t0 = now_seconds();
    long done = 0;
    char path[64];
    for (int a = 4; a <= argc; a++) {          /* segments between snapshots */
        long target = steps;
        if (a < argc && parse_long(argv[a], done, steps, &target) != 0) {
            fprintf(stderr, "error: bad snapshot step %s\n", argv[a]);
            return 1;
        }
        run_steps(&cur, &next, n, target - done, p);
        done = target;
        if (a < argc) {
            snprintf(path, sizeof path, "snap_%ld.bin", done);
            if (write_grid(path, cur, n) != 0) {
                perror(path);
                return 1;
            }
        }
    }
    double elapsed = now_seconds() - t0;

    double updates = (double)(n - 2) * (n - 2) * (double)steps;
    printf("center temperature after %ld steps: %.4f C\n",
           steps, cur[(n / 2) * n + n / 2]);
    printf("time: %.6f s, %.1f million cell updates per second, %d threads\n",
           elapsed, elapsed > 0 ? updates / elapsed / 1e6 : 0.0, p);
    free(cur);
    free(next);
    return 0;
}
