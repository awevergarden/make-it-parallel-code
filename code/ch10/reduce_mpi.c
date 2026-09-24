/*
 * reduce_mpi.c -- a sum across processes with MPI_Reduce.
 * Make It Parallel, Chapter 10.
 *
 * Each rank sums its own block of the terms 1/(i+1), i < N; MPI_Reduce
 * adds the partial sums on rank 0. The result changes in the last
 * digits with the number of processes, as in Chapter 8.
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o reduce_mpi reduce_mpi.c
 */
#include <mpi.h>
#include <stdio.h>

#define N 10000000L

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    long lo = rank * N / size, hi = (rank + 1) * N / size;
    double part = 0.0;
    for (long i = lo; i < hi; i++)
        part += 1.0 / (double)(i + 1);
    double total = 0.0;
    MPI_Reduce(&part, &total, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0)
        printf("processes,%d\nsum,%.17g\n", size, total);
    MPI_Finalize();
    return 0;
}
