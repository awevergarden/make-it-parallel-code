#!/bin/sh
# run_ch20.sh -- Chapter 20 kit, Make It Parallel.
#     cd code/ch20 && sh run_ch20.sh [OUTDIR]
# Fits doubling times to published transistor counts and TOP500 results,
# and simulates SimQueue's job queue for comparison with queueing theory.
set -e
OUT=${1:-results}
mkdir -p "$OUT"
{ echo "date: $(date)"; echo "uname: $(uname -a)"; } > "$OUT/machine.txt"
python3 fit_growth.py > "$OUT/fits.csv"
cp growth_data.csv "$OUT/"
gcc -std=c17 -O2 -Wall -Wextra -Werror -o queue_sim queue_sim.c -lm
echo "workers,utilization,jobs,mean_wait_min" > "$OUT/queue.csv"
for r in 0.3 0.5 0.6 0.7 0.8 0.85 0.9 0.95; do
    ./queue_sim 8 $r exp >> "$OUT/queue.csv"
done
for k in fixed mixed; do ./queue_sim 8 0.8 $k >> "$OUT/queue.csv"; done
echo "workers,utilization,jobs,mean_wait_min" > "$OUT/pool.csv"
for c in 4 8 16 32; do ./queue_sim $c 0.8 exp >> "$OUT/pool.csv"; done
rm -f queue_sim
echo "all done: results are in $OUT/"
