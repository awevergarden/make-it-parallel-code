/*
 * train_mpi.c -- data-parallel training of a linear model with MPI.
 * Make It Parallel, Chapter 15.
 *
 * Every process holds the same model (D weights) and its own shard of
 * the N training samples. Each step, it computes the gradient of the
 * squared error on its shard, the processes sum their gradients with an
 * allreduce, and every process applies the same update. MODE mpi uses
 * MPI_Allreduce; MODE ring uses a hand-written ring allreduce
 * (reduce-scatter, then allgather) and counts the bytes it sends.
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o train_mpi train_mpi.c -lm
 * Run:    mpirun -np P ./train_mpi mpi|ring
 */
#include <math.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 4096           /* training samples */
#define D 64             /* features = model size */
#define STEPS 300
#define LR 0.5

static long bytes_sent;

/* Deterministic pseudo-random numbers in [-1, 1). */
static double rnd(unsigned long long *s)
{
    *s = *s * 6364136223846793005ULL + 1442695040888963407ULL;
    return (double)(*s >> 11) / 4503599627370496.0 - 1.0;
}

/* Sum x (length len) across all processes, in place, around a ring. */
static void ring_allreduce(double *x, int len, int rank, int p)
{
    if (p == 1)
        return;
    int right = (rank + 1) % p, left = (rank - 1 + p) % p;
    int lo[65], seg;
    for (int c = 0; c <= p; c++)                     /* p segments */
        lo[c] = (int)((long)c * len / p);
    double *in = malloc(((len + p - 1) / p + 1) * sizeof *in);
    if (in == NULL)
        MPI_Abort(MPI_COMM_WORLD, 1);
    for (int s = 0; s < p - 1; s++) {                /* reduce-scatter */
        int send = (rank - s + p) % p, recv = (rank - s - 1 + p) % p;
        seg = lo[recv + 1] - lo[recv];
        MPI_Sendrecv(&x[lo[send]], lo[send + 1] - lo[send], MPI_DOUBLE, right, 0,
                     in, seg, MPI_DOUBLE, left, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        bytes_sent += 8L * (lo[send + 1] - lo[send]);
        for (int i = 0; i < seg; i++)
            x[lo[recv] + i] += in[i];
    }
    for (int s = 0; s < p - 1; s++) {                /* allgather */
        int send = (rank + 1 - s + p) % p, recv = (rank - s + p) % p;
        MPI_Sendrecv(&x[lo[send]], lo[send + 1] - lo[send], MPI_DOUBLE, right, 1,
                     &x[lo[recv]], lo[recv + 1] - lo[recv], MPI_DOUBLE, left, 1,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        bytes_sent += 8L * (lo[send + 1] - lo[send]);
    }
    free(in);
}

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank, p;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &p);
    int ring = argc > 1 && strcmp(argv[1], "ring") == 0;
    if (N % p != 0 || p > 64) {
        if (rank == 0)
            fprintf(stderr, "error: P must divide %d (and be at most 64)\n", N);
        MPI_Finalize();
        return 1;
    }
    /* Every process generates the same data set, then keeps its shard. */
    unsigned long long seed = 42;
    double w_true[D], w[D] = {0}, g[D];
    for (int j = 0; j < D; j++)
        w_true[j] = rnd(&seed);
    int per = N / p, first = rank * per;
    double *X = malloc((size_t)per * D * sizeof *X), *y = malloc(per * sizeof *y);
    if (X == NULL || y == NULL)
        MPI_Abort(MPI_COMM_WORLD, 1);
    for (int i = 0; i < N; i++) {
        double row[D], t = 0.0;
        for (int j = 0; j < D; j++) {
            row[j] = rnd(&seed);
            t += row[j] * w_true[j];
        }
        t += 0.01 * rnd(&seed);                      /* noise */
        if (i >= first && i < first + per) {
            memcpy(&X[(size_t)(i - first) * D], row, sizeof row);
            y[i - first] = t;
        }
    }
    double loss = 0.0;
    for (int step = 0; step <= STEPS; step++) {
        double local_loss = 0.0;
        memset(g, 0, sizeof g);
        for (int i = 0; i < per; i++) {              /* gradient on my shard */
            double r = -y[i];
            for (int j = 0; j < D; j++)
                r += X[(size_t)i * D + j] * w[j];
            local_loss += r * r;
            for (int j = 0; j < D; j++)
                g[j] += r * X[(size_t)i * D + j];
        }
        MPI_Allreduce(&local_loss, &loss, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
        if (ring)
            ring_allreduce(g, D, rank, p);
        else
            MPI_Allreduce(MPI_IN_PLACE, g, D, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
        for (int j = 0; j < D; j++)                  /* same update everywhere */
            w[j] -= LR * g[j] / N;
        if (rank == 0 && (step == 0 || step == 10 || step == 100 || step == STEPS))
            printf("loss,%s,%d,%d,%.17g\n", ring ? "ring" : "mpi", p, step, loss / N);
    }
    double err = 0.0;
    for (int j = 0; j < D; j++)
        err += (w[j] - w_true[j]) * (w[j] - w_true[j]);
    long max_bytes;
    MPI_Reduce(&bytes_sent, &max_bytes, 1, MPI_LONG, MPI_MAX, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        printf("weights,%s,%d,%.17g,%.17g\n", ring ? "ring" : "mpi", p, w[0], sqrt(err));
        printf("ringbytes,%d,%ld,%ld\n", p, max_bytes / (STEPS + 1),
               p > 1 ? 2L * (p - 1) * 8 * D / p : 0L);
    }
    free(X);
    free(y);
    MPI_Finalize();
    return 0;
}
