/*
 * mm_dist.c -- distributed matrix multiplication, four ways.
 * Make It Parallel, Chapter 13.
 *
 *   1d      row blocks of A and C; blocks of B travel around a ring
 *   cannon  sqrt(p) x sqrt(p) grid; skew, then multiply-and-shift
 *   fox     sqrt(p) x sqrt(p) grid; broadcast A along rows, shift B up
 *   summa   any pr x pc grid; broadcast panels of A and B
 *   cannon-overlap  Cannon, with the next shift in flight during each multiply
 *
 * Setting MM_BUG_SKEW=1 skews A to the right instead of the left -- a
 * deliberate bug for Chapter 13's Bug Hunt.
 *
 * A and B hold small integers, so every product and sum is exact in
 * double precision and each process can check its block of C exactly.
 * Each process counts the matrix values it receives.
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o mm_dist mm_dist.c -lm
 * Run:    mpirun -np P ./mm_dist 1d|cannon|fox|summa N [PANEL]
 */
#include <math.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Small integers with no simple period, so a misplaced block changes the
   answer (values made only of i and j patterns can hide such bugs). */
static double a_val(long i, long j) { return (double)((i * 31 + j * 17 + (i * j) % 13) % 11 - 5); }
static double b_val(long i, long j) { return (double)((i * 19 + j * 23 + (i * j) % 7) % 9 - 4); }

static long received;                 /* matrix values this process received */

/* C (m x n) += A (m x k) * B (k x n), all row-major with given strides. */
static void gemm(int m, int n, int k, const double *restrict A, int lda,
                 const double *restrict B, int ldb, double *restrict C, int ldc)
{
    for (int i = 0; i < m; i++)
        for (int p = 0; p < k; p++) {
            double a = A[(size_t)i * lda + p];
            for (int j = 0; j < n; j++)
                C[(size_t)i * ldc + j] += a * B[(size_t)p * ldb + j];
        }
}

static double *alloc(size_t count)
{
    double *x = calloc(count, sizeof *x);
    if (x == NULL)
        MPI_Abort(MPI_COMM_WORLD, 1);
    return x;
}

/* Fill a block whose top-left global element is (r0, c0). */
static void fill(double *X, int rows, int cols, long r0, long c0,
                 double (*f)(long, long))
{
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            X[(size_t)i * cols + j] = f(r0 + i, c0 + j);
}

/* Count wrong entries of a C block against the exact formula. */
static long check(const double *C, int rows, int cols, long r0, long c0, long n)
{
    long bad = 0;
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++) {
            double s = 0.0;
            for (long k = 0; k < n; k++)
                s += a_val(r0 + i, k) * b_val(k, c0 + j);
            bad += C[(size_t)i * cols + j] != s;
        }
    return bad;
}

