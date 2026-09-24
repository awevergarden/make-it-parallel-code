/*
 * tobcast.c -- totally ordered multicast with Lamport clocks: every
 * replica of SimQueue's job log delivers submissions in the same order.
 * Make It Parallel, Chapter 16.
 *
 * Each of P processes submits JOBS jobs, multicasting each one with its
 * Lamport timestamp. Every process holds received jobs in a queue
 * sorted by (timestamp, sender) and acknowledges each to everyone --
 * including the sender, which acknowledges its own jobs too. A
 * job is delivered when it heads the queue and this process has heard
 * something stamped later from every process (MPI messages between two
 * processes arrive in order, so nothing earlier can still be coming).
 * Random pauses vary the interleaving. Rank 0 checks that all delivery
 * orders are identical.
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o tobcast tobcast.c
 * Run:    mpirun -np P ./tobcast [JOBS] [SEED]
 */
#define _POSIX_C_SOURCE 200809L
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAXP 16
#define MAXJOBS 256
enum { JOB, ACK };

struct job { long ts; int sender, seq, acks; };

static long L;                        /* Lamport clock */
static long latest[MAXP];             /* newest timestamp heard from each */
static struct job queue[MAXP * MAXJOBS];
static int qlen;
static long sent_msgs;

static void pause_randomly(unsigned *s)
{
    *s = *s * 1103515245u + 12345u;
    struct timespec t = {0, (long)((*s >> 16) % 200) * 1000};  /* 0-200 us */
    nanosleep(&t, NULL);
}

static void multicast(int p, int rank, long *msg)
{
    for (int k = 0; k < p; k++)
        if (k != rank) {
            MPI_Send(msg, 4, MPI_LONG, k, 0, MPI_COMM_WORLD);
            sent_msgs++;
        }
}

/* Insert a job in (timestamp, sender) order. */
static void enqueue(long ts, int sender, int seq)
{
    int i = qlen++;
    while (i > 0 && (queue[i - 1].ts > ts || (queue[i - 1].ts == ts && queue[i - 1].sender > sender))) {
        queue[i] = queue[i - 1];
        i--;
    }
    queue[i] = (struct job){ts, sender, seq, 0};
}

static void handle(long *m, int from, int p, int rank)
{
    L = (L > m[1] ? L : m[1]) + 1;
    if (m[1] > latest[from])
        latest[from] = m[1];
    if (m[0] == JOB) {
        enqueue(m[1], (int)m[2], (int)m[3]);
        long ack[4] = {ACK, ++L, m[2], m[3]};    /* acknowledge to everyone */
        latest[rank] = ack[1];
        multicast(p, rank, ack);
    }
}

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank, p;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &p);
    int jobs = argc > 1 ? atoi(argv[1]) : 20;
    unsigned seed = (argc > 2 ? (unsigned)atoi(argv[2]) : 1u) * 7919u + (unsigned)rank;
    if (p > MAXP || jobs > MAXJOBS) {
        MPI_Finalize();
        return 1;
    }
    int *order = malloc(2 * p * jobs * sizeof *order), delivered = 0, submitted = 0;
    if (order == NULL)
        MPI_Abort(MPI_COMM_WORLD, 1);
    for (int k = 0; k < p; k++)
        latest[k] = -1;
    while (delivered < p * jobs) {
        if (submitted < jobs) {                   /* submit my next job */
            pause_randomly(&seed);
            long m[4] = {JOB, ++L, rank, submitted};
            latest[rank] = L;
            enqueue(m[1], rank, submitted);
            multicast(p, rank, m);
            long ack[4] = {ACK, ++L, rank, submitted};   /* ack my own job too */
            latest[rank] = L;
            multicast(p, rank, ack);
            submitted++;
        }
        int flag = 1;
        while (flag) {                            /* absorb what has arrived */
            MPI_Status st;
            MPI_Iprobe(MPI_ANY_SOURCE, 0, MPI_COMM_WORLD, &flag, &st);
            if (!flag && submitted == jobs) {
                int ready = qlen > 0;             /* nothing to send: wait */
                for (int k = 0; k < p && ready; k++)
                    if (k != rank && latest[k] <= queue[0].ts) ready = 0;
                if (!ready) {
                    MPI_Probe(MPI_ANY_SOURCE, 0, MPI_COMM_WORLD, &st);
                    flag = 1;
                }
            }
            if (!flag)
                break;
            long m[4];
            MPI_Recv(m, 4, MPI_LONG, st.MPI_SOURCE, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            handle(m, st.MPI_SOURCE, p, rank);
        }
        /* deliver from the head while everyone has moved past it */
        while (qlen > 0) {
            int ready = 1;
            for (int k = 0; k < p; k++)
                if (k != rank && latest[k] <= queue[0].ts) ready = 0;
            if (!ready)
                break;
            order[2 * delivered] = queue[0].sender;
            order[2 * delivered + 1] = queue[0].seq;
            delivered++;
            memmove(queue, queue + 1, --qlen * sizeof *queue);
        }
    }
    /* compare every replica's delivery order with rank 0's */
    int *all = rank == 0 ? malloc((size_t)2 * p * jobs * p * sizeof *all) : NULL;
    MPI_Gather(order, 2 * p * jobs, MPI_INT, all, 2 * p * jobs, MPI_INT, 0, MPI_COMM_WORLD);
    long total_sent;
    MPI_Reduce(&sent_msgs, &total_sent, 1, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        int same = 1, interleaved = 0;
        for (int k = 1; k < p; k++)
            same &= memcmp(all, all + (size_t)2 * p * jobs * k, 2 * p * jobs * sizeof *all) == 0;
        for (int d = 1; d < p * jobs; d++)          /* senders alternate? */
            interleaved += all[2 * d] != all[2 * (d - 1)];
        printf("processes,%d\njobs_each,%d\nall_orders_identical,%s\nsender_changes,%d\n"
               "messages_sent,%ld\nfirst_ten,", p, jobs, same ? "yes" : "NO", interleaved,
               total_sent);
        for (int d = 0; d < 10 && d < p * jobs; d++)
            printf("%s%d.%d", d ? " " : "", all[2 * d], all[2 * d + 1]);
        printf("\n");
        free(all);
    }
    free(order);
    MPI_Finalize();
    return 0;
}
