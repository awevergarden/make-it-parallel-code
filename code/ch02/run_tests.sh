#!/bin/sh
# run_tests.sh -- build and run every Chapter 2 example.
# Every program must compile with zero warnings.
set -e
CFLAGS="-std=c17 -O2 -Wall -Wextra"
for p in float_order overflow swap grid sum_bug launcher parse_args; do
    out=$(gcc $CFLAGS -o "$p" "$p.c" 2>&1)
    if [ -n "$out" ]; then echo "WARNINGS in $p.c:"; echo "$out"; exit 1; fi
done
echo "== float_order";  ./float_order
echo "== overflow";     ./overflow 50000
echo "== swap";         ./swap
echo "== grid";         ./grid 4
echo "== launcher";     ./launcher
echo "== parse_args";   ./parse_args 128 20000
./parse_args 12x 5 || echo "(rejected 12x, as intended)"
./parse_args 99999999999 5 || echo "(rejected overflow, as intended)"
echo "== sanitizers"
gcc -std=c17 -O1 -g -fsanitize=undefined -o overflow_ub overflow.c
./overflow_ub 50000 2>&1 | grep -m1 "runtime error" || true
gcc -std=c17 -O1 -g -fsanitize=address -o sum_bug_asan sum_bug.c
./sum_bug_asan 2>&1 | grep -E "ERROR|READ of|#[01] |located 0 bytes|allocated by" | head -6 || true
echo "all builds clean"
