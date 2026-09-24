#!/bin/sh
# run_ch07.sh -- Chapter 7 kit, Make It Parallel.
#     cd code/ch07 && sh run_ch07.sh [OUTDIR]
# Checks correctness (any machine, any core count), measures
# single-thread costs, and measures the single-core HeatSim rates
# that feed the speedup model. It does not measure parallel speedup.
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
W="-std=c17 -O2 -Wall -Wextra -Werror -pthread"
for p in race costs false_sharing launcher_threads; do $CC $W -o $p $p.c; done
$CC $W -fopenmp-simd -o heat_v4 ../heatsim/heatsim_v4.c
$CC -std=c17 -O2 -Wall -Wextra -Werror -o heat_v1 ../heatsim/heatsim_seq.c

# ---- correctness: v4 matches v1 bit for bit at every thread count
./heat_v1 300 1001 0 1 500 1001 > /dev/null && mkdir -p ref && mv snap_*.bin ref/
for p in 1 2 3 4 7 8 16; do
    ./heat_v4 300 1001 $p 0 1 500 1001 > /dev/null
    mkdir -p got && mv snap_*.bin got/
    for f in ref/*.bin; do
        cmp -s "$f" "got/$(basename "$f")" || { echo "v4 p=$p differs"; exit 1; }
    done
    rm -rf got
    ./heat_v4 129 50000 $p | grep -q "25.0000 C" || { echo "v4 p=$p 25 C check failed"; exit 1; }
done
rm -rf ref
echo "v4 identical to v1 for 1-16 threads" > "$OUT/checks.txt"

# ---- ThreadSanitizer: v4 is clean, the racy counter is caught
if $CC -std=c17 -O1 -g -pthread -fsanitize=thread -fopenmp-simd \
       -o heat_v4_tsan ../heatsim/heatsim_v4.c 2> /dev/null; then
    $CC -std=c17 -O1 -g -pthread -fsanitize=thread -o race_tsan race.c
    echo "tsan_v4_warnings,$(./heat_v4_tsan 64 200 4 2>&1 | grep -c WARNING || true)" >> "$OUT/checks.txt"
    echo "tsan_race_warnings,$(./race_tsan plain 2 1000 2>&1 | grep -c WARNING || true)" >> "$OUT/checks.txt"
    echo "tsan_atomic_warnings,$(./race_tsan atomic 2 1000 2>&1 | grep -c WARNING || true)" >> "$OUT/checks.txt"
fi
echo "checks passed"

# ---- the racy counter, and its two fixes
echo "mode,run,expected,got,ns" > "$OUT/race.csv"
for run in 1 2 3 4 5; do
    for m in plain atomic mutex; do
        ./race $m 2 20000000 | awk -v m=$m -v r=$run \
            '{ gsub(/[(,]/, " "); print m "," r "," $3 "," $5 "," $6 }' >> "$OUT/race.csv"
    done
done
./costs > "$OUT/costs.csv"
./false_sharing 4 > "$OUT/false_sharing.csv"
./launcher_threads > "$OUT/launcher.txt"
echo "race, costs, false sharing done"

# ---- single-core rates that feed the speedup model
echo "version,n,run,mlups" > "$OUT/rates.csv"
for n in 256 1024 4096; do
    steps=$(( 1000000000 / ((n - 2) * (n - 2)) ))
    for run in 1 2 3; do
        echo "v1,$n,$run,$(./heat_v1 $n $steps | awk '/^time:/ { print $4 }')" >> "$OUT/rates.csv"
        echo "v4,$n,$run,$(./heat_v4 $n $steps 1 | awk '/^time:/ { print $4 }')" >> "$OUT/rates.csv"
    done
done
echo "rates done"
# ---- lock ordering and the bounded queue (Chapter 7 expansion)
$CC $W -o lock_order lock_order.c
$CC $W -o queue queue.c
if ./lock_order opposite > /dev/null 2>&1; then r=finished; else r=deadlock; fi
echo "opposite,$r" > "$OUT/lock_order.csv"
if ./lock_order ordered > /dev/null 2>&1; then r=finished; else r=deadlock; fi
echo "ordered,$r" >> "$OUT/lock_order.csv"
echo "consumers,run,taken,sum,us_per_item" > "$OUT/queue.csv"
for run in 1 2 3; do
    for c in 1 3 8; do
        ./queue $c | awk -v c=$c -v r=$run '{ gsub(/,/, ""); print c "," r "," $4 "," $7 "," $10 }' >> "$OUT/queue.csv"
    done
done
if $CC -std=c17 -O1 -g -pthread -fsanitize=thread -o queue_tsan queue.c 2> /dev/null; then
    echo "tsan_queue_warnings,$(./queue_tsan 3 2>&1 | grep -c WARNING || true)" >> "$OUT/checks.txt"
fi
$CC $W -o sem_queue sem_queue.c
if ./sem_queue 3 > /dev/null 2>&1; then r=correct; else r=failed; fi
echo "sem_queue,$r" >> "$OUT/lock_order.csv"
rm -f lock_order queue queue_tsan sem_queue
echo "lock order and queue done"

rm -f race costs false_sharing launcher_threads heat_v4 heat_v1 heat_v4_tsan race_tsan
echo "all done: results are in $OUT/"
