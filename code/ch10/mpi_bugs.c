/*
 * mpi_bugs.c -- two classic MPI mistakes, one per mode.
 * Make It Parallel, Chapter 10.
 *
 * MODE truncate  rank 1 posts a receive for 5 doubles, rank 0 sends 10
 * MODE barrier   every rank except 0 calls MPI_Barrier
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o mpi_bugs mpi_bugs.c
 * Run:    mpirun -np 2 ./mpi_bugs truncate|barrier
 */
#include <mpi.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    if (argc > 1 && strcmp(argv[1], "truncate") == 0) {
        double buf[10] = {0};
        if (rank == 0)
            MPI_Send(buf, 10, MPI_DOUBLE, 1, 0, MPI_COMM_WORLD);
        else if (rank == 1)
            MPI_Recv(buf, 5, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD,
                     MPI_STATUS_IGNORE);
    } else {
        if (rank != 0)                       /* rank 0 never arrives */
            MPI_Barrier(MPI_COMM_WORLD);
    }
    printf("rank %d finished\n", rank);
    MPI_Finalize();
    return 0;
}
