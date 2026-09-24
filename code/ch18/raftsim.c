/*
 * raftsim.c -- a discrete-event simulation of Raft, checking its safety
 * rules under message loss, delays, crashes, and restarts.
 * Make It Parallel, Chapter 18.
 *
 * Five servers replicate SimQueue's job log. Simulated time advances from
 * event to event: message deliveries (1-10 ms delay, 5% lost), election
 * and heartbeat timers, client submissions every 20 ms, and random crashes
 * and restarts. A server's term, vote, and log survive a crash; everything
 * else is lost. Two checks run throughout:
 *   election safety -- at most one leader in any term
 *   state machine safety -- every server applies the same job at each index
 * Modes: raft (as specified), fixed (every election timeout 150 ms,
 * instead of random 150-300 ms), nocheck (voters skip the check that the
 * candidate's log is at least as up to date as their own: a bug).
 *
 * Build:  gcc -std=c17 -O2 -Wall -Wextra -o raftsim raftsim.c
 * Run:    ./raftsim raft|fixed|nocheck SEEDS [RECOVERY_FILE]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 5
#define MAXLOG 2048
#define MAXENT 64
#define END_US 10000000L              /* 10 simulated seconds per run */

enum { EV_TIMER, EV_HEARTBEAT, EV_DELIVER, EV_CRASH, EV_RESTART, EV_CLIENT };
enum { RV, RV_REPLY, AE, AE_REPLY };
enum { FOLLOWER, CANDIDATE, LEADER };

struct msg {
    int type, from, to, term;
    int last_index, last_term, granted;           /* RequestVote and reply */
    int prev_index, prev_term, commit, n;         /* AppendEntries */
    int eterm[MAXENT], eval[MAXENT];
    int success, match;                           /* AppendEntries reply */
};
struct event { long t; int type, node, gen; struct msg *m; };

struct server {
    int alive, term, voted_for, role, votes, commit, applied;
    int n;                                        /* log length (index 1..n) */
    int lterm[MAXLOG + 1], lval[MAXLOG + 1];
    int next[N], match[N];
    int timer_gen;
};

static struct server s[N];
static struct event *heap;
static int hn, hcap;
static unsigned long long rng;
static int mode_fixed, mode_nocheck;
static int leader_of_term[100000];
static int committed_val[MAXLOG + 1];
static long elect_violations, apply_violations, elections, leader_crashes;
static long recovery_total_us, recoveries, jobs_submitted, next_job;
static long crash_time = -1;                      /* when the last leader crashed */
static long now_us;
static FILE *recfile;                              /* optional: each recovery time */

static unsigned rnd(void)
{
    rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
    return (unsigned)(rng >> 11);
}

static void push(struct event e)
{
    if (hn == hcap) {
        hcap = hcap ? 2 * hcap : 1024;
        heap = realloc(heap, hcap * sizeof *heap);
    }
    int i = hn++;
    while (i > 0 && heap[(i - 1) / 2].t > e.t) {
        heap[i] = heap[(i - 1) / 2];
        i = (i - 1) / 2;
    }
    heap[i] = e;
}

static struct event pop(void)
{
    struct event top = heap[0], last = heap[--hn];
    int i = 0;
    for (;;) {
        int c = 2 * i + 1;
        if (c >= hn) break;
        if (c + 1 < hn && heap[c + 1].t < heap[c].t) c++;
        if (heap[c].t >= last.t) break;
        heap[i] = heap[c];
        i = c;
    }
    heap[i] = last;
    return top;
}

static void send(struct msg *m)
{
    if (rnd() % 100 < 5) {                        /* lost */
        free(m);
        return;
    }
    push((struct event){now_us + 1000 + rnd() % 9001, EV_DELIVER, m->to, 0, m});
}

static void reset_timer(int i)
{
    long timeout = mode_fixed ? 150000 : 150000 + rnd() % 150001;
    s[i].timer_gen++;
    push((struct event){now_us + timeout, EV_TIMER, i, s[i].timer_gen, NULL});
}

static void step_down(int i, int term)
{
    s[i].term = term;
    s[i].voted_for = -1;
    s[i].role = FOLLOWER;
}

static void apply(int i)
{
    while (s[i].applied < s[i].commit) {
        int k = ++s[i].applied;
        if (committed_val[k] == 0)
            committed_val[k] = s[i].lval[k];
        else if (committed_val[k] != s[i].lval[k])
            apply_violations++;                   /* two servers disagree */
    }
}

