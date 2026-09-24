/*
 * cristian.c -- Cristian's clock synchronization, with a simulated
 * server clock and simulated, uneven network delays.
 * Make It Parallel, Chapter 16.
 *
 * A child process plays the time server over a socket pair. Its clock
 * reads the real clock plus OFFSET seconds, drifting DRIFT_PPM parts per
 * million. Before the request and before the reply, random pauses stand
 * in for network delays that differ in each direction. The client
 * estimates the server's time as the server's reply plus half the round
 * trip, and compares the estimate with the true simulated server time.
 * Cristian's bound: the error is at most half the round-trip time.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o cristian cristian.c
 * Run:    ./cristian [TRIALS]      (prints: trial,rtt_ms,error_ms,bound_ms)
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include "../ch09/io_all.h"

#define OFFSET 0.750              /* the server is 750 ms ahead ...     */
#define DRIFT_PPM 50.0            /* ... and gains 50 microseconds/second */

static double real_now(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec;
}

static double start;
static double server_clock(double t)          /* the simulated server clock */
{
    return t + OFFSET + DRIFT_PPM * 1e-6 * (t - start);
}

static void delay(unsigned *s, int max_us)
{
    *s = *s * 1103515245u + 12345u;
    struct timespec t = {0, (long)((*s >> 16) % (unsigned)max_us) * 1000};
    nanosleep(&t, NULL);
}

int main(int argc, char *argv[])
{
    int trials = argc > 1 ? atoi(argv[1]) : 20;
    int sv[2];
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) < 0) {
        perror("socketpair");
        return 1;
    }
    start = real_now();
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }
    if (pid == 0) {                           /* the time server */
        close(sv[0]);                         /* not ours: keep EOF working */
        unsigned s = 99;
        char c;
        while (read_all(sv[1], &c, 1) == 0) {
            double t = server_clock(real_now());
            delay(&s, 20000);                 /* reply in flight: 0-20 ms */
            if (write_all(sv[1], &t, sizeof t) != 0)
                break;
        }
        _exit(0);
    }
    close(sv[1]);                             /* the server's end */
    unsigned s = 7;
    printf("trial,rtt_ms,error_ms,bound_ms\n");
    for (int k = 0; k < trials; k++) {
        double t0 = real_now(), ts;
        char c = 'q';
        delay(&s, 5000);                      /* request in flight: 0-5 ms */
        if (write_all(sv[0], &c, 1) != 0 || read_all(sv[0], &ts, sizeof ts) != 0)
            return 1;
        double t1 = real_now();
        double estimate = ts + (t1 - t0) / 2; /* Cristian's estimate at t1 */
        double truth = server_clock(t1);
        printf("%d,%.3f,%.3f,%.3f\n", k, (t1 - t0) * 1e3, (estimate - truth) * 1e3,
               (t1 - t0) / 2 * 1e3);
    }
    close(sv[0]);
    waitpid(pid, NULL, 0);
    return 0;
}
