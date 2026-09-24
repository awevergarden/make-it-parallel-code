/*
 * lease.c -- why a lease needs a fencing token.
 * Make It Parallel, Chapter 17.
 *
 * Three "machines", played by threads in one process: a lock service
 * that grants leases of LEASE_MS milliseconds with an increasing token,
 * a storage service, and two clients. Client A takes the lease, then
 * pauses for a random time (standing in for a garbage-collection pause
 * or a swapped-out process); client B keeps asking for the lease and,
 * once A's has expired, gets it and writes. When A wakes, it writes too,
 * still believing it holds the lease. Without fencing, the storage
 * accepts A's stale write; with fencing, it rejects any write whose
 * token is lower than one it has already seen.
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -pthread -o lease lease.c
 * Run:    ./lease TRIALS          (prints CSV)
 */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define LEASE_MS 30

static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;
static double lease_end;          /* when the current lease expires */
static long next_token, holder_token;
static long max_token_seen;       /* storage: highest token seen */
static char stored;               /* storage: who wrote last */
static int fencing, stale_accepted, stale_rejected, overlaps;

static double now(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec;
}

static void sleep_ms(double ms)
{
    struct timespec s = {(time_t)(ms / 1000), (long)((ms - 1000 * (time_t)(ms / 1000)) * 1e6)};
    nanosleep(&s, NULL);
}

/* Lock service: grant a lease if none is active. Returns token or 0. */
static long try_acquire(void)
{
    long tok = 0;
    pthread_mutex_lock(&mu);
    if (now() >= lease_end) {
        tok = ++next_token;
        holder_token = tok;
        lease_end = now() + LEASE_MS * 1e-3;
    }
    pthread_mutex_unlock(&mu);
    return tok;
}

/* Storage service: a write carrying a token. Returns 1 if accepted. */
static int storage_write(char who, long token)
{
    int ok = 1;
    pthread_mutex_lock(&mu);
    if (fencing && token < max_token_seen)
        ok = 0;                               /* stale holder: fenced off */
    if (ok) {
        if (token > max_token_seen)
            max_token_seen = token;
        stored = who;
    }
    pthread_mutex_unlock(&mu);
    return ok;
}

static double pause_ms;

static void *client_a(void *arg)
{
    (void)arg;
    long tok;
    while ((tok = try_acquire()) == 0)
        sleep_ms(1);
    sleep_ms(pause_ms);                       /* the pause A doesn't notice */
    int ok = storage_write('A', tok);         /* A still thinks it holds the lease */
    pthread_mutex_lock(&mu);
    int stale = tok != holder_token;          /* someone else got the lease */
    pthread_mutex_unlock(&mu);
    if (stale) {
        overlaps++;
        if (ok) stale_accepted++; else stale_rejected++;
    }
    return NULL;
}

static void *client_b(void *arg)
{
    (void)arg;
    sleep_ms(2);                              /* let A get there first */
    long tok;
    double give_up = now() + 0.2;
    while ((tok = try_acquire()) == 0 && now() < give_up)
        sleep_ms(1);
    if (tok)
        storage_write('B', tok);
    return NULL;
}

int main(int argc, char *argv[])
{
    int trials = argc > 1 ? atoi(argv[1]) : 50;
    printf("fencing,trials,a_lease_expired_before_write,stale_writes_accepted,stale_writes_rejected\n");
    for (fencing = 0; fencing <= 1; fencing++) {
        stale_accepted = stale_rejected = overlaps = 0;
        unsigned s = 77;
        for (int t = 0; t < trials; t++) {
            s = s * 1103515245u + 12345u;
            pause_ms = (double)((s >> 16) % 80);  /* 0-79 ms: often past the lease */
            lease_end = 0;
            next_token = holder_token = max_token_seen = 0;
            stored = 0;
            pthread_t a, b;
            pthread_create(&a, NULL, client_a, NULL);
            pthread_create(&b, NULL, client_b, NULL);
            pthread_join(a, NULL);
            pthread_join(b, NULL);
        }
        printf("%s,%d,%d,%d,%d\n", fencing ? "yes" : "no", trials, overlaps,
               stale_accepted, stale_rejected);
    }
    return 0;
}
