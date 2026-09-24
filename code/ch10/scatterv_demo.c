/*
 * scatterv_demo.c -- divide 10 values among processes as evenly as
 * possible with MPI_Scatterv, and sum them with MPI_Reduce.
 * Make It Parallel, Chapter 10.
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o scatterv_demo scatterv_demo.c
 * Run:    mpirun -np 3 ./scatterv_demo
 */
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

#define N 10

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    int *counts = malloc(size * sizeof *counts);
    int *displs = malloc(size * sizeof *displs);
    if (counts == NULL || displs == NULL)
        MPI_Abort(MPI_COMM_WORLD, 1);
    for (int k = 0; k < size; k++) {         /* Chapter 2's even split */
        displs[k] = k * N / size;
        counts[k] = (k + 1) * N / size - displs[k];
    }
    double all[N];
    if (rank == 0)
        for (int i = 0; i < N; i++)
            all[i] = i + 1;                  /* 1, 2, ..., 10 */
    double mine[N];
    MPI_Scatterv(all, counts, displs, MPI_DOUBLE,
                 mine, counts[rank], MPI_DOUBLE, 0, MPI_COMM_WORLD);
    double part = 0.0;
    for (int i = 0; i < counts[rank]; i++)
        part += mine[i];
    printf("rank %d got %d values starting with %g; partial sum %g\n",
           rank, counts[rank], counts[rank] ? mine[0] : 0.0, part);
    double total;
    MPI_Reduce(&part, &total, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0)
        printf("total %g (expected %d)\n", total, N * (N + 1) / 2);
    free(counts);
    free(displs);
    MPI_Finalize();
    return 0;
}