/* ---------------------------------------------------------------- 1D ring */
static long mm_1d(int n, int rank, int p)
{
    int rows = n / p;
    double *A = alloc((size_t)rows * n), *B = alloc((size_t)rows * n);
    double *C = alloc((size_t)rows * n);
    fill(A, rows, n, (long)rank * rows, 0, a_val);
    fill(B, rows, n, (long)rank * rows, 0, b_val);   /* my rows of B */
    int from = (rank + 1) % p, to = (rank - 1 + p) % p;
    for (int s = 0; s < p; s++) {
        int owner = (rank + s) % p;          /* whose rows of B I hold now */
        gemm(rows, n, rows, &A[(size_t)owner * rows], n, B, n, C, n);
        if (s < p - 1) {
            MPI_Sendrecv_replace(B, rows * n, MPI_DOUBLE, to, 0, from, 0,
                                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            received += (long)rows * n;
        }
    }
    long bad = check(C, rows, n, (long)rank * rows, 0, n);
    free(A); free(B); free(C);
    return bad;
}

/* ------------------------------------------------------ Cannon and Fox */
static long mm_square(int n, int rank, int p, int fox, int overlap)
{
    int q = (int)lround(sqrt((double)p)), b = n / q;
    int dims[2] = {q, q}, periods[2] = {1, 1}, c[2];
    MPI_Comm grid, row;
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 0, &grid);
    MPI_Comm_rank(grid, &rank);
    MPI_Cart_coords(grid, rank, 2, c);
    MPI_Comm_split(grid, c[0], c[1], &row);          /* my process row */
    double *A = alloc((size_t)b * b), *B = alloc((size_t)b * b);
    double *C = alloc((size_t)b * b), *T = alloc((size_t)b * b);
    double *A2 = alloc((size_t)b * b), *B2 = alloc((size_t)b * b);
    int bug = getenv("MM_BUG_SKEW") != NULL;
    fill(A, b, b, (long)c[0] * b, (long)c[1] * b, a_val);
    fill(B, b, b, (long)c[0] * b, (long)c[1] * b, b_val);
    int src, dst, up, down, left, right;
    MPI_Cart_shift(grid, 0, -1, &down, &up);         /* B moves up    */
    MPI_Cart_shift(grid, 1, -1, &right, &left);      /* A moves left  */
    if (!fox) {                                      /* Cannon: skew  */
        int dir = bug ? +1 : -1;                     /* the bug: wrong way */
        MPI_Cart_shift(grid, 1, dir * c[0], &src, &dst);  /* A left by row */
        if (c[0] > 0) {
            MPI_Sendrecv_replace(A, b * b, MPI_DOUBLE, dst, 1, src, 1, grid,
                                 MPI_STATUS_IGNORE);
            received += (long)b * b;
        }
        MPI_Cart_shift(grid, 0, -c[1], &src, &dst);  /* B up by column */
        if (c[1] > 0) {
            MPI_Sendrecv_replace(B, b * b, MPI_DOUBLE, dst, 2, src, 2, grid,
                                 MPI_STATUS_IGNORE);
            received += (long)b * b;
        }
    }
    for (int k = 0; k < q; k++) {
        if (fox) {                   /* broadcast A(i, i+k) along row i */
            int root = (c[0] + k) % q;
            if (c[1] == root)
                memcpy(T, A, (size_t)b * b * sizeof *T);
            else
                received += (long)b * b;
            MPI_Bcast(T, b * b, MPI_DOUBLE, root, row);
            gemm(b, b, b, T, b, B, b, C, b);
        } else if (overlap && k < q - 1) {         /* start next shift, then compute */
            MPI_Request req[4];
            MPI_Irecv(A2, b * b, MPI_DOUBLE, right, 5, grid, &req[0]);
            MPI_Irecv(B2, b * b, MPI_DOUBLE, down, 6, grid, &req[1]);
            MPI_Isend(A, b * b, MPI_DOUBLE, left, 5, grid, &req[2]);
            MPI_Isend(B, b * b, MPI_DOUBLE, up, 6, grid, &req[3]);
            gemm(b, b, b, A, b, B, b, C, b);         /* A, B only read */
            MPI_Waitall(4, req, MPI_STATUSES_IGNORE);
            double *t = A; A = A2; A2 = t;
            t = B; B = B2; B2 = t;
            received += 2L * b * b;
            continue;
        } else {
            gemm(b, b, b, A, b, B, b, C, b);
            if (k < q - 1) {
                MPI_Sendrecv_replace(A, b * b, MPI_DOUBLE, left, 3, right, 3,
                                     grid, MPI_STATUS_IGNORE);
                received += (long)b * b;
            }
        }
        if (k < q - 1) {             /* both: shift B up by one */
            MPI_Sendrecv_replace(B, b * b, MPI_DOUBLE, up, 4, down, 4, grid,
                                 MPI_STATUS_IGNORE);
            received += (long)b * b;
        }
    }
    long bad = check(C, b, b, (long)c[0] * b, (long)c[1] * b, n);
    free(A); free(B); free(C); free(T); free(A2); free(B2);
    MPI_Comm_free(&row);
    MPI_Comm_free(&grid);
    return bad;
}

