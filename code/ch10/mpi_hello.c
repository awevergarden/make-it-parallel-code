/*
 * mpi_hello.c -- every process reports its rank.
 * Make It Parallel, Chapter 10.
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o mpi_hello mpi_hello.c
 * Run:    mpirun -np 4 ./mpi_hello
 */
#include <mpi.h>
#include <stdio.h>

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    printf("hello from rank %d of %d\n", rank, size);
    MPI_Finalize();
    return 0;
}
