#!/bin/sh
# run_ch15.sh -- Chapter 15 kit, Make It Parallel.
#     cd code/ch15 && sh run_ch15.sh [OUTDIR]
# Simulates systolic arrays (checked exactly), measures the accuracy of
# low-precision matrix products, and trains a small model with data
# parallelism on several MPI processes (correctness and bytes, not speed).
set -e
OUT=${1:-results}
MPIRUN=${MPIRUN:-"mpirun --oversubscribe"}
if [ "$(id -u)" = 0 ]; then
    export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
fi
mkdir -p "$OUT"
{ echo "date: $(date)"; echo "uname: $(uname -a)"; } > "$OUT/machine.txt"
gcc -std=c17 -O2 -Wall -Wextra -Werror -o systolic systolic.c
echo "mode,n,m,cycles,wrong,utilization" > "$OUT/systolic.csv"
for n in 1 3 16 256; do
    ./systolic os $n | awk -F, '{ v[$1] = $2 } END { print "os," v["n"] "," v["n"] "," v["cycles"] "," v["wrong"] "," v["utilization"] }' >> "$OUT/systolic.csv"
done
for m in 1 16 256 4096 65536; do
    ./systolic ws 16 $m | awk -F, '{ v[$1] = $2 } END { print "ws," v["n"] "," v["m"] "," v["cycles"] "," v["wrong"] "," v["utilization"] }' >> "$OUT/systolic.csv"
done
python3 precision.py > "$OUT/precision.csv"
mpicc -std=c17 -O2 -Wall -Wextra -Werror -o train_mpi train_mpi.c -lm
: > "$OUT/train.txt"
for mode in mpi ring; do
    for p in 1 2 4 8; do
        $MPIRUN -np $p ./train_mpi $mode >> "$OUT/train.txt"
    done
done
rm -f systolic train_mpi
echo "all done: results are in $OUT/"
