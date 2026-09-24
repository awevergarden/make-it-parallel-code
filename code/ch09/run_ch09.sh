#!/bin/sh
# run_ch09.sh -- Chapter 9 kit, Make It Parallel.
#     cd code/ch09 && sh run_ch09.sh [OUTDIR]
# Everything here runs between processes on ONE machine. On a one-core
# machine, each round trip also includes switching the core between
# the two processes, and the results say so.
set -e
CC=${CC:-gcc}
OUT=${1:-results}
mkdir -p "$OUT"
{
    echo "date: $(date)"
    echo "uname: $(uname -a)"
    echo "compiler: $($CC --version | head -1)"
    if command -v lscpu > /dev/null; then lscpu; else
        sysctl -n machdep.cpu.brand_string hw.ncpu 2> /dev/null || true; fi
} > "$OUT/machine.txt"
W="-std=c17 -O2 -Wall -Wextra -Werror"
for p in fork_demo pipe_capacity pipe_deadlock pingpong shm_demo; do
    $CC $W -o $p $p.c
done

./fork_demo > "$OUT/fork_demo.txt"
./shm_demo > "$OUT/shm_demo.txt"
./pipe_capacity > "$OUT/pipe_capacity.txt"
cap=$(awk '{ print $3 }' "$OUT/pipe_capacity.txt")
echo "mode,bytes,result" > "$OUT/deadlock.csv"
for b in 1000 $cap $((cap + 1)) 1000000; do
    if ./pipe_deadlock both-write $b > /dev/null 2>&1; then r=ok; else r=deadlock; fi
    echo "both-write,$b,$r" >> "$OUT/deadlock.csv"
done
if ./pipe_deadlock ordered 1000000 > /dev/null 2>&1; then r=ok; else r=deadlock; fi
echo "ordered,1000000,$r" >> "$OUT/deadlock.csv"
echo "processes, pipes, and deadlock done"

echo "kind,run,bytes,microseconds" > "$OUT/pingpong.csv"
for run in 1 2 3; do
    for k in pipe unix tcp; do
        ./pingpong $k | awk -F, -v k=$k -v r=$run 'NR > 1 { print k "," r "," $0 }' >> "$OUT/pingpong.csv"
    done
done
echo "ping-pong done"
# ---- one server, many clients (Chapter 9 expansion)
$CC $W -o sum_server sum_server.c
echo "clients,run,result,us_per_request" > "$OUT/server.csv"
for run in 1 2 3; do
    for c in 1 3 8; do
        ./sum_server $c 10000 | awk -v c=$c -v r=$run '{ ok = ($0 ~ /all totals correct/) ? "correct" : "failed"; print c "," r "," ok "," $(NF - 3) }' >> "$OUT/server.csv"
    done
done
rm -f sum_server
echo "server done"

rm -f fork_demo pipe_capacity pipe_deadlock pingpong shm_demo
echo "all done: results are in $OUT/"
