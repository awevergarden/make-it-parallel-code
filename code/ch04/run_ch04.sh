#!/bin/sh
# run_ch04.sh -- Chapter 4 benchmark kit, Make It Parallel.
#     cd code/ch04 && sh run_ch04.sh [OUTDIR]
# Takes about a minute; writes OUTDIR/*.csv and OUTDIR/machine.txt.
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

W="-std=c17 -Wall -Wextra -Werror"
# Pipelining experiment: one add instruction per addition, no SIMD.
$CC $W -O2 -fno-tree-vectorize -o accum accum.c
# Branch experiment: keep the branch as a real conditional jump ...
$CC $W -O2 -fno-if-conversion -fno-if-conversion2 -fno-tree-vectorize \
    -o branch_jump branch.c
# ... and let the compiler do what it likes at plain -O2.
$CC $W -O2 -o branch_O2 branch.c

# ---- 1. accumulators: 5 runs
echo "run,accumulators,ns_per_add" > "$OUT/accum.csv"
./accum > /dev/null                                    # warm-up
for run in 1 2 3 4 5; do
    ./accum | awk -F, -v r=$run 'NR > 1 { print r "," $1 "," $2 }' \
        >> "$OUT/accum.csv"
done
echo "accumulators done"

# ---- 2. branch predictability sweep: 5 runs per threshold
ns() { "$@" | awk '{ print $1 }'; }
echo "variant,threshold,run,ns_per_element" > "$OUT/branch.csv"
for run in 1 2 3 4 5; do
    for t in 0 16 32 48 64 80 96 112 128 144 160 176 192 208 224 240 256; do
        echo "jump,$t,$run,$(ns ./branch_jump $t)" >> "$OUT/branch.csv"
    done
    echo "jump_sorted,128,$run,$(ns ./branch_jump 128 sorted)" >> "$OUT/branch.csv"
    echo "O2,128,$run,$(ns ./branch_O2 128)" >> "$OUT/branch.csv"
    echo "O2_sorted,128,$run,$(ns ./branch_O2 128 sorted)" >> "$OUT/branch.csv"
done
echo "branch sweep done"
# ---- 3. instruction costs, and 4. branch-pattern length (Chapter 4 expansion)
$CC $W -O2 -fno-tree-vectorize -o instr_cost instr_cost.c -lm
echo "run,op,latency_ns,throughput_ns" > "$OUT/instr.csv"
for run in 1 2 3; do
    ./instr_cost | awk -F, -v r=$run 'NR > 1 { print r "," $1 "," $2 "," $3 }' >> "$OUT/instr.csv"
done
$CC $W -O2 -fno-if-conversion -fno-if-conversion2 -fno-tree-vectorize \
    -o pattern pattern.c
echo "period,run,ns_per_element" > "$OUT/pattern.csv"
for run in 1 2 3; do
    L=2
    while [ $L -le 1048576 ]; do
        echo "$L,$run,$(./pattern $L | awk '{ print $1 }')" >> "$OUT/pattern.csv"
        L=$((L * 2))
    done
done
rm -f instr_cost pattern
echo "instruction costs and patterns done"

rm -f accum branch_jump branch_O2
echo "all done: results are in $OUT/"
