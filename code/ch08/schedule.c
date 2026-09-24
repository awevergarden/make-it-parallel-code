/*
 * schedule.c -- which thread gets which iteration?
 * Make It Parallel, Chapter 8.
 *
 * Runs an empty loop of N iterations under three schedules and
 * prints the thread that executed each iteration. For the static
 * schedules, OpenMP's assignment is fixed in advance, so the output
 * is the same on any machine.
 *
 * Build:  gcc -std=c17 -O2 -fopenmp -Wall -Wextra -o schedule schedule.c
 * Run:    OMP_NUM_THREADS=4 ./schedule    (prints: schedule,i,thread)
 */
#include <omp.h>
#include <stdio.h>

#define N 400

int main(void)
{
    int owner[N];
    printf("schedule,i,thread\n");

    #pragma omp parallel for schedule(static)
    for (int i = 0; i < N; i++)
        owner[i] = omp_get_thread_num();
    for (int i = 0; i < N; i++)
        printf("static,%d,%d\n", i, owner[i]);

    #pragma omp parallel for schedule(static, 1)
    for (int i = 0; i < N; i++)
        owner[i] = omp_get_thread_num();
    for (int i = 0; i < N; i++)
        printf("static1,%d,%d\n", i, owner[i]);

    #pragma omp parallel for schedule(static, 25)
    for (int i = 0; i < N; i++)
        owner[i] = omp_get_thread_num();
    for (int i = 0; i < N; i++)
        printf("static25,%d,%d\n", i, owner[i]);
    return 0;
}
