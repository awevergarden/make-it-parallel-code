/*
 * topology.c -- a 2D Cartesian communicator and a column datatype.
 * Make It Parallel, Chapter 10.
 *
 * Part 1: arranges the processes in a 2D grid with MPI_Dims_create
 * and MPI_Cart_create, and prints each rank's coordinates and its
 * neighbors from MPI_Cart_shift (-1 means MPI_PROC_NULL).
 * Part 2: rank 0 sends column 2 of a 4 x 5 row-major matrix to rank 1
 * as ONE message, using MPI_Type_vector to describe the strided layout.
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o topology topology.c
 * Run:    mpirun -np 6 ./topology
 */
#include <mpi.h>
#include <stdio.h>

#define ROWS 4
#define COLS 5

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    /* ---- Part 1: a 2D process grid */
    int dims[2] = {0, 0}, periods[2] = {0, 0};
    MPI_Dims_create(size, 2, dims);          /* e.g. 6 -> 3 x 2 */
    MPI_Comm grid;
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 0, &grid);
    int coords[2], up, down, left, right;
    MPI_Cart_coords(grid, rank, 2, coords);
    MPI_Cart_shift(grid, 0, 1, &up, &down);     /* along dimension 0 */
    MPI_Cart_shift(grid, 1, 1, &left, &right);  /* along dimension 1 */
    printf("rank %d at (%d,%d) of %dx%d: up %d down %d left %d right %d\n",
           rank, coords[0], coords[1], dims[0], dims[1],
           up == MPI_PROC_NULL ? -1 : up, down == MPI_PROC_NULL ? -1 : down,
           left == MPI_PROC_NULL ? -1 : left,
           right == MPI_PROC_NULL ? -1 : right);

    /* ---- Part 2: send one column with a derived datatype */
    MPI_Datatype column;
    MPI_Type_vector(ROWS, 1, COLS, MPI_DOUBLE, &column);  /* 4 blocks of 1, stride 5 */
    MPI_Type_commit(&column);
    if (rank == 0) {
        double a[ROWS * COLS];
        for (int k = 0; k < ROWS * COLS; k++)
            a[k] = k;                        /* a[i][j] = 5i + j */
        MPI_Send(&a[2], 1, column, 1, 0, MPI_COMM_WORLD);
    } else if (rank == 1) {
        double col[ROWS];
        MPI_Recv(col, ROWS, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD,
                 MPI_STATUS_IGNORE);
        printf("rank 1 received column 2: %g %g %g %g\n",
               col[0], col[1], col[2], col[3]);
    }
    MPI_Type_free(&column);
    MPI_Comm_free(&grid);
    MPI_Finalize();
    return 0;
}
