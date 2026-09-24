#!/bin/sh
# run_ch03.sh -- Chapter 3 benchmark kit, Make It Parallel.
#
# Run on a quiet machine (close other programs, plug in the laptop):
#     cd code/ch03 && sh run_ch03.sh
# Takes a few minutes and writes results/*.csv plus results/machine.txt.
# Send the whole results folder back; nothing else is needed.
set -e
CC=${CC:-gcc}
OUT=${1:-results}
HS=../heatsim/heatsim_seq.c
mkdir -p "$OUT"

# ---- what machine is this?
{
    echo "date: $(date)"
    echo "uname: $(uname -a)"
    echo "compiler: $($CC --version | head -1)"
    if command -v lscpu > /dev/null; then
        lscpu
    else
        sysctl -n machdep.cpu.brand_string hw.ncpu hw.physicalcpu \
            hw.memsize 2> /dev/null || true
    fi
} > "$OUT/machine.txt"

# ---- build every variant with zero warnings
for O in 0 1 2 3; do
    $CC -std=c17 -O$O -Wall -Wextra -Werror -o heat_O$O $HS
done
for p in timer_res dce; do
    $CC -std=c17 -O2 -Wall -Wextra -Werror -o $p $p.c
done

seconds() { "$@" | awk '/^time:/ { print $2 }'; }

# ---- 0. correct first: the 25 C check must pass before timing
./heat_O2 129 50000 > "$OUT/check.txt"
grep -q "25.0000 C" "$OUT/check.txt" || {
    echo "correctness check FAILED:"; cat "$OUT/check.txt"; exit 1; }
echo "check passed"

# ---- 1. timer resolution and cost
./timer_res > "$OUT/timer.txt"

# ---- 2. dead-code elimination demo
./dce > "$OUT/dce.txt"

# ---- 3. optimization levels: N = 512, 4000 steps, 5 runs each
echo "opt,rep,seconds" > "$OUT/opt.csv"
./heat_O2 512 400 > /dev/null                  # warm-up run
for rep in 1 2 3 4 5; do
    for O in 0 1 2 3; do
        echo "O$O,$rep,$(seconds ./heat_O$O 512 4000)" >> "$OUT/opt.csv"
    done
done
echo "optimization levels done"

# ---- 4. run-to-run variation: 30 identical runs at -O2
echo "rep,seconds" > "$OUT/repeat.csv"
for rep in $(seq 1 30); do
    echo "$rep,$(seconds ./heat_O2 512 4000)" >> "$OUT/repeat.csv"
done
echo "repeatability done"

# ---- 5. grid-size sweep: about 1e9 cell updates per run, 3 runs each
echo "n,steps,rep,seconds" > "$OUT/sweep.csv"
for n in 64 96 128 192 256 384 512 768 1024 1536 2048 3072 4096; do
    steps=$(( 1000000000 / ((n - 2) * (n - 2)) ))
    [ "$steps" -lt 8 ] && steps=8
    for rep in 1 2 3; do
        echo "$n,$steps,$rep,$(seconds ./heat_O2 $n $steps)" \
            >> "$OUT/sweep.csv"
    done
done
echo "size sweep done"

# ---- 6. profiling: where does the time go? (added with Chapter 3's expansion)
$CC -std=c17 -O2 -Wall -Wextra -Werror -o profile_demo profile_demo.c
echo "variant,run,step,seconds,percent" > "$OUT/profile.csv"
for run in 1 2 3; do
    for v in insertion qsort; do
        arg=""; [ $v = qsort ] && arg=qsort
        ./profile_demo $arg 2> /dev/null | awk -F, -v v=$v -v r=$run \
            'NR > 1 { print v "," r "," $0 }' >> "$OUT/profile.csv"
    done
done
if command -v valgrind > /dev/null; then
    $CC -std=c17 -O2 -g -fno-inline -Wall -Wextra -Werror -o profile_g profile_demo.c
    valgrind --tool=callgrind --callgrind-out-file=cg.out ./profile_g > /dev/null 2>&1
    callgrind_annotate --inclusive=no cg.out > "$OUT/callgrind.txt" 2> /dev/null || true
    rm -f cg.out profile_g
fi
rm -f profile_demo
echo "profiling done"

rm -f heat_O0 heat_O1 heat_O2 heat_O3 timer_res dce
echo "all done: results are in $OUT/"
