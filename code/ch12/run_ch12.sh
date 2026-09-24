#!/bin/sh
# run_ch12.sh -- Chapter 12 kit, Make It Parallel (Open MPI + OpenMP).
#     cd code/ch12 && sh run_ch12.sh [OUTDIR]
# Checks HeatSim v7 against v1 for many layouts and thread counts,
# records how many halo bytes each process sends per step for row and
# square decompositions, and measures v7's one-process rates. It does
# not measure speedup.
set -e
OUT=${1:-results}
MPIRUN=${MPIRUN:-"mpirun --oversubscribe"}
if [ "$(id -u)" = 0 ]; then
    export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
fi
mkdir -p "$OUT"
{
    echo "date: $(date)"
    echo "uname: $(uname -a)"
    echo "compiler: $(mpicc --version | head -1)"
    echo "mpi: $(mpirun --version 2>&1 | head -1)"
    if command -v lscpu > /dev/null; then lscpu; fi
} > "$OUT/machine.txt"
mpicc -std=c17 -O2 -fopenmp -Wall -Wextra -Werror -o heat_v7 ../heatsim/heatsim_v7.c
gcc -std=c17 -O2 -Wall -Wextra -Werror -o heat_v1 ../heatsim/heatsim_seq.c

# ---- correctness: v7 identical to v1 for layouts x threads
./heat_v1 300 1001 0 1 500 1001 > /dev/null && mkdir -p ref && mv snap_*.bin ref/
echo "processes,threads,dims,result" > "$OUT/checks.csv"
for cfg in 1:1: 2:1: 4:1: 4:2: 4:1:4x1 4:1:1x4 6:3: 8:2: 9:1: 12:1:; do
    p=${cfg%%:*}; rest=${cfg#*:}; t=${rest%%:*}; d=${rest#*:}
    if [ -n "$d" ]; then export HEATSIM_DIMS=$d; else unset HEATSIM_DIMS; fi
    OMP_NUM_THREADS=$t $MPIRUN -np $p ./heat_v7 300 1001 0 1 500 1001 > /dev/null
    mkdir -p got && mv snap_*.bin got/
    r=identical
    for f in ref/*.bin; do cmp -s "$f" "got/$(basename "$f")" || r=DIFFERS; done
    rm -rf got
    echo "$p,$t,${d:-auto},$r" >> "$OUT/checks.csv"
    [ $r = identical ] || { echo "v7 p=$p t=$t differs"; exit 1; }
done
unset HEATSIM_DIMS
OMP_NUM_THREADS=2 $MPIRUN -np 4 ./heat_v7 129 50000 | grep -q "25.0000 C" || { echo "25 C failed"; exit 1; }
rm -rf ref
echo "checks passed"

# ---- halo bytes per step: rows (px1) versus squares (MPI_Dims_create)
echo "processes,layout,dims,max_bytes,total_bytes" > "$OUT/halo.csv"
for p in 1 2 4 8 16 32 64; do
    for layout in rows squares; do
        if [ $layout = rows ]; then export HEATSIM_DIMS=${p}x1; else unset HEATSIM_DIMS; fi
        OMP_NUM_THREADS=1 $MPIRUN -np $p ./heat_v7 1026 1 |
            awk -v p=$p -v l=$layout '/processes \(/ { d = $0; sub(/.*\(/, "", d); sub(/\).*/, "", d) }
                 /halo bytes/ { print p "," l "," d "," $6 "," $10 }' >> "$OUT/halo.csv"
    done
done
unset HEATSIM_DIMS
echo "halo counts done"

# ---- one-process, one-thread rates for the models
echo "n,run,mlups" > "$OUT/rates.csv"
for n in 256 1024 4096; do
    steps=$(( 1000000000 / ((n - 2) * (n - 2)) ))
    for run in 1 2 3; do
        echo "$n,$run,$(OMP_NUM_THREADS=1 $MPIRUN -np 1 ./heat_v7 $n $steps | awk '/^time:/ { print $4 }')" >> "$OUT/rates.csv"
    done
done
rm -f heat_v7 heat_v1
echo "all done: results are in $OUT/"
