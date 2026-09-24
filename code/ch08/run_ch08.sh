#!/bin/sh
# run_ch08.sh -- Chapter 8 kit, Make It Parallel.
#     cd code/ch08 && sh run_ch08.sh [OUTDIR]
# Checks correctness at many thread counts (any machine), records the
# reduction results and static schedules, and measures the one-core
# rates that feed Chapter 8's models. It does not measure speedup.
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
W="-std=c17 -O2 -Wall -Wextra -Werror -fopenmp"
for p in reduce_omp schedule matmul_omp sum_bug task_sum; do $CC $W -o $p $p.c; done
$CC $W -o heat_v5 ../heatsim/heatsim_v5.c
$CC $W -pthread -o heat_v4 ../heatsim/heatsim_v4.c
$CC -std=c17 -O2 -Wall -Wextra -Werror -o heat_v1 ../heatsim/heatsim_seq.c
$CC -std=c17 -O2 -Wall -Wextra -Werror -o mm_ref ../ch05/matmul.c

# ---- correctness: v5 identical to v1; matmul identical to Chapter 5
./heat_v1 300 1001 0 1 500 1001 > /dev/null && mkdir -p ref && mv snap_*.bin ref/
for p in 1 2 3 4 7 8 16; do
    OMP_NUM_THREADS=$p ./heat_v5 300 1001 0 1 500 1001 > /dev/null
    mkdir -p got && mv snap_*.bin got/
    for f in ref/*.bin; do
        cmp -s "$f" "got/$(basename "$f")" || { echo "v5 p=$p differs"; exit 1; }
    done
    rm -rf got
    OMP_NUM_THREADS=$p ./heat_v5 129 50000 | grep -q "25.0000 C" || { echo "v5 25 C failed"; exit 1; }
done
rm -rf ref
ref=$(./mm_ref ijk 256 | grep checksum)
for p in 1 3 8; do
    for v in ikj tiled; do
        [ "$(OMP_NUM_THREADS=$p ./matmul_omp $v 256 | grep checksum)" = "$ref" ] || {
            echo "matmul $v p=$p differs"; exit 1; }
    done
done
echo "v5 identical to v1 for 1-16 threads; matmul identical" > "$OUT/checks.txt"
echo "checks passed"

# ---- reductions, the Bug Hunt, tasks, and the static schedules
echo "threads,kind,value" > "$OUT/reduce.csv"
for p in 1 2 3 4 8 16; do
    OMP_NUM_THREADS=$p ./reduce_omp | awk -F, -v p=$p 'NR > 1 { print p "," $1 "," $2 }' >> "$OUT/reduce.csv"
    OMP_NUM_THREADS=$p ./task_sum | awk -F, -v p=$p 'NR > 1 { print p "," $1 "," $2 }' >> "$OUT/reduce.csv"
done
echo "threads,run,count" > "$OUT/sum_bug.csv"
for p in 1 2 4 8; do
    for run in 1 2 3; do
        echo "$p,$run,$(OMP_NUM_THREADS=$p ./sum_bug | awk '{ print $6 }')" >> "$OUT/sum_bug.csv"
    done
done
OMP_NUM_THREADS=4 ./schedule > "$OUT/schedule.csv"
echo "reductions, bug, schedules done"

# ---- one-core rates for the models
echo "version,n,run,mlups" > "$OUT/rates.csv"
for n in 256 1024 4096; do
    steps=$(( 1000000000 / ((n - 2) * (n - 2)) ))
    for run in 1 2 3; do
        echo "v1,$n,$run,$(./heat_v1 $n $steps | awk '/^time:/ { print $4 }')" >> "$OUT/rates.csv"
        echo "v4,$n,$run,$(./heat_v4 $n $steps 1 | awk '/^time:/ { print $4 }')" >> "$OUT/rates.csv"
        echo "v5,$n,$run,$(OMP_NUM_THREADS=1 ./heat_v5 $n $steps | awk '/^time:/ { print $4 }')" >> "$OUT/rates.csv"
    done
done
echo "variant,n,run,GFLOPs" > "$OUT/matmul.csv"
for n in 1024 2048; do
    for run in 1 2 3; do
        for v in ikj tiled; do
            echo "$v,$n,$run,$(OMP_NUM_THREADS=1 ./matmul_omp $v $n | awk -F, '/GFLOPs/ { print $2 }')" >> "$OUT/matmul.csv"
        done
    done
done
echo "rates done"
# ---- a parallel scan and four histograms (Chapter 8 expansion)
$CC $W -o scan scan.c
$CC $W -o histogram histogram.c
echo "threads,errors" > "$OUT/scan.csv"
for p in 1 2 3 4 8 16; do
    echo "$p,$(OMP_NUM_THREADS=$p ./scan | awk -F, '/^errors/ { print $2 }')" >> "$OUT/scan.csv"
done
echo "threads,run,method,ns_per_update,ok" > "$OUT/histogram.csv"
for run in 1 2 3; do
    OMP_NUM_THREADS=1 ./histogram | awk -F, -v r=$run 'NR > 1 { print 1 "," r "," $0 }' >> "$OUT/histogram.csv"
done
OMP_NUM_THREADS=4 ./histogram | awk -F, 'NR > 1 { print 4 ",1," $0 }' >> "$OUT/histogram.csv"
rm -f scan histogram
echo "scan and histogram done"

rm -f reduce_omp schedule matmul_omp sum_bug task_sum heat_v5 heat_v4 heat_v1 mm_ref
echo "all done: results are in $OUT/"
