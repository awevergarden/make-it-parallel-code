/*
 * heatsim_v5.c -- HeatSim version 5 (OpenMP)
 * Make It Parallel, companion code (Chapter 8).
 *
 * The same algorithm as version 4, written with OpenMP instead of
 * Pthreads: one parallel region encloses the whole time loop, and
 * "#pragma omp for" divides the rows among the threads, with an
 * implicit barrier after each step. Results are bit-identical to
 * version 1 for any number of threads.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp -Wall -Wextra \
 *             -o heatsim_v5 heatsim_v5.c
 * Run:    OMP_NUM_THREADS=4 ./heatsim_v5 N STEPS [SNAPSHOT_STEP ...]
 *         (same arguments as version 1; the thread count comes from
 *         OMP_NUM_THREADS)
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

#define HOT  100.0
#define COLD   0.0

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

/* Run STEPS time steps with the current OpenMP thread count. */
static void run_steps(double **cur_p, double **next_p, int n, long steps)
{
    double *cur = *cur_p, *next = *next_p;
    #pragma omp parallel default(none) shared(n, steps) \
                         firstprivate(cur, next)
    {
        for (long s = 0; s < steps; s++) {
            #pragma omp for schedule(static)
            for (int i = 1; i < n - 1; i++)
                update_row(cur, next, i, n);
            /* implicit barrier: every row of step s is done */
            double *tmp = cur;      /* each thread swaps its own */
            cur = next;             /* private copies            */
            next = tmp;
        }
    }
    if (steps % 2 == 1) {           /* match the threads' swaps */
        *cur_p = next;
        *next_p = cur;
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
    long n_arg, steps;
    if (argc < 3
        || parse_long(argv[1], 3, 46340, &n_arg) != 0
        || parse_long(argv[2], 0, 1000000000L, &steps) != 0) {
        fprintf(stderr, "usage: %s N STEPS [SNAPSHOT_STEP ...]\n"
                "       3 <= N <= 46340, STEPS >= 0\n", argv[0]);
        return 1;
    }
    int n = (int)n_arg;
    double *cur = calloc((size_t)n * n, sizeof *cur);
    double *next = calloc((size_t)n * n, sizeof *next);
    if (cur == NULL || next == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    set_edges(cur, n);
    set_edges(next, n);

    double t0 = omp_get_wtime();
    long done = 0;
    char path[64];
    for (int a = 3; a <= argc; a++) {          /* segments between snapshots */
        long target = steps;
        if (a < argc && parse_long(argv[a], done, steps, &target) != 0) {
            fprintf(stderr, "error: bad snapshot step %s\n", argv[a]);
            return 1;
        }
        run_steps(&cur, &next, n, target - done);
        done = target;
        if (a < argc) {
            snprintf(path, sizeof path, "snap_%ld.bin", done);
            if (write_grid(path, cur, n) != 0) {
                perror(path);
                return 1;
            }
        }
    }
    double elapsed = omp_get_wtime() - t0;

    double updates = (double)(n - 2) * (n - 2) * (double)steps;
    printf("center temperature after %ld steps: %.4f C\n",
           steps, cur[(n / 2) * n + n / 2]);
    printf("time: %.6f s, %.1f million cell updates per second, %d threads\n",
           elapsed, elapsed > 0 ? updates / elapsed / 1e6 : 0.0,
           omp_get_max_threads());
    free(cur);
    free(next);
    return 0;
}
