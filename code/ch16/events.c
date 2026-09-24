/*
 * events.c -- Lamport clocks, vector clocks, and skewed wall clocks.
 * Make It Parallel, Chapter 16.
 *
 * P processes perform local events and exchange messages in a random
 * pattern (the same pattern on every run with the same seed). Every
 * event records a Lamport timestamp, a vector timestamp, and a wall-
 * clock time read from a deliberately skewed clock (offset SKEW_MS * k
 * milliseconds for process k). Rank 0 gathers the log and checks:
 *   - a -> b (by vector clocks) always implies L(a) < L(b)
 *   - how many pairs are concurrent, and how many of those Lamport
 *     timestamps nonetheless order
 *   - how many messages appear received before they were sent when
 *     ordered by the skewed wall clocks
 *   - that hybrid logical clocks (HLC: a physical part l and a counter
 *     c) also respect happened-before, and how far l runs ahead of
 *     each process's own clock
 *
 * Build:  mpicc -std=c17 -O2 -Wall -Wextra -o events events.c
 * Run:    mpirun -np P ./events [SKEW_MS]
 */
#define _POSIX_C_SOURCE 200809L
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAXP 16
#define ROUNDS 40                 /* actions per process */

enum { LOCAL, SEND, RECV };
struct event {
    int proc, kind, peer, msg;    /* msg: global message id (or -1) */
    long lamport;
    long vc[MAXP];
    double wall;                  /* skewed wall clock, seconds */
    long hl, hc;                  /* hybrid logical clock (microseconds, count) */
    long pt;                      /* this process's clock when stamped (us) */
};

static double wall_now(double skew)
{
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec + skew;
}

/* The shared random plan: at round r, process k sends to plan(k, r)
   (or -1 for a local event). Everyone can compute everyone's plan. */
static int plan(int k, int r, int p, unsigned seed)
{
    unsigned long long x = (unsigned long long)seed * 2654435761ULL + k * 97 + r * 7919;
    x ^= x >> 13; x *= 0x9E3779B97F4A7C15ULL; x ^= x >> 29;
    if (x % 3 == 0)
        return -1;                                /* local event */
    int to = (int)((x >> 8) % (p - 1));
    return to >= k ? to + 1 : to;                 /* anyone but me */
}

/* Hybrid logical clock rules (Kulkarni et al., 2014). pt: physical time. */
static long hl, hc;
static void hlc_local(long pt)
{
    long old = hl;
    hl = old > pt ? old : pt;
    hc = hl == old ? hc + 1 : 0;
}
static void hlc_receive(long pt, long ml, long mc)
{
    long old = hl, m = old > ml ? old : ml;
    hl = m > pt ? m : pt;
    if (hl == old && hl == ml)
        hc = (hc > mc ? hc : mc) + 1;
    else if (hl == old)
        hc = hc + 1;
    else if (hl == ml)
        hc = mc + 1;
    else
        hc = 0;
}

