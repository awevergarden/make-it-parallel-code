#!/bin/sh
# run_ch10.sh -- Chapter 10 kit, Make It Parallel (Open MPI 4.1 or later).
#     cd code/ch10 && sh run_ch10.sh [OUTDIR]
# Runs every check with several processes on one machine (more processes
# than cores is fine for correctness), finds the eager-send limit,
# measures local MPI messages, and measures the one-process HeatSim
# rates that feed the scaling model. It does not measure speedup.
set -e
OUT=${1:-results}
MPIRUN=${MPIRUN:-"mpirun --oversubscribe"}
if [ "$(id -u)" = 0 ]; then                  # containers often run as root
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
W="-std=c17 -O2 -Wall -Wextra -Werror"
for p in mpi_hello exchange pingpong_mpi reduce_mpi topology scatterv_demo mpi_bugs; do
    mpicc $W -o $p $p.c
done
mpicc $W -fopenmp-simd -o heat_v6 ../heatsim/heatsim_v6.c
gcc $W -o heat_v1 ../heatsim/heatsim_seq.c

# ---- correctness: v6 identical to v1 for several process counts
./heat_v1 300 1001 0 1 500 1001 > /dev/null && mkdir -p ref && mv snap_*.bin ref/
for p in 1 2 3 4 7 8; do
    $MPIRUN -np $p ./heat_v6 300 1001 0 1 500 1001 > /dev/null
    mkdir -p got && mv snap_*.bin got/
    for f in ref/*.bin; do
        cmp -s "$f" "got/$(basename "$f")" || { echo "v6 p=$p differs"; exit 1; }
    done
    rm -rf got
    $MPIRUN -np $p ./heat_v6 129 50000 | grep -q "25.0000 C" || { echo "v6 25 C failed"; exit 1; }
done
rm -rf ref
echo "v6 identical to v1 for 1-8 processes" > "$OUT/checks.txt"
$MPIRUN -np 4 ./mpi_hello | sort > "$OUT/hello.txt"
$MPIRUN --tag-output -np 2 ./mpi_hello | sort > "$OUT/tag_output.txt"
$MPIRUN -np 6 ./topology | sort > "$OUT/topology.txt"
$MPIRUN -np 3 ./scatterv_demo | sort > "$OUT/scatterv.txt"
echo "checks passed"

# ---- one-process rates for the model, measured before the deadlock tests
#      (a timed-out run can leave its cleanup running for a while)
echo "version,n,run,mlups" > "$OUT/rates.csv"
for n in 256 1024 4096; do
    steps=$(( 1000000000 / ((n - 2) * (n - 2)) ))
    for run in 1 2 3; do
        echo "v1,$n,$run,$(./heat_v1 $n $steps | awk '/^time:/ { print $4 }')" >> "$OUT/rates.csv"
        echo "v6,$n,$run,$($MPIRUN -np 1 ./heat_v6 $n $steps | awk '/^time:/ { print $4 }')" >> "$OUT/rates.csv"
    done
done
echo "rates done"

# ---- the Bug Hunt: largest message two MPI_Sends can swap without deadlock
works() { timeout 5 $MPIRUN -np 2 ./exchange "$1" "$2" > /dev/null 2>&1; }
lo=1024; hi=1048576                           # lo works, hi hangs
works send $lo || { echo "send $lo hangs?"; exit 1; }
if works send $hi; then echo "send never hung" > "$OUT/eager.txt"; else
    while [ $((hi - lo)) -gt 1 ]; do
        mid=$(( (lo + hi) / 2 ))
        if works send $mid; then lo=$mid; else hi=$mid; fi
    done
    echo "largest_ok,$lo" > "$OUT/eager.txt"
    echo "smallest_hang,$hi" >> "$OUT/eager.txt"
fi
if works ssend 8; then echo "ssend_8,ok" >> "$OUT/eager.txt"; else echo "ssend_8,hang" >> "$OUT/eager.txt"; fi
if works sendrecv 1048576; then echo "sendrecv_1M,ok" >> "$OUT/eager.txt"; else echo "sendrecv_1M,hang" >> "$OUT/eager.txt"; fi
# ---- two classic mistakes: a truncated receive, and a collective not all ranks call
$MPIRUN -np 2 ./mpi_bugs truncate > "$OUT/bug_truncate.txt" 2>&1 || true
if timeout 8 $MPIRUN -np 2 ./mpi_bugs barrier > /dev/null 2>&1; then
    echo "barrier_bug,finished" >> "$OUT/eager.txt"
else
    echo "barrier_bug,hang" >> "$OUT/eager.txt"
fi
sleep 5                                       # let timed-out runs finish exiting
echo "eager limit found"

# ---- reductions and ping-pong
echo "processes,sum" > "$OUT/reduce.csv"
for p in 1 2 3 4 8; do
    $MPIRUN -np $p ./reduce_mpi | awk -F, -v p=$p '/^sum/ { print p "," $2 }' >> "$OUT/reduce.csv"
done
echo "run,bytes,microseconds" > "$OUT/pingpong.csv"
for run in 1 2 3; do
    $MPIRUN -np 2 ./pingpong_mpi | awk -F, -v r=$run 'NR > 1 { print r "," $0 }' >> "$OUT/pingpong.csv"
done

rm -f mpi_hello exchange pingpong_mpi reduce_mpi topology scatterv_demo mpi_bugs heat_v6 heat_v1
echo "all done: results are in $OUT/"
