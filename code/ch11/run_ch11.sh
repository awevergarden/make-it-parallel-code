#!/bin/sh
# run_ch11.sh -- Chapter 11 kit, Make It Parallel.
#     cd code/ch11 && sh run_ch11.sh [OUTDIR]
# Computes the topology table, and measures this machine's connection
# to public internet servers (needs curl and network access).
set -e
OUT=${1:-results}
mkdir -p "$OUT"
{
    echo "date: $(date)"
    echo "uname: $(uname -a)"
    if command -v lscpu > /dev/null; then lscpu; fi
} > "$OUT/machine.txt"
python3 topology.py > "$OUT/topology.csv"
bash -n heatsim_job.sh && echo "job_script,syntax ok" > "$OUT/checks.txt"
gcc -std=c17 -O2 -Wall -Wextra -Werror -o smallfiles smallfiles.c
echo "layout,count,us_per_record" > "$OUT/files.csv"
for run in 1 2 3 4 5; do
    ./smallfiles many 20000 sf_test_dir >> "$OUT/files.csv"
    ./smallfiles one 20000 sf_test_dir >> "$OUT/files.csv"
done
rm -f smallfiles
echo "fs_type,$(df -T . | tail -1 | awk '{ print $2 }')" >> "$OUT/checks.txt"
if command -v curl > /dev/null; then
    sh wan_probe.sh > "$OUT/wan.csv"
fi
echo "all done: results are in $OUT/"
