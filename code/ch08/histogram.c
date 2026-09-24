/*
 * histogram.c -- counting into shared bins, four ways.
 * Make It Parallel, Chapter 8.
 *
 * critical   every update inside #pragma omp critical
 * atomic     every update with #pragma omp atomic
 * private    each thread fills its own histogram; merge at the end
 * reduction  reduction(+:hist[:BINS]), OpenMP's array reduction
 *
 * Build:  gcc -std=c17 -O2 -fopenmp -Wall -Wextra -o histogram histogram.c
 * Run:    OMP_NUM_THREADS=4 ./histogram   (prints: method,ns_per_update,ok)
 */
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 20000000L
#define BINS 64

static void fill_reference(const unsigned char *key, long *ref)
{
    memset(ref, 0, BINS * sizeof *ref);
    for (long i = 0; i < N; i++)
        ref[key[i]]++;
}

int main(void)
{
    unsigned char *key = malloc(N);
    if (key == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    unsigned long long x = 2463534242ULL;
    for (long i = 0; i < N; i++) {             /* xorshift keys in 0..63 */
        x ^= x << 13; x ^= x >> 7; x ^= x << 17;
        key[i] = (unsigned char)(x % BINS);
    }
    long ref[BINS], hist[BINS];
    fill_reference(key, ref);
    const char *name[] = {"critical", "atomic", "private", "reduction"};
    printf("method,ns_per_update,ok\n");
    for (int m = 0; m < 4; m++) {
        memset(hist, 0, sizeof hist);
        double t0 = omp_get_wtime();
        if (m == 0) {
            #pragma omp parallel for
            for (long i = 0; i < N; i++) {
                #pragma omp critical
                hist[key[i]]++;
            }
        } else if (m == 1) {
            #pragma omp parallel for
            for (long i = 0; i < N; i++) {
                #pragma omp atomic
                hist[key[i]]++;
            }
        } else if (m == 2) {
            #pragma omp parallel
            {
                long mine[BINS] = {0};
                #pragma omp for
                for (long i = 0; i < N; i++)
                    mine[key[i]]++;
                for (int b = 0; b < BINS; b++) {
                    #pragma omp atomic
                    hist[b] += mine[b];
                }
            }
        } else {
            #pragma omp parallel for reduction(+:hist[:BINS])
            for (long i = 0; i < N; i++)
                hist[key[i]]++;
        }
        double t = omp_get_wtime() - t0;
        int ok = memcmp(hist, ref, sizeof hist) == 0;
        printf("%s,%.2f,%s\n", name[m], t / N * 1e9, ok ? "yes" : "no");
    }
    free(key);
    return 0;
}
