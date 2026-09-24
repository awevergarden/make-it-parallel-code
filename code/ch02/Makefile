# Makefile -- Chapter 2 examples, Make It Parallel.
# make          build every example with the book's standard flags
# make check    also build the sanitizer versions used in Section 2.11
# make clean    remove everything make built
CC      = gcc
CFLAGS  = -std=c17 -O2 -Wall -Wextra
SANFLAGS = -std=c17 -O1 -g
PROGS   = float_order overflow swap grid sum_bug launcher parse_args

all: $(PROGS)

%: %.c
	$(CC) $(CFLAGS) -o $@ $<

check: all sum_bug_asan overflow_ub

sum_bug_asan: sum_bug.c
	$(CC) $(SANFLAGS) -fsanitize=address -o $@ $<

overflow_ub: overflow.c
	$(CC) $(SANFLAGS) -fsanitize=undefined -o $@ $<

clean:
	rm -f $(PROGS) sum_bug_asan overflow_ub

.PHONY: all check clean