int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);
    int rank, p;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &p);
    if (p < 2 || p > MAXP) {
        if (rank == 0) fprintf(stderr, "error: 2..%d processes\n", MAXP);
        MPI_Finalize();
        return 1;
    }
    double skew = (argc > 1 ? atof(argv[1]) : 2.0) * 1e-3 * rank;
    unsigned seed = 12345;
    int expect = 0;                               /* messages I will receive */
    for (int k = 0; k < p; k++)
        for (int r = 0; r < ROUNDS; r++)
            expect += plan(k, r, p, seed) == rank;
    struct event *log = malloc((2 * ROUNDS + expect) * sizeof *log);
    if (log == NULL)
        MPI_Abort(MPI_COMM_WORLD, 1);
    int n = 0, got = 0;
    long L = 0, vc[MAXP] = {0};
    long buf[4 + MAXP];                           /* id, Lamport, HLC l, c, vector */
    for (int r = 0; r < ROUNDS || got < expect; r++) {
        /* take any messages that have arrived */
        int flag = 1;
        while (flag && got < expect) {
            MPI_Status st;
            MPI_Iprobe(MPI_ANY_SOURCE, 0, MPI_COMM_WORLD, &flag, &st);
            if (!flag && r >= ROUNDS) {           /* done sending: wait */
                MPI_Probe(MPI_ANY_SOURCE, 0, MPI_COMM_WORLD, &st);
                flag = 1;
            }
            if (!flag)
                break;
            MPI_Recv(buf, 4 + p, MPI_LONG, st.MPI_SOURCE, 0, MPI_COMM_WORLD,
                     MPI_STATUS_IGNORE);
            L = (L > buf[1] ? L : buf[1]) + 1;    /* Lamport receive rule */
            for (int k = 0; k < p; k++)           /* vector receive rule */
                vc[k] = vc[k] > buf[4 + k] ? vc[k] : buf[4 + k];
            vc[rank]++;
            double w = wall_now(skew);
            long pt = (long)(w * 1e6);
            hlc_receive(pt, buf[2], buf[3]);
            log[n] = (struct event){rank, RECV, st.MPI_SOURCE, (int)buf[0], L, {0},
                                    w, hl, hc, pt};
            memcpy(log[n].vc, vc, sizeof vc);
            n++;
            got++;
        }
        if (r >= ROUNDS)
            continue;
        int to = plan(rank, r, p, seed);
        L++;                                      /* every event ticks */
        vc[rank]++;
        double w = wall_now(skew);
        long pt = (long)(w * 1e6);
        hlc_local(pt);
        log[n] = (struct event){rank, to < 0 ? LOCAL : SEND, to,
                                to < 0 ? -1 : rank * ROUNDS + r, L, {0}, w, hl, hc, pt};
        memcpy(log[n].vc, vc, sizeof vc);
        if (to >= 0) {
            buf[0] = rank * ROUNDS + r;
            buf[1] = L;
            buf[2] = hl;
            buf[3] = hc;
            memcpy(&buf[4], vc, p * sizeof *vc);
            MPI_Send(buf, 4 + p, MPI_LONG, to, 0, MPI_COMM_WORLD);
        }
        n++;
    }
    /* gather every process's log on rank 0 */
    int bytes = n * (int)sizeof *log, *counts = NULL, *displs = NULL, total = 0;
    struct event *all = NULL;
    if (rank == 0) {
        counts = malloc(p * sizeof *counts);
        displs = malloc(p * sizeof *displs);
    }
    MPI_Gather(&bytes, 1, MPI_INT, counts, 1, MPI_INT, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        for (int k = 0; k < p; k++) {
            displs[k] = total;
            total += counts[k];
        }
        all = malloc(total);
    }
    MPI_Gatherv(log, bytes, MPI_BYTE, all, counts, displs, MPI_BYTE, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        int m = total / (int)sizeof *all;
        long hb = 0, conc = 0, lamport_violations = 0, conc_ordered = 0, hlc_violations = 0;
        for (int a = 0; a < m; a++)
            for (int b = 0; b < m; b++) {
                if (a == b) continue;
                int le = 1, lt = 0;               /* vc(a) <= vc(b), strictly somewhere */
                for (int k = 0; k < p; k++) {
                    if (all[a].vc[k] > all[b].vc[k]) le = 0;
                    if (all[a].vc[k] < all[b].vc[k]) lt = 1;
                }
                if (le && lt) {                   /* a happened before b */
                    hb++;
                    lamport_violations += !(all[a].lamport < all[b].lamport);
                    hlc_violations += !(all[a].hl < all[b].hl
                                        || (all[a].hl == all[b].hl && all[a].hc < all[b].hc));
                } else if (a < b) {
                    int ge = 1;
                    for (int k = 0; k < p; k++)
                        if (all[b].vc[k] > all[a].vc[k]) ge = 0;
                    if (!ge) {                    /* neither way: concurrent */
                        conc++;
                        conc_ordered += all[a].lamport != all[b].lamport;
                    }
                }
            }
        long msgs = 0, wall_backwards = 0, ahead = 0, max_c = 0;
        for (int a = 0; a < m; a++) {
            if (all[a].hl - all[a].pt > ahead) ahead = all[a].hl - all[a].pt;
            if (all[a].hc > max_c) max_c = all[a].hc;
        }
        for (int a = 0; a < m; a++)
            if (all[a].kind == SEND)
                for (int b = 0; b < m; b++)
                    if (all[b].kind == RECV && all[b].msg == all[a].msg) {
                        msgs++;
                        wall_backwards += all[b].wall < all[a].wall;
                    }
        printf("processes,%d\nevents,%d\nmessages,%ld\nhappened_before_pairs,%ld\n"
               "lamport_violations,%ld\nconcurrent_pairs,%ld\n"
               "concurrent_with_different_lamport,%ld\nreceived_before_sent_by_wall_clock,%ld\n"
               "hlc_violations,%ld\nhlc_max_ahead_us,%ld\nhlc_max_counter,%ld\n",
               p, m, msgs, hb, lamport_violations, conc, conc_ordered, wall_backwards,
               hlc_violations, ahead, max_c);
    }
    free(log); free(all); free(counts); free(displs);
    MPI_Finalize();
    return 0;
}
