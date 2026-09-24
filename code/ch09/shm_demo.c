/*
 * shm_demo.c -- two processes share memory created before fork().
 * Make It Parallel, Chapter 9.
 *
 * The parent maps an anonymous shared region, forks, and waits. The
 * child fills the region's array and then sets a flag with release
 * ordering; the parent waits for the flag with acquire ordering, which
 * guarantees that it sees the whole array.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o shm_demo shm_demo.c
 */
#define _DEFAULT_SOURCE                 /* for MAP_ANONYMOUS */
#include <sched.h>
#include <stdatomic.h>
#include <stdio.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>

#define N 1000

struct shared {
    atomic_int ready;                   /* 0 until the data is written */
    double data[N];
};

int main(void)
{
    struct shared *s = mmap(NULL, sizeof *s, PROT_READ | PROT_WRITE,
                            MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (s == MAP_FAILED) {
        perror("mmap");
        return 1;
    }
    atomic_init(&s->ready, 0);
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }
    if (pid == 0) {                     /* child: produce */
        for (int i = 0; i < N; i++)
            s->data[i] = 0.5 * i;
        atomic_store_explicit(&s->ready, 1, memory_order_release);
        _exit(0);
    }
    while (atomic_load_explicit(&s->ready, memory_order_acquire) == 0)
        sched_yield();                  /* parent: wait for the flag */
    double sum = 0.0;
    for (int i = 0; i < N; i++)
        sum += s->data[i];
    printf("parent read the child's data: sum = %.1f (expected %.1f)\n",
           sum, 0.5 * N * (N - 1) / 2.0);
    waitpid(pid, NULL, 0);
    munmap(s, sizeof *s);
    return 0;
}
