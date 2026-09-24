/*
 * heartbeat.c -- how a timeout-based failure detector trades false
 * alarms against detection time. Make It Parallel, Chapter 17.
 *
 * A child process sends a heartbeat every PERIOD_MS milliseconds over a
 * socket pair. Each heartbeat is held back by a simulated network delay:
 * usually under 2 ms, but with probability 3% between 20 and 60 ms.
 * After BEATS heartbeats the child "crashes" (exits). The monitor
 * records every arrival; afterwards, for each candidate timeout, it
 * replays the same trace and counts false suspicions (gaps longer than
 * the timeout while the child was alive) and the detection delay (from
 * the crash until the last heartbeat plus the timeout). The monitor uses
 * the end of the connection only to learn the true crash time for this
 * measurement; a real detector has no such signal.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o heartbeat heartbeat.c
 * Run:    ./heartbeat          (prints CSV)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define PERIOD_MS 10
#define BEATS 400

static double now(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec;
}

static void sleep_until(double t)
{
    double d = t - now();
    if (d > 0) {
        struct timespec s = {(time_t)d, (long)((d - (time_t)d) * 1e9)};
        nanosleep(&s, NULL);
    }
}

int main(void)
{
    int sv[2];
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) < 0) {
        perror("socketpair");
        return 1;
    }
    double start = now() + 0.05;
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }
    if (pid == 0) {                                  /* the monitored process */
        close(sv[0]);
        unsigned s = 2026;
        for (int k = 0; k < BEATS; k++) {
            s = s * 1103515245u + 12345u;
            double delay = ((s >> 16) % 100 < 3) ? 0.020 + ((s >> 8) % 400) * 1e-4
                                                  : ((s >> 8) % 200) * 1e-5;
            sleep_until(start + k * PERIOD_MS * 1e-3 + delay);
            char c = 'h';
            if (write(sv[1], &c, 1) != 1)
                _exit(1);
        }
        sleep_until(start + BEATS * PERIOD_MS * 1e-3);  /* crash on schedule */
        _exit(0);
    }
    close(sv[1]);
    double *arrive = malloc(BEATS * sizeof *arrive);
    int n = 0;
    char c;
    while (read(sv[0], &c, 1) == 1 && n < BEATS)
        arrive[n++] = now();
    double crash = start + BEATS * PERIOD_MS * 1e-3;  /* when it stopped */
    waitpid(pid, NULL, 0);
    double longest = 0;
    for (int k = 1; k < n; k++)
        if (arrive[k] - arrive[k - 1] > longest)
            longest = arrive[k] - arrive[k - 1];
    printf("heartbeats,%d\nlongest_gap_ms,%.1f\n", n, longest * 1e3);
    printf("timeout_ms,false_suspicions,detection_ms\n");
    int timeouts[] = {12, 15, 20, 30, 45, 60, 80};
    for (int t = 0; t < 7; t++) {
        double to = timeouts[t] * 1e-3;
        int false_alarms = 0;
        for (int k = 1; k < n; k++)
            false_alarms += arrive[k] - arrive[k - 1] > to;
        printf("%d,%d,%.1f\n", timeouts[t], false_alarms, (arrive[n - 1] + to - crash) * 1e3);
    }
    free(arrive);
    return 0;
}
