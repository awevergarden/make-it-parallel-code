/*
 * pingpong_mpi.c -- one-way message time between two MPI ranks.
 * Make It Parallel, Chapter 10.
 *
 * Rank 0 sends a message to rank 1, which sends it back, for sizes
 * from 8 bytes to 2 MB. The one-way time is half the round trip.
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o pingpong_mpi pingpong_mpi.c
 * Run:    mpirun -np 2 ./pingpong_mpi     (prints: bytes,microseconds)
 */
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_BYTES (2 * 1024 * 1024)

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    char *buf = malloc(MAX_BYTES);
    if (buf == NULL)
        MPI_Abort(MPI_COMM_WORLD, 1);
    memset(buf, 'x', MAX_BYTES);
    if (rank == 0)
        printf("bytes,microseconds\n");
    for (int n = 8; n <= MAX_BYTES; n *= 4) {
        int reps = n <= 65536 ? 2000 : 100;
        double t0 = 0.0;
        for (int r = -10; r < reps; r++) {      /* 10 warm-up trips */
            if (r == 0)
                t0 = MPI_Wtime();
            if (rank == 0) {
                MPI_Send(buf, n, MPI_CHAR, 1, 0, MPI_COMM_WORLD);
                MPI_Recv(buf, n, MPI_CHAR, 1, 0, MPI_COMM_WORLD,
                         MPI_STATUS_IGNORE);
            } else if (rank == 1) {
                MPI_Recv(buf, n, MPI_CHAR, 0, 0, MPI_COMM_WORLD,
                         MPI_STATUS_IGNORE);
                MPI_Send(buf, n, MPI_CHAR, 0, 0, MPI_COMM_WORLD);
            }
        }
        if (rank == 0)
            printf("%d,%.3f\n", n, (MPI_Wtime() - t0) / reps / 2 * 1e6);
    }
    free(buf);
    MPI_Finalize();
    return 0;
}
