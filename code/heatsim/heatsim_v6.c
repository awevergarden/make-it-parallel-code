/*
 * heatsim_v6.c -- HeatSim version 6 (MPI)
 * Make It Parallel, companion code (Chapter 10).
 *
 * The interior rows are divided into one contiguous block per process.
 * Each process stores its block plus two halo rows: copies of the
 * neighboring processes' edge rows, refreshed with MPI_Sendrecv before
 * every step. The update kernel is version 3's. Results are
 * bit-identical to version 1 for any number of processes.
 *
 * Build:  mpicc -std=c17 -O2 -fopenmp-simd -Wall -Wextra \
 *             -o heatsim_v6 heatsim_v6.c
 * Run:    mpirun -np 4 ./heatsim_v6 N STEPS [SNAPSHOT_STEP ...]
 *         (same arguments as version 1; rank 0 prints and writes)
 */
#include <errno.h>
#include <mpi.h>
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

/* Version 3's kernel: update row i of dst from rows i-1..i+1 of src. */
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

/* This process's share of the grid. Local row 0 and row rows + 1 are
   halos; local rows 1..rows hold global rows first..first + rows - 1. */
struct block {
    int n, rows, first;          /* grid width, owned rows, first global row */
    int up, down;                /* neighbor ranks or MPI_PROC_NULL */
    double *cur, *next;          /* (rows + 2) x n each */
};

/* Set the fixed edges that fall inside this block, in both arrays. */
static void set_edges(struct block *b)
{
    for (int k = 0; k < 2; k++) {
        double *g = k ? b->next : b->cur;
        for (int i = 0; i < b->rows + 2; i++) {
            int gi = b->first - 1 + i;             /* global row */
            for (int j = 0; j < b->n; j++) {
                if (gi == 0)
                    g[i * b->n + j] = HOT;          /* top edge    */
                else if (gi == b->n - 1 || j == 0 || j == b->n - 1)
                    g[i * b->n + j] = COLD;         /* other edges */
            }
        }
    }
}

/* Refresh both halo rows of cur from the neighbors. */
static void exchange_halos(struct block *b)
{
    int n = b->n, r = b->rows;
    double *g = b->cur;
    /* send my first row up; receive my bottom halo from below */
    MPI_Sendrecv(&g[1 * n], n, MPI_DOUBLE, b->up, 0,
                 &g[(r + 1) * n], n, MPI_DOUBLE, b->down, 0,
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    /* send my last row down; receive my top halo from above */
    MPI_Sendrecv(&g[r * n], n, MPI_DOUBLE, b->down, 1,
                 &g[0 * n], n, MPI_DOUBLE, b->up, 1,
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
}

static void run_steps(struct block *b, long steps)
{
    for (long s = 0; s < steps; s++) {
        exchange_halos(b);
        for (int i = 1; i <= b->rows; i++)
            update_row(b->cur, b->next, i, b->n);
        double *tmp = b->cur;
        b->cur = b->next;
        b->next = tmp;
    }
}

/* Assemble the whole grid on rank 0 (NULL elsewhere). */
static double *gather_grid(const struct block *b, int rank, int size)
{
    int n = b->n;
    double *grid = NULL;
    int *counts = NULL, *displs = NULL;
    if (rank == 0) {
        grid = calloc((size_t)n * n, sizeof *grid);
        counts = malloc(size * sizeof *counts);
        displs = malloc(size * sizeof *displs);
        if (grid == NULL || counts == NULL || displs == NULL)
            MPI_Abort(MPI_COMM_WORLD, 1);
        for (int k = 0; k < size; k++) {
            int f = 1 + (int)((long)k * (n - 2) / size);
            int l = 1 + (int)((long)(k + 1) * (n - 2) / size);
            counts[k] = (l - f) * n;
            displs[k] = f * n;
        }
        for (int j = 0; j < n; j++) {               /* fixed edge rows */
            grid[j] = HOT;
            grid[(size_t)(n - 1) * n + j] = COLD;
        }
    }
    MPI_Gatherv(&b->cur[n], b->rows * n, MPI_DOUBLE, grid, counts, displs,
                MPI_DOUBLE, 0, MPI_COMM_WORLD);
    free(counts);
    free(displs);
    return grid;
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
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    long n_arg, steps;
    if (argc < 3 || parse_long(argv[1], 3, 46340, &n_arg) != 0
        || parse_long(argv[2], 0, 1000000000L, &steps) != 0
        || size > n_arg - 2) {
        if (rank == 0)
            fprintf(stderr, "usage: mpirun -np P %s N STEPS [SNAPSHOT_STEP ...]\n"
                    "       3 <= N <= 46340, P <= N - 2\n", argv[0]);
        MPI_Finalize();
        return 1;
    }
    struct block b;
    b.n = (int)n_arg;
    b.first = 1 + (int)((long)rank * (b.n - 2) / size);
    b.rows = 1 + (int)((long)(rank + 1) * (b.n - 2) / size) - b.first;
    b.up = rank > 0 ? rank - 1 : MPI_PROC_NULL;
    b.down = rank < size - 1 ? rank + 1 : MPI_PROC_NULL;
    b.cur = calloc((size_t)(b.rows + 2) * b.n, sizeof *b.cur);
    b.next = calloc((size_t)(b.rows + 2) * b.n, sizeof *b.next);
    if (b.cur == NULL || b.next == NULL) {
        fprintf(stderr, "rank %d: out of memory\n", rank);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    set_edges(&b);

    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();
    long done = 0;
    char path[64];
    for (int a = 3; a <= argc; a++) {          /* segments between snapshots */
        long target = steps;
        if (a < argc && parse_long(argv[a], done, steps, &target) != 0) {
            if (rank == 0)
                fprintf(stderr, "error: bad snapshot step %s\n", argv[a]);
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        run_steps(&b, target - done);
        done = target;
        if (a < argc) {
            double *grid = gather_grid(&b, rank, size);
            snprintf(path, sizeof path, "snap_%ld.bin", done);
            if (rank == 0 && write_grid(path, grid, b.n) != 0) {
                perror(path);
                MPI_Abort(MPI_COMM_WORLD, 1);
            }
            free(grid);
        }
    }
    MPI_Barrier(MPI_COMM_WORLD);
    double elapsed = MPI_Wtime() - t0;

    double *grid = gather_grid(&b, rank, size);
    if (rank == 0) {
        int n = b.n;
        double updates = (double)(n - 2) * (n - 2) * (double)steps;
        printf("center temperature after %ld steps: %.4f C\n",
               steps, grid[(size_t)(n / 2) * n + n / 2]);
        printf("time: %.6f s, %.1f million cell updates per second, "
               "%d processes\n", elapsed,
               elapsed > 0 ? updates / elapsed / 1e6 : 0.0, size);
    }
    free(grid);
    free(b.cur);
    free(b.next);
    MPI_Finalize();
    return 0;
}
