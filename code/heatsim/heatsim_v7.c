/*
 * heatsim_v7.c -- HeatSim version 7 (MPI + OpenMP, 2D blocks)
 * Make It Parallel, companion code (Chapter 12).
 *
 * The processes form a 2D grid (MPI_Dims_create, MPI_Cart_create), and
 * each owns a rectangular block of the plate plus a one-cell halo on
 * all four sides. Rows of the halo are sent directly; columns use an
 * MPI_Type_vector. Inside each process, OpenMP threads share the rows;
 * only the main thread calls MPI (MPI_THREAD_FUNNELED). Results are
 * bit-identical to version 1 for any layout and thread count.
 *
 * Build:  mpicc -std=c17 -O2 -fopenmp -Wall -Wextra \
 *             -o heatsim_v7 heatsim_v7.c
 * Run:    OMP_NUM_THREADS=T mpirun -np P ./heatsim_v7 N STEPS [SNAP ...]
 *         HEATSIM_DIMS=RxC chooses the process grid (e.g. 4x1 for rows).
 */
#include <errno.h>
#include <mpi.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define HOT  100.0
#define COLD   0.0

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

struct block {
    int n;                        /* global grid width                  */
    int rows, cols;               /* owned interior cells               */
    int r0, c0;                   /* global index of first owned cell   */
    int w;                        /* local row length: cols + 2         */
    int up, down, left, right;    /* neighbors (or MPI_PROC_NULL)       */
    MPI_Comm grid;
    MPI_Datatype column;          /* one halo column: rows values       */
    long bytes_per_step;          /* halo bytes this process sends      */
};

/* Split `len` interior cells among `parts`; part k starts at 1 + ... */
static void split(int len, int parts, int k, int *first, int *count)
{
    *first = 1 + (int)((long)k * len / parts);
    *count = 1 + (int)((long)(k + 1) * len / parts) - *first;
}

static void set_edges(const struct block *b, double *g)
{
    for (int i = 0; i < b->rows + 2; i++)
        for (int j = 0; j < b->w; j++) {
            int gi = b->r0 - 1 + i, gj = b->c0 - 1 + j;
            if (gi == 0)
                g[i * b->w + j] = HOT;
            else if (gi == b->n - 1 || gj == 0 || gj == b->n - 1)
                g[i * b->w + j] = COLD;
        }
}

/* Version 3's kernel, on a local row of width w with cols interior cells. */
static void update_row(const double *restrict src, double *restrict dst,
                       int i, int w, int cols)
{
    #pragma omp simd
    for (int j = 1; j <= cols; j++)
        dst[i * w + j] = 0.25 * (src[(i - 1) * w + j]
                               + src[(i + 1) * w + j]
                               + src[i * w + j - 1]
                               + src[i * w + j + 1]);
}

static void exchange_halos(const struct block *b, double *g)
{
    int w = b->w, r = b->rows, c = b->cols;
    MPI_Comm comm = b->grid;
    /* rows: first row up / bottom halo from below, and the reverse */
    MPI_Sendrecv(&g[1 * w + 1], c, MPI_DOUBLE, b->up, 0,
                 &g[(r + 1) * w + 1], c, MPI_DOUBLE, b->down, 0,
                 comm, MPI_STATUS_IGNORE);
    MPI_Sendrecv(&g[r * w + 1], c, MPI_DOUBLE, b->down, 1,
                 &g[0 * w + 1], c, MPI_DOUBLE, b->up, 1,
                 comm, MPI_STATUS_IGNORE);
    /* columns: first column left / right halo from the right, and back */
    MPI_Sendrecv(&g[1 * w + 1], 1, b->column, b->left, 2,
                 &g[1 * w + c + 1], 1, b->column, b->right, 2,
                 comm, MPI_STATUS_IGNORE);
    MPI_Sendrecv(&g[1 * w + c], 1, b->column, b->right, 3,
                 &g[1 * w + 0], 1, b->column, b->left, 3,
                 comm, MPI_STATUS_IGNORE);
}

