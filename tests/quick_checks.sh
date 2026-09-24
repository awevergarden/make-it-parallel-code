#!/bin/sh
# quick_checks.sh -- fast checks of the book's main results (run by "make check").
# Every HeatSim version reaches the 25 C center temperature; the distributed
# matrix product is exact; the replicated job log agrees; and the GPU
# kernels' CPU emulation matches version 1 bit for bit.
set -e
cd "$(dirname "$0")/.."
if [ "$(id -u)" = 0 ]; then
    export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
fi
MPIRUN="mpirun --oversubscribe"
fail=0
check() {   # check NAME COMMAND...
    name=$1; shift
    if out=$("$@" 2>&1); then echo "ok      $name"; else echo "FAILED  $name"; echo "$out" | tail -3; fail=1; fi
}
h=code/heatsim
check "HeatSim v1, 25 C"   sh -c "$h/heatsim_seq 129 50000 | grep -q '25.0000 C'"
check "HeatSim v2, 25 C"   sh -c "$h/heatsim_v2 129 50000 | grep -q '25.0000 C'"
check "HeatSim v3, 25 C"   sh -c "$h/heatsim_v3 129 50000 | grep -q '25.0000 C'"
check "HeatSim v4, 25 C"   sh -c "$h/heatsim_v4 129 50000 2 | grep -q '25.0000 C'"
check "HeatSim v5, 25 C"   sh -c "OMP_NUM_THREADS=2 $h/heatsim_v5 129 50000 | grep -q '25.0000 C'"
check "HeatSim v6, 25 C"   sh -c "$MPIRUN -np 2 $h/heatsim_v6 129 50000 | grep -q '25.0000 C'"
check "HeatSim v7, 25 C"   sh -c "OMP_NUM_THREADS=2 $MPIRUN -np 4 $h/heatsim_v7 129 50000 | grep -q '25.0000 C'"
check "matrix product exact (Cannon, 4 processes)" \
    sh -c "$MPIRUN -np 4 code/ch13/mm_dist cannon 120 | awk -F, '{ exit !(\$4 == 0) }'"
check "replicated job log agrees (3 processes)" \
    sh -c "$MPIRUN -np 3 code/ch16/tobcast 10 1 | grep -q 'all_orders_identical,yes'"
T=$(mktemp -d)
check "GPU kernels emulated on the CPU match v1" sh -c "
    cd $T && $OLDPWD/$h/heatsim_seq 37 101 0 50 101 > /dev/null && mkdir a && mv snap_*.bin a/ &&
    $OLDPWD/code/ch14/emulate_v8 tiled 37 101 0 50 101 > /dev/null && mkdir b && mv snap_*.bin b/ &&
    cmp a/snap_101.bin b/snap_101.bin"
rm -rf "$T"
if [ $fail = 0 ]; then echo "all quick checks passed"; else echo "some checks failed"; exit 1; fi