/* ----------------------------------------------------------------- SUMMA */
static long mm_summa(int n, int rank, int p, int panel)
{
    int dims[2] = {0, 0}, periods[2] = {0, 0}, c[2];
    MPI_Dims_create(p, 2, dims);
    int mr = n / dims[0], mc = n / dims[1];          /* my block of C */
    if (panel <= 0 || mr % panel || mc % panel)
        MPI_Abort(MPI_COMM_WORLD, 2);
    MPI_Comm grid, row, col;
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 0, &grid);
    MPI_Comm_rank(grid, &rank);
    MPI_Cart_coords(grid, rank, 2, c);
    int keep_cols[2] = {0, 1}, keep_rows[2] = {1, 0};
    MPI_Cart_sub(grid, keep_cols, &row);             /* along my row    */
    MPI_Cart_sub(grid, keep_rows, &col);             /* along my column */
    double *A = alloc((size_t)mr * mc), *B = alloc((size_t)mr * mc);
    double *C = alloc((size_t)mr * mc);
    double *Ap = alloc((size_t)mr * panel), *Bp = alloc((size_t)panel * mc);
    fill(A, mr, mc, (long)c[0] * mr, (long)c[1] * mc, a_val);
    fill(B, mr, mc, (long)c[0] * mr, (long)c[1] * mc, b_val);
    for (int k = 0; k < n; k += panel) {
        int acol = k / mc, brow = k / mr;            /* owners of the panels */
        if (c[1] == acol)                            /* my columns of A */
            for (int i = 0; i < mr; i++)
                memcpy(&Ap[(size_t)i * panel], &A[(size_t)i * mc + (k - acol * mc)],
                       panel * sizeof *Ap);
        else
            received += (long)mr * panel;
        if (c[0] == brow)                            /* my rows of B */
            memcpy(Bp, &B[(size_t)(k - brow * mr) * mc], (size_t)panel * mc * sizeof *Bp);
        else
            received += (long)panel * mc;
        MPI_Bcast(Ap, mr * panel, MPI_DOUBLE, acol, row);
        MPI_Bcast(Bp, panel * mc, MPI_DOUBLE, brow, col);
        gemm(mr, mc, panel, Ap, panel, Bp, mc, C, mc);
    }
    long bad = check(C, mr, mc, (long)c[0] * mr, (long)c[1] * mc, n);
    free(A); free(B); free(C); free(Ap); free(Bp);
    MPI_Comm_free(&row); MPI_Comm_free(&col); MPI_Comm_free(&grid);
    return bad;
}

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank, p;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &p);
    if (argc < 3) {
        if (rank == 0)
            fprintf(stderr, "usage: %s 1d|cannon|fox|summa N [PANEL]\n", argv[0]);
        MPI_Finalize();
        return 1;
    }
    const char *alg = argv[1];
    int n = atoi(argv[2]);
    int q = (int)lround(sqrt((double)p));
    int square = strcmp(alg, "cannon") == 0 || strcmp(alg, "fox") == 0
                 || strcmp(alg, "cannon-overlap") == 0;
    if (n < 1 || (strcmp(alg, "1d") == 0 && n % p) || (square && (q * q != p || n % q))) {
        if (rank == 0)
            fprintf(stderr, "error: N must divide evenly (and P be square for %s)\n", alg);
        MPI_Finalize();
        return 1;
    }
    double t0 = MPI_Wtime();
    long bad = strcmp(alg, "1d") == 0 ? mm_1d(n, rank, p)
             : square ? mm_square(n, rank, p, strcmp(alg, "fox") == 0,
                                  strcmp(alg, "cannon-overlap") == 0)
             : mm_summa(n, rank, p, argc > 3 ? atoi(argv[3]) : 60);
    double t = MPI_Wtime() - t0;
    long total_bad, max_recv, sum_recv;
    MPI_Reduce(&bad, &total_bad, 1, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(&received, &max_recv, 1, MPI_LONG, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&received, &sum_recv, 1, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0)
        printf("%s,%d,%d,%ld,%ld,%ld,%.3f\n", alg, n, p, total_bad, max_recv,
               sum_recv, t);
    MPI_Finalize();
    return 0;
}
