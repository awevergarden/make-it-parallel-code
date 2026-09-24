#!/bin/sh
# run_ch05.sh -- Chapter 5 benchmark kit, Make It Parallel.
#     cd code/ch05 && sh run_ch05.sh [OUTDIR]
# Needs about 1.5 GB of free memory; takes a few minutes.
set -e
CC=${CC:-gcc}
OUT=${1:-results}
mkdir -p "$OUT"
{
    echo "date: $(date)"
    echo "uname: $(uname -a)"
    echo "compiler: $($CC --version | head -1)"
    if command -v lscpu > /dev/null; then lscpu; else
        sysctl -n machdep.cpu.brand_string hw.ncpu hw.l1dcachesize \
            hw.l2cachesize hw.l3cachesize 2> /dev/null || true; fi
} > "$OUT/machine.txt"
W="-std=c17 -O2 -Wall -Wextra -Werror"
for p in latency stride bandwidth peak matmul; do $CC $W -o $p $p.c; done
$CC $W -o heat_v1 ../heatsim/heatsim_seq.c
$CC $W -o heat_v2 ../heatsim/heatsim_v2.c

# ---- 0. correct first: both versions pass, and v2 matches v1 bit for bit
for v in heat_v1 heat_v2; do
    ./$v 129 50000 | grep -q "25.0000 C" || { echo "$v check FAILED"; exit 1; }
done
./heat_v1 300 1001 1001 > /dev/null && mv snap_1001.bin v1.bin
./heat_v2 300 1001 1001 > /dev/null && mv snap_1001.bin v2.bin
cmp -s v1.bin v2.bin || { echo "v2 differs from v1"; exit 1; }
rm -f v1.bin v2.bin
c1=$(./matmul ijk 256 | grep checksum)
for v in ikj tiled; do
    [ "$(./matmul $v 256 | grep checksum)" = "$c1" ] || {
        echo "matmul $v differs"; exit 1; }
done
echo "checks passed"

./latency > "$OUT/latency.csv";      echo "latency done"
./stride > "$OUT/stride.csv" 2> /dev/null; echo "stride done"
./bandwidth > "$OUT/bandwidth.csv";  echo "bandwidth done"
./peak > "$OUT/peak.txt";            echo "peak done"

echo "variant,run,GFLOPs" > "$OUT/matmul.csv"
for run in 1 2 3; do
    for v in ijk ikj tiled; do
        echo "$v,$run,$(./matmul $v 1024 | awk -F, '/GFLOPs/ { print $2 }')" \
            >> "$OUT/matmul.csv"
    done
done
echo "matmul done"

echo "version,n,steps,run,mlups" > "$OUT/heat.csv"
for n in 256 512 1024 2048 4096 6144; do
    steps=$(( 1000000000 / ((n - 2) * (n - 2)) ))
    [ "$steps" -lt 8 ] && steps=8
    for run in 1 2 3; do
        for v in v1 v2; do
            r=$(./heat_$v $n $steps | awk '/^time:/ { print $4 }')
            echo "$v,$n,$steps,$run,$r" >> "$OUT/heat.csv"
        done
    done
done
echo "heat sweep done"
# ---- transposes and conflict misses (Chapter 5 expansion)
$CC $W -o transpose transpose.c
$CC $W -o conflict conflict.c
echo "variant,n,run,ns_per_element" > "$OUT/transpose.csv"
for n in 1024 4096; do
    for run in 1 2 3; do
        for v in naive tiled; do
            echo "$v,$n,$run,$(./transpose $v $n | awk '{ print $1 }')" >> "$OUT/transpose.csv"
        done
    done
done
echo "width,run,ns_per_element" > "$OUT/conflict.csv"
for run in 1 2 3; do
    for w in 4096 4104; do
        echo "$w,$run,$(./conflict $w | awk '{ print $1 }')" >> "$OUT/conflict.csv"
    done
done
rm -f transpose conflict
echo "transposes and conflicts done"

rm -f latency stride bandwidth peak matmul heat_v1 heat_v2
echo "all done: results are in $OUT/"