static void run_steps(struct block *b, double **cur_p, double **next_p,
                      long steps)
{
    double *cur = *cur_p, *next = *next_p;
    #pragma omp parallel default(none) shared(b, steps) \
                         firstprivate(cur, next)
    {
        for (long s = 0; s < steps; s++) {
            #pragma omp masked
            exchange_halos(b, cur);          /* main thread only */
            #pragma omp barrier
            #pragma omp for schedule(static)
            for (int i = 1; i <= b->rows; i++)
                update_row(cur, next, i, b->w, b->cols);
            double *tmp = cur;               /* implicit barrier above */
            cur = next;
            next = tmp;
        }
    }
    if (steps % 2 == 1) {
        double *tmp = *cur_p;
        *cur_p = *next_p;
        *next_p = tmp;
    }
}

/* Assemble the whole grid on rank 0 (NULL elsewhere). */
static double *gather_grid(const struct block *b, const double *g,
                           int rank, int size)
{
    int n = b->n, count = b->rows * b->cols;
    double *mine = malloc((size_t)count * sizeof *mine);
    if (mine == NULL)
        MPI_Abort(MPI_COMM_WORLD, 1);
    for (int i = 0; i < b->rows; i++)
        memcpy(&mine[(size_t)i * b->cols], &g[(i + 1) * b->w + 1],
               b->cols * sizeof *mine);
    int info[4] = {b->r0, b->c0, b->rows, b->cols}, *all = NULL;
    int *counts = NULL, *displs = NULL;
    double *packed = NULL, *grid = NULL;
    if (rank == 0) {
        all = malloc(4 * size * sizeof *all);
        counts = malloc(size * sizeof *counts);
        displs = malloc(size * sizeof *displs);
        if (all == NULL || counts == NULL || displs == NULL)
            MPI_Abort(MPI_COMM_WORLD, 1);
    }
    MPI_Gather(info, 4, MPI_INT, all, 4, MPI_INT, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        long total = 0;
        for (int k = 0; k < size; k++) {
            counts[k] = all[4 * k + 2] * all[4 * k + 3];
            displs[k] = (int)total;
            total += counts[k];
        }
        packed = malloc((size_t)total * sizeof *packed);
        grid = calloc((size_t)n * n, sizeof *grid);
        if (packed == NULL || grid == NULL)
            MPI_Abort(MPI_COMM_WORLD, 1);
    }
    MPI_Gatherv(mine, count, MPI_DOUBLE, packed, counts, displs,
                MPI_DOUBLE, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        for (int j = 0; j < n; j++) {             /* fixed edges */
            grid[j] = HOT;
            grid[(size_t)(n - 1) * n + j] = COLD;
        }
        for (int k = 0; k < size; k++)            /* place each block */
            for (int i = 0; i < all[4 * k + 2]; i++)
                memcpy(&grid[(size_t)(all[4 * k] + i) * n + all[4 * k + 1]],
                       &packed[displs[k] + (size_t)i * all[4 * k + 3]],
                       all[4 * k + 3] * sizeof *grid);
    }
    free(mine); free(all); free(counts); free(displs); free(packed);
    return grid;
}

