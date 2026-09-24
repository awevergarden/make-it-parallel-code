#!/bin/sh
# convergence.sh -- center temperature versus time step for three grid
# sizes (Figure 3.1). Deterministic: any machine gives the same numbers.
# Usage: sh convergence.sh > convergence.csv
set -e
CC=${CC:-gcc}
$CC -std=c17 -O2 -Wall -Wextra -Werror -o heat_conv ../heatsim/heatsim_seq.c
echo "n,steps,center"
for n in 33 65 129; do
    for s in 10 20 50 100 200 500 1000 2000 5000 10000 20000 50000 100000; do
        c=$(./heat_conv $n $s | awk '/^center/ { print $(NF-1) }')
        echo "$n,$s,$c"
    done
done
rm -f heat_conv
