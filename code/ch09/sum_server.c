/*
 * sum_server.c -- one server process, many clients, with poll().
 * Make It Parallel, Chapter 9.
 *
 * The server listens on a TCP port on the loopback address. Each
 * client sends 8-byte integers; for each one, the server adds it to
 * that client's running total and sends the total back. poll() tells
 * the server which connections have data, so one process serves all
 * clients without ever blocking on a quiet one. This program forks
 * the server and CLIENTS client processes, then checks every total.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o sum_server sum_server.c
 * Run:    ./sum_server CLIENTS REQUESTS
 */
#define _POSIX_C_SOURCE 200809L
#include <arpa/inet.h>
#include <netinet/in.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
#include "io_all.h"
#include "../common/timer.h"

#define MAX_CLIENTS 64

static void die(const char *what)
{
    perror(what);
    exit(1);
}

/* Serve until `expected` clients have connected and all have left. */
static void serve(int listener, int expected)
{
    struct pollfd fds[MAX_CLIENTS + 1];
    int64_t total[MAX_CLIENTS + 1];
    int n = 1, accepted = 0;
    fds[0] = (struct pollfd){.fd = listener, .events = POLLIN};
    while (accepted < expected || n > 1) {
        if (poll(fds, n, -1) < 0)                 /* wait for activity */
            die("poll");
        if ((fds[0].revents & POLLIN) && n <= MAX_CLIENTS) {
            int c = accept(listener, NULL, NULL); /* a new client */
            if (c < 0)
                die("accept");
            fds[n] = (struct pollfd){.fd = c, .events = POLLIN};
            total[n++] = 0;
            accepted++;
        }
        for (int k = 1; k < n; k++) {
            if (!(fds[k].revents & (POLLIN | POLLHUP)))
                continue;
            int64_t v;
            if (read_all(fds[k].fd, &v, sizeof v) != 0) {   /* client left */
                close(fds[k].fd);
                fds[k] = fds[n - 1];              /* fill the gap */
                total[k] = total[n - 1];
                n--;
                k--;
                continue;
            }
            total[k] += v;
            if (write_all(fds[k].fd, &total[k], sizeof total[k]) != 0)
                die("write");
        }
    }
}

/* One client: send 1..requests, check the final running total. */
static int client(struct sockaddr_in *addr, long requests)
{
    int s = socket(AF_INET, SOCK_STREAM, 0);
    if (s < 0 || connect(s, (struct sockaddr *)addr, sizeof *addr) < 0)
        return 1;
    int64_t reply = 0;
    for (int64_t v = 1; v <= requests; v++)
        if (write_all(s, &v, sizeof v) != 0 || read_all(s, &reply, sizeof reply) != 0)
            return 1;
    close(s);
    return reply == (int64_t)requests * (requests + 1) / 2 ? 0 : 1;
}

int main(int argc, char *argv[])
{
    int clients = argc > 1 ? atoi(argv[1]) : 3;
    long requests = argc > 2 ? atol(argv[2]) : 10000;
    if (clients < 1 || clients > MAX_CLIENTS || requests < 1) {
        fprintf(stderr, "usage: %s CLIENTS (1..%d) REQUESTS\n", argv[0], MAX_CLIENTS);
        return 1;
    }
    int ls = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    socklen_t len = sizeof addr;
    if (ls < 0 || bind(ls, (struct sockaddr *)&addr, len) < 0
        || listen(ls, MAX_CLIENTS) < 0
        || getsockname(ls, (struct sockaddr *)&addr, &len) < 0)
        die("listen");
    double t0 = now_seconds();
    pid_t server = fork();
    if (server < 0)
        die("fork");
    if (server == 0) {
        serve(ls, clients);
        _exit(0);
    }
    close(ls);
    for (int k = 0; k < clients; k++) {
        pid_t pid = fork();
        if (pid < 0)
            die("fork");
        if (pid == 0)
            _exit(client(&addr, requests));
    }
    int failures = 0, status;
    for (int k = 0; k < clients + 1; k++) {
        if (wait(&status) < 0)
            die("wait");
        failures += !WIFEXITED(status) || WEXITSTATUS(status) != 0;
    }
    double t = now_seconds() - t0;
    printf("clients %d, requests %ld each: %s, %.1f us per request\n", clients,
           requests, failures ? "FAILED" : "all totals correct",
           t / ((double)clients * requests) * 1e6);
    return failures ? 1 : 0;
}
