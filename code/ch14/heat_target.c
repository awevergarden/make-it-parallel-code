/*
 * heat_target.c -- HeatSim with OpenMP offload directives.
 * Make It Parallel, Chapter 14.
 *
 * The target data region copies both grids to the device once; each step
 * runs as a target region spread over teams and threads. With a GPU and
 * an offloading compiler, it runs there; without one, the same program
 * runs on the host, which is how Chapter 14 checked it.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp -Wall -Wextra -o heat_target heat_target.c
 * Run:    ./heat_target N STEPS [SNAPSHOT_STEP ...]
 */
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

static void set_edges(double *g, int n)
{
    for (int j = 0; j < n; j++) {
        g[j] = 100.0;
        g[(size_t)(n - 1) * n + j] = 0.0;
    }
    for (int i = 1; i < n - 1; i++) {
        g[(size_t)i * n] = 0.0;
        g[(size_t)i * n + n - 1] = 0.0;
    }
}

static int write_grid(const char *path, const double *g, int n)
{
    FILE *f = fopen(path, "wb");
    if (f == NULL)
        return -1;
    size_t count = (size_t)n * n;
    size_t w = fwrite(g, sizeof *g, count, f);
    return fclose(f) == 0 && w == count ? 0 : -1;
}

int main(int argc, char *argv[])
{
    if (argc < 3) {
        fprintf(stderr, "usage: %s N STEPS [SNAPSHOT_STEP ...]\n", argv[0]);
        return 1;
    }
    int n = atoi(argv[1]);
    long steps = atol(argv[2]);
    if (n < 3 || steps < 0)
        return 1;
    size_t nn = (size_t)n * n;
    double *a = calloc(nn, sizeof *a), *b = calloc(nn, sizeof *b);
    if (a == NULL || b == NULL)
        return 1;
    set_edges(a, n);
    set_edges(b, n);
    int snap = 3, failed = 0;
    char path[64];
    #pragma omp target data map(tofrom: a[0:nn], b[0:nn])
    for (long s = 0; ; s++) {
        while (snap < argc && atol(argv[snap]) == s) {
            double *cur = s % 2 == 0 ? a : b;
            #pragma omp target update from(cur[0:nn])
            snprintf(path, sizeof path, "snap_%ld.bin", s);
            if (write_grid(path, cur, n) != 0) {
                failed = 1;             /* no return from inside the region */
                break;
            }
            snap++;
        }
        if (failed || s == steps)
            break;
        const double *cur = s % 2 == 0 ? a : b;
        double *next = s % 2 == 0 ? b : a;
        #pragma omp target teams distribute parallel for collapse(2)
        for (int i = 1; i < n - 1; i++)
            for (int j = 1; j < n - 1; j++)
                next[i * n + j] = 0.25 * (cur[(i - 1) * n + j] + cur[(i + 1) * n + j]
                                        + cur[i * n + j - 1] + cur[i * n + j + 1]);
    }
    if (failed) {
        perror("snapshot");
        return 1;
    }
    double *last = steps % 2 == 0 ? a : b;
    printf("center temperature after %ld steps: %.4f C (devices available: %d)\n",
           steps, last[(size_t)(n / 2) * n + n / 2], omp_get_num_devices());
    free(a);
    free(b);
    return 0;
}
