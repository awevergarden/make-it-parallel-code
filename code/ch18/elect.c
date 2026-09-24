/*
 * elect.c -- message counts of two leader-election algorithms.
 * Make It Parallel, Chapter 18.
 *
 * Chang-Roberts ring election: every process starts at once and sends
 * its ID around a one-way ring; a process forwards IDs larger than its
 * own and drops smaller ones; the ID that returns to its owner wins.
 * Counted for IDs increasing along the ring (best case), decreasing
 * (worst case), and in random order (averaged over 1,000 rings).
 * Bully election: the highest process has crashed and process 0
 * notices. A process sends ELECTION to every higher-numbered process;
 * each live receiver answers OK and holds its own election; the highest
 * live process finally announces itself to all lower ones.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o elect elect.c
 * Run:    ./elect        (prints CSV)
 */
#include <stdio.h>
#include <stdlib.h>

/* messages until the maximum ID returns to its owner (announcement excluded) */
static long ring(const int *id, int n)
{
    long msgs = 0;
    for (int start = 0; start < n; start++) {   /* follow each ID's journey */
        int pos = start;
        do {
            pos = (pos + 1) % n;
            msgs++;
        } while (pos != start && id[pos] < id[start]);
    }
    return msgs;
}

static long bully(int n, int detector)
{
    /* processes 0..n-1, process n-1 has crashed */
    long msgs = 0;
    int *started = calloc(n, sizeof *started);
    int *queue = malloc(n * sizeof *queue), head = 0, tail = 0;
    queue[tail++] = detector;
    started[detector] = 1;
    while (head < tail) {
        int k = queue[head++];
        for (int j = k + 1; j < n; j++) {
            msgs++;                               /* ELECTION to j */
            if (j == n - 1)
                continue;                         /* crashed: no answer */
            msgs++;                               /* OK back to k */
            if (!started[j]) {
                started[j] = 1;
                queue[tail++] = j;
            }
        }
    }
    msgs += n - 2;                                /* COORDINATOR from n-2 */
    free(started);
    free(queue);
    return msgs;
}

int main(void)
{
    srand(2026);
    printf("n,ring_best,ring_worst,ring_random,bully_lowest_detects,bully_second_detects\n");
    for (int n = 8; n <= 128; n *= 2) {
        int *id = malloc(n * sizeof *id);
        for (int i = 0; i < n; i++) id[i] = i;            /* increasing along the ring */
        long best = ring(id, n);
        for (int i = 0; i < n; i++) id[i] = n - 1 - i;    /* decreasing */
        long worst = ring(id, n);
        double avg = 0;
        for (int t = 0; t < 1000; t++) {
            for (int i = 0; i < n; i++) id[i] = i;
            for (int i = n - 1; i > 0; i--) {
                int j = rand() % (i + 1), x = id[i];
                id[i] = id[j];
                id[j] = x;
            }
            avg += ring(id, n) / 1000.0;
        }
        printf("%d,%ld,%ld,%.0f,%ld,%ld\n", n, best, worst, avg, bully(n, 0), bully(n, n - 2));
        free(id);
    }
    return 0;
}
