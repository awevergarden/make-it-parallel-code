/*
 * pingpong.c -- one-way message time between two processes.
 * Make It Parallel, Chapter 9.
 *
 * A parent and a child bounce a message back and forth over a pipe
 * pair, a Unix-domain socket pair, or a TCP connection on the
 * loopback address, for message sizes from 8 bytes to 2 MB. The
 * one-way time is half the average round trip.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o pingpong pingpong.c
 * Run:    ./pingpong pipe|unix|tcp      (prints: bytes,microseconds)
 */
#define _POSIX_C_SOURCE 200809L
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
#include "io_all.h"
#include "../common/timer.h"

#define MAX_BYTES (2 * 1024 * 1024)

static void die(const char *what)
{
    perror(what);
    exit(1);
}

/* Set up a connected channel: parent uses p_in/p_out, child c_in/c_out. */
static void make_channel(const char *kind, int *p_in, int *p_out,
                         int *c_in, int *c_out, int *listener)
{
    *listener = -1;
    if (strcmp(kind, "pipe") == 0) {
        int a[2], b[2];                  /* a: parent->child, b: back */
        if (pipe(a) < 0 || pipe(b) < 0)
            die("pipe");
        *p_out = a[1]; *c_in = a[0];
        *c_out = b[1]; *p_in = b[0];
    } else if (strcmp(kind, "unix") == 0) {
        int sv[2];
        if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) < 0)
            die("socketpair");
        *p_in = *p_out = sv[0];
        *c_in = *c_out = sv[1];
    } else {                             /* tcp on 127.0.0.1 */
        int ls = socket(AF_INET, SOCK_STREAM, 0);
        if (ls < 0)
            die("socket");
        struct sockaddr_in addr;
        memset(&addr, 0, sizeof addr);
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
        addr.sin_port = 0;               /* any free port */
        socklen_t len = sizeof addr;
        if (bind(ls, (struct sockaddr *)&addr, len) < 0
            || listen(ls, 1) < 0
            || getsockname(ls, (struct sockaddr *)&addr, &len) < 0)
            die("bind/listen");
        int cs = socket(AF_INET, SOCK_STREAM, 0);
        if (cs < 0 || connect(cs, (struct sockaddr *)&addr, len) < 0)
            die("connect");
        int ps = accept(ls, NULL, NULL);
        if (ps < 0)
            die("accept");
        int one = 1;                     /* send small messages at once */
        setsockopt(ps, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
        setsockopt(cs, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
        *p_in = *p_out = ps;
        *c_in = *c_out = cs;
        *listener = ls;
    }
}

int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s pipe|unix|tcp\n", argv[0]);
        return 1;
    }
    int p_in, p_out, c_in, c_out, ls;
    make_channel(argv[1], &p_in, &p_out, &c_in, &c_out, &ls);
    char *buf = malloc(MAX_BYTES);
    if (buf == NULL)
        die("malloc");
    memset(buf, 'x', MAX_BYTES);

    pid_t pid = fork();
    if (pid < 0)
        die("fork");
    if (pid == 0) {                      /* child: echo every message */
        for (size_t n = 8; n <= MAX_BYTES; n *= 4) {
            long reps = n <= 65536 ? 2000 : 100;
            for (long r = 0; r < reps + 10; r++)
                if (read_all(c_in, buf, n) || write_all(c_out, buf, n))
                    _exit(1);
        }
        _exit(0);
    }
    printf("bytes,microseconds\n");
    for (size_t n = 8; n <= MAX_BYTES; n *= 4) {
        long reps = n <= 65536 ? 2000 : 100;
        for (long r = 0; r < 10; r++)    /* warm up */
            if (write_all(p_out, buf, n) || read_all(p_in, buf, n))
                die("warm-up");
        double t0 = now_seconds();
        for (long r = 0; r < reps; r++)
            if (write_all(p_out, buf, n) || read_all(p_in, buf, n))
                die("ping-pong");
        double t = now_seconds() - t0;
        printf("%zu,%.3f\n", n, t / reps / 2 * 1e6);
    }
    int status;
    waitpid(pid, &status, 0);
    free(buf);
    return WIFEXITED(status) && WEXITSTATUS(status) == 0 ? 0 : 1;
}
