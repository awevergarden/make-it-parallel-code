/*
 * exchange.c -- two ranks swap messages of BYTES bytes.
 * Make It Parallel, Chapter 10 (the Bug Hunt).
 *
 * MODE send      both ranks call MPI_Send, then MPI_Recv
 * MODE ssend     both ranks call MPI_Ssend, then MPI_Recv
 * MODE sendrecv  both ranks call MPI_Sendrecv
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o exchange exchange.c
 * Run:    mpirun -np 2 ./exchange send|ssend|sendrecv BYTES
 */
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    if (argc != 3 || size != 2) {
        if (rank == 0)
            fprintf(stderr, "usage: mpirun -np 2 %s send|ssend|sendrecv BYTES\n",
                    argv[0]);
        MPI_Finalize();
        return 1;
    }
    int bytes = atoi(argv[2]);
    char *out = malloc(bytes), *in = malloc(bytes);
    if (out == NULL || in == NULL)
        MPI_Abort(MPI_COMM_WORLD, 1);
    memset(out, 'a' + rank, bytes);
    int other = 1 - rank;

    if (strcmp(argv[1], "send") == 0) {
        MPI_Send(out, bytes, MPI_CHAR, other, 0, MPI_COMM_WORLD);
        MPI_Recv(in, bytes, MPI_CHAR, other, 0, MPI_COMM_WORLD,
                 MPI_STATUS_IGNORE);
    } else if (strcmp(argv[1], "ssend") == 0) {
        MPI_Ssend(out, bytes, MPI_CHAR, other, 0, MPI_COMM_WORLD);
        MPI_Recv(in, bytes, MPI_CHAR, other, 0, MPI_COMM_WORLD,
                 MPI_STATUS_IGNORE);
    } else {
        MPI_Sendrecv(out, bytes, MPI_CHAR, other, 0,
                     in, bytes, MPI_CHAR, other, 0,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    }
    if (rank == 0)
        printf("exchanged %d bytes: ok\n", bytes);
    free(out);
    free(in);
    MPI_Finalize();
    return 0;
}
