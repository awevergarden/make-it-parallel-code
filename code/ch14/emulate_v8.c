/*
 * emulate_v8.c -- run HeatSim version 8's kernels on the CPU.
 * Make It Parallel, Chapter 14.
 *
 * Replays every block and every thread of each kernel launch, calling
 * the same per-thread functions as the GPU (heatsim_cell.h). For the
 * tiled kernel, all threads of a block finish tile_load before any
 * starts tile_compute -- what __syncthreads guarantees on the GPU.
 * This checks the kernels' index arithmetic and halo loading; it does
 * not test the GPU's hardware, memory system, or timing.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o emulate_v8 emulate_v8.c
 * Run:    ./emulate_v8 simple|tiled N STEPS [SNAPSHOT_STEP ...]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../heatsim/heatsim_cell.h"

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

static void launch(int tiled, const double *cur, double *next, int n)
{
    int gx = (n - 2 + BX - 1) / BX, gy = (n - 2 + BY - 1) / BY;
    double tile[(BY + 2) * TW];
    for (int by = 0; by < gy; by++)
        for (int bx = 0; bx < gx; bx++) {
            if (!tiled) {
                for (int ty = 0; ty < BY; ty++)
                    for (int tx = 0; tx < BX; tx++)
                        simple_update(cur, next, n, bx, by, tx, ty);
                continue;
            }
            for (int k = 0; k < (BY + 2) * TW; k++)
                tile[k] = -1e300;          /* poison: unloaded cells show */
            for (int ty = 0; ty < BY; ty++)
                for (int tx = 0; tx < BX; tx++)
                    tile_load(cur, tile, n, bx, by, tx, ty);
            /* __syncthreads() */
            for (int ty = 0; ty < BY; ty++)
                for (int tx = 0; tx < BX; tx++)
                    tile_compute(tile, next, n, bx, by, tx, ty);
        }
}

int main(int argc, char *argv[])
{
    if (argc < 4) {
        fprintf(stderr, "usage: %s simple|tiled N STEPS [SNAPSHOT_STEP ...]\n", argv[0]);
        return 1;
    }
    int tiled = strcmp(argv[1], "tiled") == 0;
    int n = atoi(argv[2]);
    long steps = atol(argv[3]);
    if (n < 3 || steps < 0) {
        fprintf(stderr, "error: need N >= 3 and STEPS >= 0\n");
        return 1;
    }
    double *cur = calloc((size_t)n * n, sizeof *cur);
    double *next = calloc((size_t)n * n, sizeof *next);
    if (cur == NULL || next == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    set_edges(cur, n);
    set_edges(next, n);
    int snap = 4;
    char path[64];
    for (long s = 0; ; s++) {
        while (snap < argc && atol(argv[snap]) == s) {
            snprintf(path, sizeof path, "snap_%ld.bin", s);
            FILE *f = fopen(path, "wb");
            if (f == NULL || fwrite(cur, sizeof *cur, (size_t)n * n, f) != (size_t)n * n
                || fclose(f) != 0) {
                perror(path);
                return 1;
            }
            snap++;
        }
        if (s == steps)
            break;
        launch(tiled, cur, next, n);
        double *tmp = cur;
        cur = next;
        next = tmp;
    }
    printf("center temperature after %ld steps: %.4f C\n", steps,
           cur[(size_t)(n / 2) * n + n / 2]);
    free(cur);
    free(next);
    return 0;
}
