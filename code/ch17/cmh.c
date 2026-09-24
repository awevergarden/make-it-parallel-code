/*
 * cmh.c -- the Chandy-Misra-Haas probe algorithm for deadlock detection.
 * Make It Parallel, Chapter 17.
 *
 * Six processes are blocked according to a planted wait-for graph:
 *   0 -> 1 -> 2 -> 0   (a cycle: deadlock)
 *   3 -> 4 -> 1        (waiting on the cycle, but not in it)
 *   5                  (not waiting)
 * With the argument "nocycle", the edge 2 -> 0 is removed.
 * Every blocked process starts a detection: it sends a probe
 * (initiator, sender, receiver) along each edge it waits on. A blocked
 * process forwards the first probe it sees from each initiator along
 * its own edges; a process that is not waiting drops probes. If a probe
 * returns to its initiator, the initiator is deadlocked. Termination:
 * the processes repeatedly compare total messages sent and received.
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o cmh cmh.c
 * Run:    mpirun -np 6 ./cmh [nocycle]
 */
#include <mpi.h>
#include <stdio.h>
#include <string.h>

#define P 6
static int waits[P][P];               /* waits[i][j]: i waits for j */
static long sent, recvd, probes;

static void send_probe(int init, int from, int to)
{
    int m[3] = {init, from, to};
    MPI_Send(m, 3, MPI_INT, to, 0, MPI_COMM_WORLD);
    sent++;
    probes++;
}

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank, p;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &p);
    if (p != P) {
        if (rank == 0) fprintf(stderr, "error: run with %d processes\n", P);
        MPI_Finalize();
        return 1;
    }
    int cycle = !(argc > 1 && strcmp(argv[1], "nocycle") == 0);
    waits[0][1] = waits[1][2] = waits[3][4] = waits[4][1] = 1;
    waits[2][0] = cycle;
    int blocked = 0, seen[P] = {0}, deadlocked = 0;
    for (int j = 0; j < P; j++)
        blocked |= waits[rank][j];
    if (blocked) {                       /* start my own detection */
        seen[rank] = 1;
        for (int j = 0; j < P; j++)
            if (waits[rank][j])
                send_probe(rank, rank, j);
    }
    for (;;) {
        int flag = 1;
        while (flag) {                   /* handle every probe that has arrived */
            MPI_Status st;
            MPI_Iprobe(MPI_ANY_SOURCE, 0, MPI_COMM_WORLD, &flag, &st);
            if (!flag)
                break;
            int m[3];
            MPI_Recv(m, 3, MPI_INT, st.MPI_SOURCE, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            recvd++;
            if (!blocked)
                continue;                /* not waiting: no cycle through me */
            if (m[0] == rank)
                deadlocked = 1;          /* my probe came back */
            else if (!seen[m[0]]) {
                seen[m[0]] = 1;
                for (int j = 0; j < P; j++)
                    if (waits[rank][j])
                        send_probe(m[0], rank, j);
            }
        }
        long mine[2] = {sent, recvd}, all[2];
        MPI_Allreduce(mine, all, 2, MPI_LONG, MPI_SUM, MPI_COMM_WORLD);
        if (all[0] == all[1])            /* nothing still in flight */
            break;
    }
    int flags[P];
    MPI_Gather(&deadlocked, 1, MPI_INT, flags, 1, MPI_INT, 0, MPI_COMM_WORLD);
    long total;
    MPI_Reduce(&probes, &total, 1, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        printf("%s,deadlocked:", cycle ? "cycle" : "nocycle");
        for (int k = 0; k < P; k++)
            if (flags[k])
                printf(" %d", k);
        printf(",probes,%ld\n", total);
    }
    MPI_Finalize();
    return 0;
}