static void send_append(int i, int j)
{
    struct msg *m = calloc(1, sizeof *m);
    m->type = AE; m->from = i; m->to = j; m->term = s[i].term;
    m->prev_index = s[i].next[j] - 1;
    m->prev_term = s[i].lterm[m->prev_index];
    m->commit = s[i].commit;
    for (int k = s[i].next[j]; k <= s[i].n && m->n < MAXENT; k++, m->n++) {
        m->eterm[m->n] = s[i].lterm[k];
        m->eval[m->n] = s[i].lval[k];
    }
    send(m);
}

static void become_leader(int i)
{
    s[i].role = LEADER;
    elections++;
    if (leader_of_term[s[i].term] >= 0 && leader_of_term[s[i].term] != i)
        elect_violations++;
    leader_of_term[s[i].term] = i;
    if (crash_time >= 0) {                        /* recovery after a leader crash */
        recovery_total_us += now_us - crash_time;
        recoveries++;
        if (recfile)
            fprintf(recfile, "%.1f\n", (now_us - crash_time) / 1000.0);
        crash_time = -1;
    }
    for (int j = 0; j < N; j++) {
        s[i].next[j] = s[i].n + 1;
        s[i].match[j] = 0;
    }
    s[i].match[i] = s[i].n;
    for (int j = 0; j < N; j++)
        if (j != i) send_append(i, j);
    push((struct event){now_us + 50000, EV_HEARTBEAT, i, s[i].term, NULL});
}

static void start_election(int i)
{
    s[i].term++;
    s[i].role = CANDIDATE;
    s[i].voted_for = i;
    s[i].votes = 1;
    reset_timer(i);
    for (int j = 0; j < N; j++) {
        if (j == i) continue;
        struct msg *m = calloc(1, sizeof *m);
        m->type = RV; m->from = i; m->to = j; m->term = s[i].term;
        m->last_index = s[i].n;
        m->last_term = s[i].lterm[s[i].n];
        send(m);
    }
}

static void advance_commit(int i)
{
    for (int k = s[i].n; k > s[i].commit; k--) {
        if (s[i].lterm[k] != s[i].term)
            break;                                /* only entries of my term */
        int count = 0;
        for (int j = 0; j < N; j++)
            count += s[i].match[j] >= k;
        if (count > N / 2) {
            s[i].commit = k;
            apply(i);
            break;
        }
    }
}

static void deliver(struct msg *m)
{
    int i = m->to;
    struct server *me = &s[i];
    if (!me->alive)
        return;
    if (m->term > me->term)
        step_down(i, m->term);
    if (m->type == RV) {
        int up_to_date = m->last_term > me->lterm[me->n]
                      || (m->last_term == me->lterm[me->n] && m->last_index >= me->n);
        int grant = m->term == me->term
                 && (me->voted_for < 0 || me->voted_for == m->from)
                 && (up_to_date || mode_nocheck);
        if (grant) {
            me->voted_for = m->from;
            reset_timer(i);
        }
        struct msg *r = calloc(1, sizeof *r);
        r->type = RV_REPLY; r->from = i; r->to = m->from; r->term = me->term; r->granted = grant;
        send(r);
    } else if (m->type == RV_REPLY) {
        if (me->role == CANDIDATE && m->term == me->term && m->granted
            && ++me->votes > N / 2)
            become_leader(i);
    } else if (m->type == AE) {
        struct msg *r = calloc(1, sizeof *r);
        r->type = AE_REPLY; r->from = i; r->to = m->from; r->term = me->term;
        if (m->term == me->term) {
            me->role = FOLLOWER;
            reset_timer(i);
            if (m->prev_index <= me->n && me->lterm[m->prev_index] == m->prev_term) {
                int k = m->prev_index;
                for (int e = 0; e < m->n; e++) {
                    k++;
                    if (k <= me->n && me->lterm[k] != m->eterm[e])
                        me->n = k - 1;            /* conflict: drop the rest */
                    if (k > me->n) {
                        me->lterm[k] = m->eterm[e];
                        me->lval[k] = m->eval[e];
                        me->n = k;
                    }
                }
                r->success = 1;
                r->match = m->prev_index + m->n;
                int c = m->commit < r->match ? m->commit : r->match;
                if (c > me->commit) {
                    me->commit = c;
                    apply(i);
                }
            } else {
                r->match = me->n;                 /* hint: my log length */
            }
        }
        send(r);
    } else if (m->type == AE_REPLY) {
        if (me->role != LEADER || m->term != me->term)
            return;
        int j = m->from;
        if (m->success) {
            if (m->match > me->match[j]) me->match[j] = m->match;
            me->next[j] = me->match[j] + 1;
            advance_commit(i);
        } else {
            int back = me->next[j] - 1;
            if (m->match + 1 < back) back = m->match + 1;
            me->next[j] = back < 1 ? 1 : back;
            send_append(i, j);
        }
    }
}

