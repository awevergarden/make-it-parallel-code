/*
 * pipe_deadlock.c -- Bug Hunt program for Chapter 9.
 * Make It Parallel, Chapter 9.
 *
 * A parent and child exchange BYTES bytes over two pipes. In mode
 * "both-write", each process writes its whole message before
 * reading; in mode "ordered", the child reads first. An alarm stops
 * the program if nothing finishes within 3 seconds.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o pipe_deadlock pipe_deadlock.c
 * Run:    ./pipe_deadlock both-write|ordered BYTES
 */
#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>
#include "io_all.h"

static void on_alarm(int sig)
{
    (void)sig;
    static const char msg[] = "no progress for 3 s: deadlock\n";
    (void)!write(2, msg, sizeof msg - 1);
    _exit(2);
}

/* Exchange: send our message, receive theirs (or the reverse). */
static int exchange(int out, int in, size_t bytes, int read_first)
{
    char *send = malloc(bytes), *recv = malloc(bytes);
    if (send == NULL || recv == NULL)
        return -1;
    memset(send, 'm', bytes);
    int rc = read_first
        ? (read_all(in, recv, bytes) || write_all(out, send, bytes))
        : (write_all(out, send, bytes) || read_all(in, recv, bytes));
    free(send);
    free(recv);
    return rc ? -1 : 0;
}

int main(int argc, char *argv[])
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s both-write|ordered BYTES\n", argv[0]);
        return 1;
    }
    int ordered = strcmp(argv[1], "ordered") == 0;
    size_t bytes = (size_t)atol(argv[2]);
    int to_child[2], to_parent[2];
    if (pipe(to_child) < 0 || pipe(to_parent) < 0) {
        perror("pipe");
        return 1;
    }
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }
    signal(SIGALRM, on_alarm);
    signal(SIGPIPE, SIG_IGN);           /* a vanished reader: report, don't die */
    alarm(3);
    if (pid == 0) {                     /* child */
        close(to_child[1]);
        close(to_parent[0]);
        return exchange(to_parent[1], to_child[0], bytes, ordered) ? 1 : 0;
    }
    close(to_child[0]);                 /* parent */
    close(to_parent[1]);
    int rc = exchange(to_child[1], to_parent[0], bytes, 0);
    int status;
    waitpid(pid, &status, 0);
    if (rc != 0 || !WIFEXITED(status) || WEXITSTATUS(status) != 0)
        return 2;
    printf("exchanged %zu bytes each way: ok\n", bytes);
    return 0;
}
