/*
 * vpatterns.c -- three vectorization patterns, timed.
 * Make It Parallel, Chapter 6.
 *
 * 1. Moving 4,096 particles: array of structures vs structure of arrays.
 * 2. A loop with a condition: y = max(x, 0), the "ReLU" of neural nets.
 * 3. a*x + y in float and in double: twice as many float lanes.
 * Every array fits in the L1 cache; each kernel is repeated many times.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp-simd -Wall -Wextra -o vpatterns vpatterns.c
 * Run:    ./vpatterns          (prints: kernel,ns_per_element)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include "../common/timer.h"

#define N 1024
#define REPS 200000

struct particle { double x, y, z, vx, vy, vz; };

static void move_aos(struct particle *restrict p, int n, double dt)
{
    #pragma omp simd
    for (int i = 0; i < n; i++) {
        p[i].x += p[i].vx * dt;
        p[i].y += p[i].vy * dt;
        p[i].z += p[i].vz * dt;
    }
}

static void move_soa(double *restrict x, double *restrict y,
                     double *restrict z, const double *restrict vx,
                     const double *restrict vy, const double *restrict vz,
                     int n, double dt)
{
    #pragma omp simd
    for (int i = 0; i < n; i++) {
        x[i] += vx[i] * dt;
        y[i] += vy[i] * dt;
        z[i] += vz[i] * dt;
    }
}

static void relu(const double *restrict x, double *restrict y, int n)
{
    #pragma omp simd
    for (int i = 0; i < n; i++)
        y[i] = x[i] > 0.0 ? x[i] : 0.0;
}

static void axpy_d(double a, const double *restrict x, double *restrict y, int n)
{
    #pragma omp simd
    for (int i = 0; i < n; i++)
        y[i] = a * x[i] + y[i];
}

static void axpy_f(float a, const float *restrict x, float *restrict y, int n)
{
    #pragma omp simd
    for (int i = 0; i < n; i++)
        y[i] = a * x[i] + y[i];
}

#define TIME(label, call) do {                                         \
    double best = 1e30;                                                \
    for (int t = 0; t < 3; t++) {                                      \
        double t0 = now_seconds();                                     \
        for (int r = 0; r < REPS; r++) { call; }                       \
        double el = now_seconds() - t0;                                \
        if (el < best) best = el;                                      \
    }                                                                  \
    printf("%s,%.4f\n", label, best / ((double)N * REPS) * 1e9);       \
} while (0)

int main(void)
{
    struct particle *p = malloc(N * sizeof *p);
    double *x = malloc(N * sizeof *x), *y = malloc(N * sizeof *y);
    double *z = malloc(N * sizeof *z), *vx = malloc(N * sizeof *vx);
    double *vy = malloc(N * sizeof *vy), *vz = malloc(N * sizeof *vz);
    float *xf = malloc(N * sizeof *xf), *yf = malloc(N * sizeof *yf);
    if (!p || !x || !y || !z || !vx || !vy || !vz || !xf || !yf) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    for (int i = 0; i < N; i++) {
        p[i] = (struct particle){0, 0, 0, 1e-9 * i, -1e-9 * i, 1e-9};
        x[i] = y[i] = z[i] = 0.0;
        vx[i] = 1e-9 * i; vy[i] = -1e-9 * i; vz[i] = 1e-9;
        xf[i] = (float)(i % 7) - 3.0f; yf[i] = 0.0f;
    }
    double *rx = malloc(N * sizeof *rx), *ry = malloc(N * sizeof *ry);
    if (!rx || !ry)
        return 1;
    for (int i = 0; i < N; i++)
        rx[i] = (double)(i % 9) - 4.0;
    printf("kernel,ns_per_element\n");
    TIME("particles_aos", move_aos(p, N, 1e-3));
    TIME("particles_soa", move_soa(x, y, z, vx, vy, vz, N, 1e-3));
    TIME("relu", relu(rx, ry, N));
    TIME("axpy_double", axpy_d(1e-9, rx, y, N));
    TIME("axpy_float", axpy_f(1e-9f, xf, yf, N));
    fprintf(stderr, "check %g %g %g %g\n", p[N / 2].x + x[N / 2], ry[5], y[7], (double)yf[3]);
    free(p); free(x); free(y); free(z); free(vx); free(vy); free(vz);
    free(xf); free(yf); free(rx); free(ry);
    return 0;
}