int main(int argc, char *argv[])
{
    int provided;
    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    if (provided < MPI_THREAD_FUNNELED) {
        if (rank == 0)
            fprintf(stderr, "error: MPI lacks MPI_THREAD_FUNNELED\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    long n_arg, steps;
    if (argc < 3 || parse_long(argv[1], 3, 46340, &n_arg) != 0
        || parse_long(argv[2], 0, 1000000000L, &steps) != 0) {
        if (rank == 0)
            fprintf(stderr, "usage: mpirun -np P %s N STEPS [SNAPSHOT_STEP ...]\n",
                    argv[0]);
        MPI_Finalize();
        return 1;
    }
    int dims[2] = {0, 0}, periods[2] = {0, 0};
    const char *want = getenv("HEATSIM_DIMS");
    if (want != NULL && (sscanf(want, "%dx%d", &dims[0], &dims[1]) != 2
                         || dims[0] * dims[1] != size)) {
        if (rank == 0)
            fprintf(stderr, "error: HEATSIM_DIMS=%s doesn't match %d processes\n",
                    want, size);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    MPI_Dims_create(size, 2, dims);
    if (dims[0] > n_arg - 2 || dims[1] > n_arg - 2) {
        if (rank == 0)
            fprintf(stderr, "error: grid too small for %dx%d processes\n",
                    dims[0], dims[1]);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    struct block b = {.n = (int)n_arg};
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 0, &b.grid);
    int coords[2];
    MPI_Cart_coords(b.grid, rank, 2, coords);
    MPI_Cart_shift(b.grid, 0, 1, &b.up, &b.down);
    MPI_Cart_shift(b.grid, 1, 1, &b.left, &b.right);
    split(b.n - 2, dims[0], coords[0], &b.r0, &b.rows);
    split(b.n - 2, dims[1], coords[1], &b.c0, &b.cols);
    b.w = b.cols + 2;
    MPI_Type_vector(b.rows, 1, b.w, MPI_DOUBLE, &b.column);
    MPI_Type_commit(&b.column);
    b.bytes_per_step = 8L * ((b.up != MPI_PROC_NULL) * b.cols
                           + (b.down != MPI_PROC_NULL) * b.cols
                           + (b.left != MPI_PROC_NULL) * b.rows
                           + (b.right != MPI_PROC_NULL) * b.rows);

    size_t cells = (size_t)(b.rows + 2) * b.w;
    double *cur = calloc(cells, sizeof *cur), *next = calloc(cells, sizeof *next);
    if (cur == NULL || next == NULL)
        MPI_Abort(MPI_COMM_WORLD, 1);
    set_edges(&b, cur);
    set_edges(&b, next);

    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();
    long done = 0;
    char path[64];
    for (int a = 3; a <= argc; a++) {
        long target = steps;
        if (a < argc && parse_long(argv[a], done, steps, &target) != 0)
            MPI_Abort(MPI_COMM_WORLD, 1);
        run_steps(&b, &cur, &next, target - done);
        done = target;
        if (a < argc) {
            double *grid = gather_grid(&b, cur, rank, size);
            snprintf(path, sizeof path, "snap_%ld.bin", done);
            if (rank == 0) {
                FILE *f = fopen(path, "wb");
                if (f == NULL || fwrite(grid, sizeof *grid, (size_t)b.n * b.n, f)
                                     != (size_t)b.n * b.n || fclose(f) != 0)
                    MPI_Abort(MPI_COMM_WORLD, 1);
            }
            free(grid);
        }
    }
    MPI_Barrier(MPI_COMM_WORLD);
    double elapsed = MPI_Wtime() - t0;

    long max_bytes, total_bytes;
    MPI_Reduce(&b.bytes_per_step, &max_bytes, 1, MPI_LONG, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&b.bytes_per_step, &total_bytes, 1, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    double *grid = gather_grid(&b, cur, rank, size);
    if (rank == 0) {
        int n = b.n;
        double updates = (double)(n - 2) * (n - 2) * (double)steps;
        printf("center temperature after %ld steps: %.4f C\n",
               steps, grid[(size_t)(n / 2) * n + n / 2]);
        printf("time: %.6f s, %.1f million cell updates per second, "
               "%d processes (%dx%d), %d threads each\n", elapsed,
               elapsed > 0 ? updates / elapsed / 1e6 : 0.0, size, dims[0],
               dims[1], omp_get_max_threads());
        printf("halo bytes per step: max %ld per process, total %ld\n",
               max_bytes, total_bytes);
    }
    free(grid); free(cur); free(next);
    MPI_Type_free(&b.column);
    MPI_Comm_free(&b.grid);
    MPI_Finalize();
    return 0;
}
