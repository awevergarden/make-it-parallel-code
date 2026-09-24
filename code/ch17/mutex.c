/*
 * mutex.c -- distributed mutual exclusion, three ways (and none).
 * Make It Parallel, Chapter 17.
 *
 *   none     no coordination at all (the control)
 *   central  rank 0 grants the critical section; others ask it
 *   ra       Ricart-Agrawala: ask everyone, enter after n-1 replies
 *   token    a token circulates around a ring; its holder may enter
 *
 * Each participant enters the critical section ENTRIES times. Inside,
 * it creates a marker file with O_CREAT | O_EXCL, which the operating
 * system makes atomic: if the file already exists, two processes are
 * in the critical section at once, and the violation is counted.
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o mutex mutex.c
 * Run:    mpirun -np P ./mutex none|central|ra|token [ENTRIES] [DIR]
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

enum { REQ = 1, GRANT, RELEASE, REPLY, DONE, TOKEN };

static int rank, p, entries;
static long sent, violations, entered;
static char marker[512];
static unsigned seed;

static void pause_us(int max_us)
{
    seed = seed * 1103515245u + 12345u;
    struct timespec t = {0, (long)((seed >> 16) % (unsigned)max_us) * 1000};
    nanosleep(&t, NULL);
}

static void send(long *m, int n, int to, int tag)
{
    MPI_Send(m, n, MPI_LONG, to, tag, MPI_COMM_WORLD);
    sent++;
}

static void critical_section(void)
{
    int fd = open(marker, O_CREAT | O_EXCL | O_WRONLY, 0644);
    if (fd < 0 && errno == EEXIST)
        violations++;                     /* someone else is inside */
    pause_us(300);                        /* work inside the section */
    if (fd >= 0) {
        close(fd);
        unlink(marker);
    }
    entered++;
}

/* ---- central coordinator (rank 0 grants; ranks 1..p-1 enter) ---- */
static void central(void)
{
    long m[2] = {0, 0};
    if (rank == 0) {
        int queue[64], head = 0, tail = 0, busy = 0, done = 0;
        while (done < p - 1) {
            MPI_Status st;
            MPI_Recv(m, 2, MPI_LONG, MPI_ANY_SOURCE, MPI_ANY_TAG, MPI_COMM_WORLD, &st);
            if (st.MPI_TAG == REQ)
                queue[tail++ % 64] = st.MPI_SOURCE;
            else if (st.MPI_TAG == RELEASE)
                busy = 0;
            else if (st.MPI_TAG == DONE)
                done++;
            if (!busy && head < tail) {
                busy = 1;
                send(m, 2, queue[head++ % 64], GRANT);
            }
        }
        return;
    }
    for (int e = 0; e < entries; e++) {
        pause_us(500);                    /* work outside the section */
        send(m, 2, 0, REQ);
        MPI_Recv(m, 2, MPI_LONG, 0, GRANT, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        critical_section();
        send(m, 2, 0, RELEASE);
    }
    send(m, 2, 0, DONE);
}

/* ---- Ricart-Agrawala ---- */
static void ricart_agrawala(void)
{
    long L = 0, my_ts = 0, m[2];
    int requesting = 0, inside = 0, replies = 0, done = 0, e = 0;
    int *deferred = calloc(p, sizeof *deferred);
    long next_start = 1;                   /* 1: wants to start the next request */
    while (e < entries || done < p - 1) {
        if (next_start && e < entries && !requesting) {
            pause_us(500);                 /* work outside the section */
            my_ts = ++L;
            requesting = 1;
            replies = 0;
            m[0] = my_ts; m[1] = rank;
            for (int k = 0; k < p; k++)
                if (k != rank)
                    send(m, 2, k, REQ);
            next_start = 0;
        }
        if (requesting && replies == p - 1) {
            inside = 1;
            critical_section();
            inside = 0;
            requesting = 0;
            for (int k = 0; k < p; k++)    /* answer everyone we made wait */
                if (deferred[k]) {
                    deferred[k] = 0;
                    send(m, 2, k, REPLY);
                }
            if (++e == entries)
                for (int k = 0; k < p; k++)
                    if (k != rank)
                        send(m, 2, k, DONE);
            next_start = 1;
            continue;
        }
        if (!requesting && e == entries && done == p - 1)
            break;
        MPI_Status st;
        MPI_Recv(m, 2, MPI_LONG, MPI_ANY_SOURCE, MPI_ANY_TAG, MPI_COMM_WORLD, &st);
        if (st.MPI_TAG == REQ) {
            L = (L > m[0] ? L : m[0]) + 1;
            int mine_first = requesting && (my_ts < m[0] || (my_ts == m[0] && rank < m[1]));
            if (inside || mine_first)
                deferred[st.MPI_SOURCE] = 1;
            else
                send(m, 2, st.MPI_SOURCE, REPLY);
        } else if (st.MPI_TAG == REPLY) {
            replies++;
        } else if (st.MPI_TAG == DONE) {
            done++;
        }
    }
    free(deferred);
}

/* ---- token ring ---- */
static void token_ring(void)
{
    long t[2] = {0, -1};                  /* entries so far, finisher (-1: none) */
    int next = (rank + 1) % p, e = 0;
    long total = (long)entries * p;
    if (rank == 0)
        send(t, 2, next, TOKEN);
    for (;;) {
        MPI_Recv(t, 2, MPI_LONG, MPI_ANY_SOURCE, TOKEN, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        if (t[1] >= 0) {                  /* the finish lap */
            if (t[1] != next)
                send(t, 2, next, TOKEN);
            return;
        }
        if (e < entries) {
            pause_us(500);                /* this process wants to enter */
            critical_section();
            e++;
            t[0]++;
        }
        if (t[0] == total)
            t[1] = rank;                  /* everyone is done: last lap */
        send(t, 2, next, TOKEN);
        if (t[1] == rank && next == rank)
            return;
        if (t[1] == rank)
            return;
    }
}

/* ---- no mutual exclusion ---- */
static void none(void)
{
    for (int e = 0; e < entries; e++) {
        pause_us(500);
        critical_section();
    }
}

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &p);
    const char *mode = argc > 1 ? argv[1] : "ra";
    entries = argc > 2 ? atoi(argv[2]) : 20;
    snprintf(marker, sizeof marker, "%s/in_critical_section", argc > 3 ? argv[3] : "/tmp");
    seed = 1234u + (unsigned)rank * 7919u;
    if (rank == 0)
        unlink(marker);
    MPI_Barrier(MPI_COMM_WORLD);
    if (strcmp(mode, "central") == 0)
        central();
    else if (strcmp(mode, "ra") == 0)
        ricart_agrawala();
    else if (strcmp(mode, "token") == 0)
        token_ring();
    else
        none();
    long tot[3], mine[3] = {violations, entered, sent};
    MPI_Reduce(mine, tot, 3, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0)
        printf("%s,%d,%ld,%ld,%ld,%.2f\n", mode, p, tot[1], tot[0], tot[2],
               tot[1] ? (double)tot[2] / tot[1] : 0.0);
    MPI_Finalize();
    return 0;
}
