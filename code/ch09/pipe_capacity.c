/*
 * pipe_capacity.c -- how many bytes fit in a pipe before write blocks?
 * Make It Parallel, Chapter 9.
 *
 * Makes the pipe non-blocking and writes one byte at a time until the
 * kernel refuses (EAGAIN).
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o pipe_capacity pipe_capacity.c
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void)
{
    int fd[2];
    if (pipe(fd) < 0) {
        perror("pipe");
        return 1;
    }
    int flags = fcntl(fd[1], F_GETFL);
    if (flags < 0 || fcntl(fd[1], F_SETFL, flags | O_NONBLOCK) < 0) {
        perror("fcntl");
        return 1;
    }
    long total = 0;
    char c = 'x';
    for (;;) {
        ssize_t k = write(fd[1], &c, 1);
        if (k == 1) {
            total++;
        } else if (errno == EAGAIN) {
            break;                      /* the pipe is full */
        } else {
            perror("write");
            return 1;
        }
    }
    printf("pipe capacity: %ld bytes\n", total);
    return 0;
}
