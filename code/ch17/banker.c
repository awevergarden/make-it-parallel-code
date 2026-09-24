/*
 * banker.c -- Dijkstra's banker's algorithm for deadlock avoidance.
 * Make It Parallel, Chapter 17.
 *
 * Four SimQueue jobs share three kinds of resource: GPUs, software
 * licenses, and scratch-disk slots. Each job has declared its maximum
 * need in advance. A state is SAFE if the jobs can all finish in some
 * order, each obtaining its remaining need from what is available plus
 * what earlier jobs in the order release. A request is granted only if
 * the state after granting it is still safe.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o banker banker.c
 * Run:    ./banker
 */
#include <stdio.h>
#include <string.h>

#define N 4                       /* jobs */
#define R 3                       /* resource types */
static const char *res[R] = {"GPUs", "licenses", "disk slots"};

static int maxneed[N][R] = {{3, 2, 2}, {2, 1, 3}, {4, 1, 1}, {1, 2, 2}};
static int alloc[N][R]   = {{1, 1, 0}, {1, 0, 1}, {2, 0, 1}, {0, 1, 1}};
static int avail[R]      = {1, 1, 2};

/* Returns 1 if safe, filling order[] with a completion order. */
static int safe(int order[N])
{
    int work[R], done[N] = {0}, k = 0;
    memcpy(work, avail, sizeof work);
    for (int progress = 1; progress && k < N; ) {
        progress = 0;
        for (int j = 0; j < N; j++) {
            if (done[j])
                continue;
            int fits = 1;
            for (int r = 0; r < R; r++)
                if (maxneed[j][r] - alloc[j][r] > work[r])
                    fits = 0;
            if (fits) {                       /* j can finish, then releases */
                for (int r = 0; r < R; r++)
                    work[r] += alloc[j][r];
                done[j] = 1;
                order[k++] = j;
                progress = 1;
            }
        }
    }
    return k == N;
}

/* Grant the request if possible and safe; otherwise leave the state alone. */
static const char *request(int j, const int req[R])
{
    for (int r = 0; r < R; r++) {
        if (alloc[j][r] + req[r] > maxneed[j][r])
            return "refused: exceeds the declared maximum";
        if (req[r] > avail[r])
            return "wait: not enough available now";
    }
    for (int r = 0; r < R; r++) {            /* try it */
        avail[r] -= req[r];
        alloc[j][r] += req[r];
    }
    int order[N];
    if (safe(order))
        return "granted: the new state is safe";
    for (int r = 0; r < R; r++) {            /* undo */
        avail[r] += req[r];
        alloc[j][r] -= req[r];
    }
    return "wait: granting would make the state unsafe";
}

int main(void)
{
    int order[N];
    printf("need:");
    for (int j = 0; j < N; j++) {
        printf(" J%d=(", j);
        for (int r = 0; r < R; r++)
            printf("%s%d", r ? "," : "", maxneed[j][r] - alloc[j][r]);
        printf(")");
    }
    printf("\n");
    int ok = safe(order);
    printf("initial state: %s", ok ? "safe, order" : "UNSAFE");
    for (int k = 0; ok && k < N; k++)
        printf(" J%d", order[k]);
    printf("\n");
    int r1[R] = {1, 0, 0}, r2[R] = {0, 1, 1}, r3[R] = {1, 0, 1};
    printf("J1 asks for (1,0,0): %s\n", request(1, r1));
    printf("J3 asks for (0,1,1): %s\n", request(3, r2));
    printf("J0 asks for (1,0,1): %s\n", request(0, r3));
    (void)res;
    return 0;
}
