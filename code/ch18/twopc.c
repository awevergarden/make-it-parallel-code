/*
 * twopc.c -- two-phase commit, including the case where it blocks.
 * Make It Parallel, Chapter 18.
 *
 * Rank 0 coordinates a transaction across ranks 1..P-1 (say, SimQueue
 * recording a job's result in several stores at once). Phase 1: the
 * coordinator sends PREPARE; each participant votes YES or NO. Phase 2:
 * COMMIT if all voted YES, otherwise ABORT. Scenarios:
 *   commit   everyone votes yes
 *   abort    the last participant votes no
 *   crash    the coordinator collects the votes, then stops for 2 s
 *            before announcing -- as if it had crashed and recovered
 * A participant that voted YES may not decide alone. If no decision
 * arrives within 0.5 s, it asks the other participants; if none of them
 * knows the outcome either, it is BLOCKED and must keep waiting.
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o twopc twopc.c
 * Run:    mpirun -np P ./twopc commit|abort|crash
 */
#define _POSIX_C_SOURCE 200809L
#include <mpi.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

enum { PREPARE = 1, VOTE, DECISION, ASK, ANSWER };
enum { NO = 0, YES = 1, COMMIT = 2, ABORT = 3, UNKNOWN = 4 };

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank, p;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &p);
    const char *mode = argc > 1 ? argv[1] : "commit";
    int crash = strcmp(mode, "crash") == 0;
    long msgs = 0;
    double t0 = MPI_Wtime();
    int v;
    if (rank == 0) {
        for (int k = 1; k < p; k++, msgs++)
            MPI_Send(&v, 1, MPI_INT, k, PREPARE, MPI_COMM_WORLD);
        int all_yes = 1;
        for (int k = 1; k < p; k++) {
            MPI_Recv(&v, 1, MPI_INT, MPI_ANY_SOURCE, VOTE, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            all_yes &= v == YES;
        }
        if (crash) {                               /* down between the phases */
            struct timespec d = {2, 0};
            nanosleep(&d, NULL);
        }
        int decision = all_yes ? COMMIT : ABORT;
        for (int k = 1; k < p; k++, msgs++)
            MPI_Send(&decision, 1, MPI_INT, k, DECISION, MPI_COMM_WORLD);
    } else {
        MPI_Recv(&v, 1, MPI_INT, 0, PREPARE, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        int vote = (strcmp(mode, "abort") == 0 && rank == p - 1) ? NO : YES;
        MPI_Send(&vote, 1, MPI_INT, 0, VOTE, MPI_COMM_WORLD);
        msgs++;
        int decision = vote == NO ? ABORT : UNKNOWN;   /* a NO voter may abort at once */
        int asked = 0, blocked = 0;
        double blocked_since = 0;
        while (decision == UNKNOWN || decision == ABORT) {
            int flag;
            MPI_Status st;
            MPI_Iprobe(MPI_ANY_SOURCE, MPI_ANY_TAG, MPI_COMM_WORLD, &flag, &st);
            if (flag) {
                MPI_Recv(&v, 1, MPI_INT, st.MPI_SOURCE, st.MPI_TAG, MPI_COMM_WORLD,
                         MPI_STATUS_IGNORE);
                if (st.MPI_TAG == DECISION) {
                    decision = v;
                    break;
                }
                if (st.MPI_TAG == ASK) {           /* a peer asks what I know */
                    MPI_Send(&decision, 1, MPI_INT, st.MPI_SOURCE, ANSWER, MPI_COMM_WORLD);
                    msgs++;
                } else if (st.MPI_TAG == ANSWER && v != UNKNOWN && decision == UNKNOWN)
                    decision = v;
                continue;
            }
            if (!asked && decision == UNKNOWN && MPI_Wtime() - t0 > 0.5) {
                for (int k = 1; k < p; k++)        /* cooperative termination */
                    if (k != rank) {
                        MPI_Send(&v, 1, MPI_INT, k, ASK, MPI_COMM_WORLD);
                        msgs++;
                    }
                asked = 1;
                blocked_since = MPI_Wtime();
            }
            if (asked && decision == UNKNOWN && MPI_Wtime() - blocked_since > 0.3)
                blocked = 1;                       /* nobody knows: must wait */
        }
        double waited = MPI_Wtime() - t0;
        printf("participant,%d,%s,%s,%.2f\n", rank, decision == COMMIT ? "commit" : "abort",
               blocked ? "was_blocked" : "not_blocked", waited);
    }
    long total;
    MPI_Reduce(&msgs, &total, 1, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0)
        printf("coordinator,%s,messages,%ld\n", mode, total);
    MPI_Finalize();
    return 0;
}
