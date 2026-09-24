#!/bin/sh
# run_ch16.sh -- Chapter 16 kit, Make It Parallel (Open MPI).
#     cd code/ch16 && sh run_ch16.sh [OUTDIR]
# Logical clocks versus skewed wall clocks; Cristian's algorithm with a
# simulated server clock; totally ordered multicast checked for agreement.
set -e
OUT=${1:-results}
MPIRUN=${MPIRUN:-"mpirun --oversubscribe"}
if [ "$(id -u)" = 0 ]; then
    export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
fi
mkdir -p "$OUT"
{ echo "date: $(date)"; echo "uname: $(uname -a)"; } > "$OUT/machine.txt"
W="-std=c17 -O2 -Wall -Wextra -Werror"
mpicc $W -o events events.c
mpicc $W -o tobcast tobcast.c
gcc $W -o cristian cristian.c
echo "skew_ms,key,value" > "$OUT/events.csv"
for skew in 0 2 20; do
    timeout 60 $MPIRUN -np 4 ./events $skew | sed "s/^/$skew,/" >> "$OUT/events.csv"
done
timeout 60 ./cristian 40 > "$OUT/cristian.csv"
echo "processes,seed,identical,messages" > "$OUT/tobcast.csv"
for p in 2 3 4 5 6; do
    for seed in 1 2 3; do
        timeout 60 $MPIRUN -np $p ./tobcast 20 $seed |
            awk -F, -v p=$p -v s=$seed '{ v[$1] = $2 } END {
                print p "," s "," v["all_orders_identical"] "," v["messages_sent"] }' >> "$OUT/tobcast.csv"
    done
done
rm -f events tobcast cristian
echo "all done: results are in $OUT/"
