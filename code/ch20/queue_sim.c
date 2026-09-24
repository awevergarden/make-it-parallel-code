/*
 * queue_sim.c -- simulate SimQueue's job queue and compare with theory.
 * Make It Parallel, Chapter 20.
 *
 * Jobs arrive at random (a Poisson process, rate LAMBDA per minute) at a
 * queue served first-come, first-served by C identical workers. Job
 * lengths are random with mean 10 minutes: exponential (the M/M/c queue
 * of queueing theory), or less variable (all exactly 10 minutes), or
 * more variable (a mix of short and very long jobs with the same mean).
 * The program reports the mean time a job waits before a worker starts
 * it, measured over 1,000,000 jobs after a warm-up.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o queue_sim queue_sim.c -lm
 * Run:    ./queue_sim C UTILIZATION exp|fixed|mixed
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned long long s = 88172645463325252ULL;
static double uniform(void)
{
    s ^= s << 13; s ^= s >> 7; s ^= s << 17;
    return ((s >> 11) + 0.5) / 9007199254740992.0;
}
static double expo(double mean) { return -mean * log(uniform()); }

int main(int argc, char *argv[])
{
    if (argc < 4) {
        fprintf(stderr, "usage: %s C UTILIZATION exp|fixed|mixed\n", argv[0]);
        return 1;
    }
    int c = atoi(argv[1]);
    double rho = atof(argv[2]), mean = 10.0;       /* minutes per job */
    double lambda = rho * c / mean;                /* arrivals per minute */
    const char *kind = argv[3];
    double *free_at = calloc(c, sizeof *free_at);  /* when each worker is next free */
    double t = 0, total_wait = 0;
    long n = 0, warm = 100000, jobs = 1000000;
    for (long k = 0; k < warm + jobs; k++) {
        t += expo(1.0 / lambda);                   /* next arrival */
        int w = 0;                                 /* earliest-free worker */
        for (int i = 1; i < c; i++)
            if (free_at[i] < free_at[w]) w = i;
        double start = free_at[w] > t ? free_at[w] : t;
        double len = strcmp(kind, "fixed") == 0 ? mean
                   : strcmp(kind, "mixed") == 0 ? (uniform() < 0.9 ? expo(mean * 0.5)
                                                                   : expo(mean * 5.5))
                   : expo(mean);
        free_at[w] = start + len;
        if (k >= warm) {
            total_wait += start - t;
            n++;
        }
    }
    printf("%d,%.2f,%s,%.3f\n", c, rho, kind, total_wait / n);
    free(free_at);
    return 0;
}