static void run(unsigned seed)
{
    memset(s, 0, sizeof s);
    memset(committed_val, 0, sizeof committed_val);
    for (int t = 0; t < 100000; t++) leader_of_term[t] = -1;
    hn = 0; now_us = 0; crash_time = -1;
    rng = 0x9E3779B97F4A7C15ULL ^ (seed * 0xBF58476D1CE4E5B9ULL);
    for (int i = 0; i < N; i++) {
        s[i].alive = 1;
        s[i].voted_for = -1;
        reset_timer(i);
    }
    push((struct event){20000, EV_CLIENT, 0, 0, NULL});
    push((struct event){500000, EV_CRASH, 0, 0, NULL});
    while (hn > 0) {
        struct event e = pop();
        now_us = e.t;
        if (now_us > END_US) {
            if (e.m) free(e.m);
            continue;
        }
        int i = e.node;
        switch (e.type) {
        case EV_DELIVER:
            deliver(e.m);
            free(e.m);
            break;
        case EV_TIMER:
            if (s[i].alive && e.gen == s[i].timer_gen && s[i].role != LEADER)
                start_election(i);
            break;
        case EV_HEARTBEAT:
            if (s[i].alive && s[i].role == LEADER && s[i].term == e.gen) {
                for (int j = 0; j < N; j++)
                    if (j != i) send_append(i, j);
                push((struct event){now_us + 50000, EV_HEARTBEAT, i, e.gen, NULL});
            }
            break;
        case EV_CLIENT:                           /* a job reaches the current leader */
            for (int j = 0; j < N; j++)
                if (s[j].alive && s[j].role == LEADER && s[j].n < MAXLOG) {
                    s[j].n++;
                    s[j].lterm[s[j].n] = s[j].term;
                    s[j].lval[s[j].n] = (int)++next_job;
                    s[j].match[j] = s[j].n;
                    jobs_submitted++;
                    break;
                }
            push((struct event){now_us + 20000, EV_CLIENT, 0, 0, NULL});
            break;
        case EV_CRASH: {                          /* crash someone, often the leader */
            int alive = 0, victim = -1;
            for (int j = 0; j < N; j++) alive += s[j].alive;
            if (alive > N / 2 + 0) {
                for (int j = 0; j < N; j++)
                    if (s[j].alive && s[j].role == LEADER && rnd() % 2) victim = j;
                if (victim < 0) {
                    int k = rnd() % N;
                    if (s[k].alive) victim = k;
                }
            }
            if (victim >= 0) {
                if (s[victim].role == LEADER) {
                    leader_crashes++;
                    if (crash_time < 0) crash_time = now_us;
                }
                s[victim].alive = 0;              /* term, vote, log persist */
                s[victim].role = FOLLOWER;
                s[victim].commit = s[victim].applied = 0;
                push((struct event){now_us + 200000 + rnd() % 600001, EV_RESTART, victim, 0, NULL});
            }
            push((struct event){now_us + 300000 + rnd() % 400001, EV_CRASH, 0, 0, NULL});
            break;
        }
        case EV_RESTART:
            s[i].alive = 1;
            reset_timer(i);
            break;
        }
    }
}

int main(int argc, char *argv[])
{
    const char *mode = argc > 1 ? argv[1] : "raft";
    int seeds = argc > 2 ? atoi(argv[2]) : 100;
    mode_fixed = strcmp(mode, "fixed") == 0;
    mode_nocheck = strcmp(mode, "nocheck") == 0;
    if (argc > 3)
        recfile = fopen(argv[3], "w");            /* recovery times, one per line */
    long runs_with_apply_violation = 0, committed = 0;
    for (int k = 1; k <= seeds; k++) {
        long before = apply_violations;
        run((unsigned)k);
        runs_with_apply_violation += apply_violations > before;
        for (int x = 1; x <= MAXLOG; x++) committed += committed_val[x] != 0;
    }
    printf("mode,%s\nruns,%d\nsimulated_seconds_each,%ld\nelection_safety_violations,%ld\n"
           "apply_violations,%ld\nruns_with_apply_violation,%ld\nleaders_elected,%ld\n"
           "leader_crashes,%ld\nmean_recovery_ms,%.1f\njobs_submitted,%ld\njobs_committed,%ld\n",
           mode, seeds, END_US / 1000000, elect_violations, apply_violations,
           runs_with_apply_violation, elections, leader_crashes,
           recoveries ? recovery_total_us / 1000.0 / recoveries : 0.0, jobs_submitted, committed);
    if (recfile)
        fclose(recfile);
    free(heap);
    return 0;
}
