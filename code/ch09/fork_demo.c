/*
 * fork_demo.c -- a child process gets a copy, not a share.
 * Make It Parallel, Chapter 9.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o fork_demo fork_demo.c
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

int counter = 10;                       /* a global variable */

int main(void)
{
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }
    if (pid == 0) {                     /* the child */
        counter += 5;
        printf("child:  counter = %d\n", counter);
        return 0;
    }
    int status;                         /* the parent */
    if (waitpid(pid, &status, 0) < 0) {
        perror("waitpid");
        return 1;
    }
    printf("parent: counter = %d (child exited with %d)\n",
           counter, WEXITSTATUS(status));
    return 0;
}
