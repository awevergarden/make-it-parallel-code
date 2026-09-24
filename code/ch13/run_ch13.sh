#!/bin/sh
# run_ch13.sh -- Chapter 13 kit, Make It Parallel (Open MPI).
#     cd code/ch13 && sh run_ch13.sh [OUTDIR]
# Checks four distributed matrix products exactly and counts the values
# each process receives; times Strassen against the ikj loop on one
# core; computes layout balance and heterogeneous partitions.
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
mpicc -std=c17 -O2 -Wall -Wextra -Werror -o mm_dist mm_dist.c -lm
gcc -std=c17 -O2 -fopenmp-simd -Wall -Wextra -Werror -o strassen strassen.c -lm

echo "algorithm,n,processes,wrong,max_received,total_received,seconds" > "$OUT/traffic.csv"
for alg in 1d cannon fox summa cannon-overlap; do
    for p in 1 4 9 16; do
        $MPIRUN -np $p ./mm_dist $alg 720 60 >> "$OUT/traffic.csv"
    done
done
for p in 2 6 8; do
    $MPIRUN -np $p ./mm_dist summa 720 60 >> "$OUT/traffic.csv"
done
awk -F, 'NR > 1 && $4 != 0 { bad = 1 } END { exit bad }' "$OUT/traffic.csv" || { echo "wrong results"; exit 1; }
echo "distributed products exact"
# ---- the Bug Hunt: Cannon with A skewed the wrong way
echo "algorithm,n,processes,wrong,max_received,total_received,seconds" > "$OUT/bug.csv"
for p in 4 9 16; do
    $MPIRUN -x MM_BUG_SKEW=1 -np $p ./mm_dist cannon 720 >> "$OUT/bug.csv"
done

echo "n,run,ikj_s,strassen_s,max_diff,max_entry" > "$OUT/strassen.csv"
for n in 512 1024 2048; do
    for run in 1 2 3; do
        ./strassen $n 128 | awk -F, -v r=$run '{ v[$1] = $2 } END {
            print v["n"] "," r "," v["ikj_s"] "," v["strassen_s"] "," v["max_diff"] "," v["max_entry"] }' >> "$OUT/strassen.csv"
    done
done
python3 layout_balance.py > "$OUT/balance.csv"
python3 hetero.py > "$OUT/hetero.csv"
if python3 -c "import numpy" 2> /dev/null; then
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 blas_rate.py > "$OUT/blas.csv"
fi
rm -f mm_dist strassen
echo "all done: results are in $OUT/"
