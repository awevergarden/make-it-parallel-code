#!/bin/sh
# run_ch18.sh -- Chapter 18 kit, Make It Parallel (Open MPI).
#     cd code/ch18 && sh run_ch18.sh [OUTDIR]
# Election message counts, two-phase commit (including blocking), and a
# Raft simulation checked for safety under loss, delay, and crashes.
set -e
OUT=${1:-results}
MPIRUN=${MPIRUN:-"mpirun --oversubscribe"}
if [ "$(id -u)" = 0 ]; then
    export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
fi
mkdir -p "$OUT"
{ echo "date: $(date)"; echo "uname: $(uname -a)"; } > "$OUT/machine.txt"
W="-std=c17 -O2 -Wall -Wextra -Werror"
gcc $W -o elect elect.c && ./elect > "$OUT/elect.csv"
mpicc $W -o twopc twopc.c
: > "$OUT/twopc.txt"
for m in commit abort crash; do
    timeout 30 $MPIRUN -np 4 ./twopc $m | sort >> "$OUT/twopc.txt"
done
gcc $W -o raftsim raftsim.c
for m in raft fixed nocheck; do
    timeout 200 ./raftsim $m 200 "$OUT/recovery_$m.txt" > "$OUT/raft_$m.txt"
done
rm -f elect twopc raftsim
echo "all done: results are in $OUT/"
