/*
 * profile_demo.c -- which part of a program takes the time?
 * Make It Parallel, Chapter 3.
 *
 * Four steps: generate 4 million readings, smooth them with a moving
 * average, sort a sample of 30,000 of them to find the median, and
 * summarize. The program times each step itself; a profiler such as
 * Valgrind's callgrind shows where the instructions go.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o profile_demo profile_demo.c
 * Run:    ./profile_demo [qsort]   (qsort: sort the sample with qsort)
 * Profile: gcc -std=c17 -O2 -g -fno-inline -o profile_demo profile_demo.c
 *          valgrind --tool=callgrind ./profile_demo
 *          callgrind_annotate callgrind.out.<pid>
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../common/timer.h"

#define N 4000000L
#define WINDOW 64
#define SAMPLE 30000

static void generate(double *x, long n)
{
    unsigned long long s = 12345;
    for (long i = 0; i < n; i++) {           /* simple LCG */
        s = s * 6364136223846793005ULL + 1442695040888963407ULL;
        x[i] = (double)(s >> 11) / 9007199254740992.0;
    }
}

static void smooth(const double *x, double *y, long n, int w)
{
    for (long i = 0; i + w <= n; i++) {       /* naive moving average */
        double s = 0.0;
        for (int k = 0; k < w; k++)
            s += x[i + k];
        y[i] = s / w;
    }
}

static void insertion_sort(double *a, long n)
{
    for (long i = 1; i < n; i++) {
        double v = a[i];
        long j = i - 1;
        while (j >= 0 && a[j] > v) {
            a[j + 1] = a[j];
            j--;
        }
        a[j + 1] = v;
    }
}

static int cmp_double(const void *p, const void *q)
{
    double a = *(const double *)p, b = *(const double *)q;
    return (a > b) - (a < b);
}

static double summarize(const double *y, long n)
{
    double s = 0.0;
    for (long i = 0; i < n; i++)
        s += y[i];
    return s / n;
}

int main(int argc, char *argv[])
{
    int use_qsort = argc > 1 && strcmp(argv[1], "qsort") == 0;
    double *x = malloc(N * sizeof *x), *y = malloc(N * sizeof *y);
    double *sample = malloc(SAMPLE * sizeof *sample);
    if (x == NULL || y == NULL || sample == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }
    double t[5];
    t[0] = now_seconds();
    generate(x, N);
    t[1] = now_seconds();
    smooth(x, y, N, WINDOW);
    t[2] = now_seconds();
    for (long k = 0; k < SAMPLE; k++)
        sample[k] = y[k * (N / SAMPLE)];
    if (use_qsort)
        qsort(sample, SAMPLE, sizeof *sample, cmp_double);
    else
        insertion_sort(sample, SAMPLE);
    t[3] = now_seconds();
    double mean = summarize(y, N - WINDOW + 1);
    t[4] = now_seconds();

    const char *name[] = {"generate", "smooth", "sort", "summarize"};
    double total = t[4] - t[0];
    printf("step,seconds,percent\n");
    for (int k = 0; k < 4; k++)
        printf("%s,%.4f,%.1f\n", name[k], t[k + 1] - t[k],
               (t[k + 1] - t[k]) / total * 100);
    fprintf(stderr, "mean %.6f median %.6f\n", mean, sample[SAMPLE / 2]);
    free(x); free(y); free(sample);
    return 0;
}
