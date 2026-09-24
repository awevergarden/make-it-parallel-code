/*
 * heatsim_seq.c -- HeatSim version 1 (sequential)
 * Make It Parallel, companion code (Chapter 3).
 *
 * Simulates heat spreading across a square plate with Jacobi
 * iteration on an n x n grid. The top edge is held at 100 C;
 * the other three edges are held at 0 C.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o heatsim_seq heatsim_seq.c
 * Run:    ./heatsim_seq N STEPS [SNAPSHOT_STEP ...]
 *         Snapshot steps must be in increasing order. Each one is
 *         written to snap_<step>.bin as n*n doubles (row-major).
 *         Benchmark runs should request no snapshots, because the
 *         reported time includes writing them.
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include "../common/timer.h"

#define HOT  100.0
#define COLD   0.0

/* Convert text to a long in [lo, hi]. Returns 0 on success. */
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

/* Fix the edge cells. The update loop never writes them. */
static void set_edges(double *g, int n)
{
    for (int j = 0; j < n; j++) {
        g[j] = HOT;                    /* top row    */
        g[(n - 1) * n + j] = COLD;     /* bottom row */
    }
    for (int i = 1; i < n - 1; i++) {
        g[i * n] = COLD;               /* left column  */
        g[i * n + n - 1] = COLD;       /* right column */
    }
}

/* One time step: every interior cell becomes the average of
   its four neighbors in the current grid. */
static void step(const double *cur, double *next, int n)
{
    for (int i = 1; i < n - 1; i++)
        for (int j = 1; j < n - 1; j++)
            next[i * n + j] = 0.25 * (cur[(i - 1) * n + j]
                                    + cur[(i + 1) * n + j]
                                    + cur[i * n + j - 1]
                                    + cur[i * n + j + 1]);
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

    int snap = 3;                      /* next snapshot argument */
    long snap_step = -1;
    if (snap < argc && parse_long(argv[snap], 0, steps, &snap_step)) {
        fprintf(stderr, "error: bad snapshot step %s\n", argv[snap]);
        return 1;
    }
    char path[64];
    double t0 = now_seconds();
    for (long s = 0; ; s++) {
        while (snap < argc && snap_step == s) {
            snprintf(path, sizeof path, "snap_%ld.bin", s);
            if (write_grid(path, cur, n) != 0) {
                perror(path);
                return 1;
            }
            snap++;
            if (snap < argc
                && parse_long(argv[snap], s + 1, steps, &snap_step)) {
                fprintf(stderr, "error: bad snapshot step %s\n",
                        argv[snap]);
                return 1;
            }
        }
        if (s == steps)
            break;
        step(cur, next, n);
        double *tmp = cur;             /* swap roles, no copying */
        cur = next;
        next = tmp;
    }
    double elapsed = now_seconds() - t0;

    double updates = (double)(n - 2) * (n - 2) * (double)steps;
    printf("center temperature after %ld steps: %.4f C\n",
           steps, cur[(n / 2) * n + n / 2]);
    printf("time: %.6f s, %.1f million cell updates per second\n",
           elapsed, elapsed > 0 ? updates / elapsed / 1e6 : 0.0);
    free(cur);
    free(next);
    return 0;
}
