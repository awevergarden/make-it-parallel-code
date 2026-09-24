#!/bin/sh
# run_ch17.sh -- Chapter 17 kit, Make It Parallel (Open MPI).
#     cd code/ch17 && sh run_ch17.sh [OUTDIR]
# Distributed mutual exclusion (checked by the file system), deadlock
# detection with probes, a heartbeat failure detector, and leases with
# and without fencing tokens.
set -e
OUT=${1:-results}
MPIRUN=${MPIRUN:-"mpirun --oversubscribe"}
if [ "$(id -u)" = 0 ]; then
    export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
fi
mkdir -p "$OUT"
{ echo "date: $(date)"; echo "uname: $(uname -a)"; } > "$OUT/machine.txt"
W="-std=c17 -O2 -Wall -Wextra -Werror"
mpicc $W -o mutex mutex.c
mpicc $W -o cmh cmh.c
gcc $W -o heartbeat heartbeat.c
gcc $W -pthread -o lease lease.c
DIR=$(mktemp -d)
echo "mode,processes,entries,violations,messages,msgs_per_entry" > "$OUT/mutex.csv"
for p in 2 4 6; do
    for mode in none central ra token; do
        timeout 60 $MPIRUN -np $p ./mutex $mode 20 "$DIR" >> "$OUT/mutex.csv"
    done
done
rmdir "$DIR" 2> /dev/null || true
: > "$OUT/cmh.txt"
for run in 1 2 3; do timeout 60 $MPIRUN -np 6 ./cmh >> "$OUT/cmh.txt"; done
timeout 60 $MPIRUN -np 6 ./cmh nocycle >> "$OUT/cmh.txt"
timeout 60 ./heartbeat > "$OUT/heartbeat.txt"
timeout 120 ./lease 50 > "$OUT/lease.csv"
gcc $W -o banker banker.c && ./banker > "$OUT/banker.txt"
rm -f mutex cmh heartbeat lease banker
echo "all done: results are in $OUT/"
