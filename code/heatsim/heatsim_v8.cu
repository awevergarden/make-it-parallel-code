/*
 * heatsim_v8.cu -- HeatSim version 8 (CUDA)
 * Make It Parallel, companion code (Chapter 14).
 *
 * The grid lives in GPU memory for the whole run; each time step is one
 * kernel launch with one thread per interior cell. HEATSIM_KERNEL=simple
 * reads neighbors from global memory; the default, tiled, first copies
 * each block's patch and its halo into shared memory. The per-thread
 * code is in heatsim_cell.h, shared with the CPU emulator.
 *
 * Build:  nvcc -O2 -arch=sm_80 -o heatsim_v8 heatsim_v8.cu
 * Run:    ./heatsim_v8 N STEPS [SNAPSHOT_STEP ...]
 */
#include <cuda_runtime.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "heatsim_cell.h"

#define HOT  100.0
#define COLD   0.0

#define CUDA_CHECK(call) do {                                          \
    cudaError_t err_ = (call);                                         \
    if (err_ != cudaSuccess) {                                         \
        fprintf(stderr, "CUDA error %s at %s:%d\n",                    \
                cudaGetErrorString(err_), __FILE__, __LINE__);         \
        exit(1);                                                       \
    }                                                                  \
} while (0)

__global__ void step_simple(const double *cur, double *next, int n)
{
    simple_update(cur, next, n, blockIdx.x, blockIdx.y,
                  threadIdx.x, threadIdx.y);
}

__global__ void step_tiled(const double *cur, double *next, int n)
{
    __shared__ double tile[(BY + 2) * TW];
    tile_load(cur, tile, n, blockIdx.x, blockIdx.y, threadIdx.x, threadIdx.y);
    __syncthreads();                    /* the whole tile is loaded */
    tile_compute(tile, next, n, blockIdx.x, blockIdx.y,
                 threadIdx.x, threadIdx.y);
}

static int parse_long(const char *text, long lo, long hi, long *out)
{
    char *end;
    errno = 0;
    long v = strtol(text, &end, 10);
    if (end == text || *end != '\0' || errno == ERANGE || v < lo || v > hi)
        return -1;
    *out = v;
    return 0;
}

static void set_edges(double *g, int n)
{
    for (int j = 0; j < n; j++) {
        g[j] = HOT;
        g[(size_t)(n - 1) * n + j] = COLD;
    }
    for (int i = 1; i < n - 1; i++) {
        g[(size_t)i * n] = COLD;
        g[(size_t)i * n + n - 1] = COLD;
    }
}

int main(int argc, char *argv[])
{
    long n_arg, steps;
    if (argc < 3 || parse_long(argv[1], 3, 46340, &n_arg) != 0
        || parse_long(argv[2], 0, 1000000000L, &steps) != 0) {
        fprintf(stderr, "usage: %s N STEPS [SNAPSHOT_STEP ...]\n", argv[0]);
        return 1;
    }
    int n = (int)n_arg;
    const char *k = getenv("HEATSIM_KERNEL");
    int tiled = k == NULL || strcmp(k, "simple") != 0;
    size_t bytes = (size_t)n * n * sizeof(double);
    double *host = (double *)calloc((size_t)n * n, sizeof(double));
    if (host == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    set_edges(host, n);
    double *cur, *next;
    CUDA_CHECK(cudaMalloc(&cur, bytes));
    CUDA_CHECK(cudaMalloc(&next, bytes));
    CUDA_CHECK(cudaMemcpy(cur, host, bytes, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(next, host, bytes, cudaMemcpyHostToDevice));

    dim3 block(BX, BY);
    dim3 grid((n - 2 + BX - 1) / BX, (n - 2 + BY - 1) / BY);
    cudaEvent_t t0, t1;
    CUDA_CHECK(cudaEventCreate(&t0));
    CUDA_CHECK(cudaEventCreate(&t1));
    CUDA_CHECK(cudaEventRecord(t0));
    long done = 0;
    char path[64];
    for (int a = 3; a <= argc; a++) {
        long target = steps;
        if (a < argc && parse_long(argv[a], done, steps, &target) != 0) {
            fprintf(stderr, "error: bad snapshot step %s\n", argv[a]);
            return 1;
        }
        for (; done < target; done++) {
            if (tiled)
                step_tiled<<<grid, block>>>(cur, next, n);
            else
                step_simple<<<grid, block>>>(cur, next, n);
            double *tmp = cur;
            cur = next;
            next = tmp;
        }
        CUDA_CHECK(cudaGetLastError());
        if (a < argc) {
            CUDA_CHECK(cudaMemcpy(host, cur, bytes, cudaMemcpyDeviceToHost));
            snprintf(path, sizeof path, "snap_%ld.bin", done);
            FILE *f = fopen(path, "wb");
            if (f == NULL || fwrite(host, sizeof(double), (size_t)n * n, f)
                                 != (size_t)n * n || fclose(f) != 0) {
                perror(path);
                return 1;
            }
        }
    }
    CUDA_CHECK(cudaEventRecord(t1));
    CUDA_CHECK(cudaEventSynchronize(t1));
    float ms = 0.0f;
    CUDA_CHECK(cudaEventElapsedTime(&ms, t0, t1));
    CUDA_CHECK(cudaMemcpy(host, cur, bytes, cudaMemcpyDeviceToHost));
    double updates = (double)(n - 2) * (n - 2) * (double)steps;
    printf("center temperature after %ld steps: %.4f C\n",
           steps, host[(size_t)(n / 2) * n + n / 2]);
    printf("time: %.6f s, %.1f million cell updates per second, %s kernel\n",
           ms / 1000.0, ms > 0 ? updates / (ms / 1000.0) / 1e6 : 0.0,
           tiled ? "tiled" : "simple");
    CUDA_CHECK(cudaFree(cur));
    CUDA_CHECK(cudaFree(next));
    free(host);
    return 0;
}
