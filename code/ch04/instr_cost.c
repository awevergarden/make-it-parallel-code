/*
 * instr_cost.c -- latency and throughput of basic arithmetic.
 * Make It Parallel, Chapter 4.
 *
 * For each operation, lat_OP() runs one long dependency chain (each
 * result feeds the next operation), and thr_OP() runs 8 independent
 * chains that the core can overlap. Reports nanoseconds per operation.
 *
 * Build:  gcc -std=c17 -O2 -fno-tree-vectorize -Wall -Wextra \
 *             -o instr_cost instr_cost.c -lm
 */
#define _POSIX_C_SOURCE 200809L
#include <math.h>
#include <stdio.h>
#include "../common/timer.h"

#define OPS 50000000L

static double op_add(double x, double a)  { return x + a; }
static double op_mul(double x, double a)  { return x * a; }
static double op_div(double x, double a)  { return x / a; }
static double op_sqrt(double x, double a) { return sqrt(x) + a; }

/* One dependent chain, and eight independent chains, per operation. */
#define TESTS(OP)                                                      \
static double lat_##OP(double a)                                       \
{                                                                      \
    double x = 1.0;                                                    \
    for (long k = 0; k < OPS; k++)                                     \
        x = op_##OP(x, a);                                             \
    return x;                                                          \
}                                                                      \
static double thr_##OP(double a)                                       \
{                                                                      \
    double x0 = 1.0, x1 = 1.1, x2 = 1.2, x3 = 1.3;                     \
    double x4 = 1.4, x5 = 1.5, x6 = 1.6, x7 = 1.7;                     \
    for (long k = 0; k < OPS / 8; k++) {                               \
        x0 = op_##OP(x0, a); x1 = op_##OP(x1, a);                      \
        x2 = op_##OP(x2, a); x3 = op_##OP(x3, a);                      \
        x4 = op_##OP(x4, a); x5 = op_##OP(x5, a);                      \
        x6 = op_##OP(x6, a); x7 = op_##OP(x7, a);                      \
    }                                                                  \
    return x0 + x1 + x2 + x3 + x4 + x5 + x6 + x7;                      \
}
TESTS(add)
TESTS(mul)
TESTS(div)
TESTS(sqrt)

static volatile double va = 1.0000001;  /* unknown to the compiler */

static void run(const char *name, double (*lat)(double), double (*thr)(double),
                double a)
{
    double t0 = now_seconds();
    double r1 = lat(a);
    double t1 = now_seconds();
    double r2 = thr(a);
    double t2 = now_seconds();
    printf("%s,%.3f,%.3f,%g\n", name, (t1 - t0) / OPS * 1e9,
           (t2 - t1) / OPS * 1e9, r1 + r2);
}

int main(void)
{
    double a = va;
    printf("op,latency_ns,throughput_ns,check\n");
    run("add", lat_add, thr_add, a);
    run("multiply", lat_mul, thr_mul, a);
    run("divide", lat_div, thr_div, a);
    run("sqrt", lat_sqrt, thr_sqrt, 1e-9 * a);
    return 0;
}
