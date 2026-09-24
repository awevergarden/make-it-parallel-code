#!/bin/sh
# run_ch14.sh -- Chapter 14 kit, Make It Parallel.
#     cd code/ch14 && sh run_ch14.sh [OUTDIR]
# 1. Replays HeatSim v8's kernels on the CPU and compares with v1 bit for
#    bit; checks the tiled matrix-product kernel exactly; shows that the
#    Bug Hunt's missing halo load is caught.
# 2. If a CUDA toolchain is present, compiles the kernels and records
#    their register and shared-memory use. With an NVIDIA GPU and nvcc,
#    also runs HeatSim v8 itself.
set -e
OUT=${1:-results}
mkdir -p "$OUT"
{ echo "date: $(date)"; echo "uname: $(uname -a)"; } > "$OUT/machine.txt"
W="-std=c17 -O2 -Wall -Wextra -Werror"
gcc $W -o emulate_v8 emulate_v8.c
gcc $W -DBUG_NO_RIGHT_HALO -o emulate_v8_bug emulate_v8.c
gcc $W -o emulate_matmul emulate_matmul.c
gcc $W -o heat_v1 ../heatsim/heatsim_seq.c
echo "kernel,n,result" > "$OUT/emulation.csv"
for n in 3 4 35 257 300; do
    ./heat_v1 $n 1001 0 1 500 1001 > /dev/null && mkdir -p ref && mv snap_*.bin ref/
    for k in simple tiled; do
        ./emulate_v8 $k $n 1001 0 1 500 1001 > /dev/null && mkdir -p got && mv snap_*.bin got/
        r=identical
        for f in ref/*.bin; do cmp -s "$f" "got/$(basename "$f")" || r=DIFFERS; done
        echo "$k,$n,$r" >> "$OUT/emulation.csv"
        rm -rf got
    done
    rm -rf ref
done
for k in simple tiled; do
    ./emulate_v8 $k 129 50000 | grep -q "25.0000 C" && echo "$k,129,25C ok" >> "$OUT/emulation.csv"
done
./emulate_v8_bug tiled 300 100 | sed 's/^/bug: /' > "$OUT/bug.txt"
./emulate_v8 tiled 300 100 | sed 's/^/correct: /' >> "$OUT/bug.txt"
echo "n,result" > "$OUT/matmul.csv"
for n in 1 15 16 100 128 257; do
    ./emulate_matmul $n | awk -v n=$n '{ print n "," $3 " wrong of " $6 }' >> "$OUT/matmul.csv"
done
gcc $W -fopenmp -o heat_target heat_target.c
./heat_v1 300 1001 0 1 500 1001 > /dev/null && mkdir -p ref && mv snap_*.bin ref/
for t in 1 3; do
    OMP_NUM_THREADS=$t ./heat_target 300 1001 0 1 500 1001 > /dev/null && mkdir -p got && mv snap_*.bin got/
    r=identical
    for f in ref/*.bin; do cmp -s "$f" "got/$(basename "$f")" || r=DIFFERS; done
    echo "omp_target_t$t,300,$r" >> "$OUT/emulation.csv"
    rm -rf got
done
rm -rf ref heat_target
gcc $W -o emulate_reduce emulate_reduce.c
./emulate_reduce > "$OUT/reduce.csv"
rm -f emulate_reduce
echo "emulation done"

R=${CUDA_MIN:-$HOME/.local/cuda-min}      # made by kit/setup_cuda.sh
[ -x "$R/bin/ptxas" ] || R=/opt/cuda-min
if command -v clang++ > /dev/null && [ -x $R/bin/ptxas ]; then
    CU="clang++ -x cuda --cuda-path=$R -Wno-unknown-cuda-version -O2"
    : > "$OUT/ptxas.txt"
    for arch in sm_80 sm_90; do
        $CU --cuda-gpu-arch=$arch --cuda-device-only -S -o v8.ptx ../heatsim/heatsim_v8.cu
        $R/bin/ptxas -arch=$arch -O3 -v v8.ptx -o v8.cubin 2>> "$OUT/ptxas.txt"
    done
    $CU --cuda-gpu-arch=sm_80 --cuda-device-only -S -o mm.ptx matmul_gpu.cu
    $R/bin/ptxas -arch=sm_80 -O3 -v mm.ptx -o mm.cubin 2>> "$OUT/ptxas.txt"
    $CU --cuda-gpu-arch=sm_80 -Wall -Wextra --cuda-host-only -c -o v8_host.o ../heatsim/heatsim_v8.cu
    $CU --cuda-gpu-arch=sm_80 --cuda-device-only -S -o red.ptx reduce_gpu.cu
    $R/bin/ptxas -arch=sm_80 -O3 -v red.ptx -o red.cubin 2>> "$OUT/ptxas.txt"
    $CU --cuda-gpu-arch=sm_80 -Wall -Wextra --cuda-host-only -c -o mm_host.o matmul_gpu.cu
    $CU --cuda-gpu-arch=sm_80 -Wall -Wextra --cuda-host-only -c -o red_host.o reduce_gpu.cu
    echo "host code compiled" >> "$OUT/ptxas.txt"
    rm -f v8.ptx v8.cubin mm.ptx mm.cubin red.ptx red.cubin v8_host.o mm_host.o red_host.o
fi
if command -v nvcc > /dev/null && command -v nvidia-smi > /dev/null; then
    nvcc -O2 -o heatsim_v8 ../heatsim/heatsim_v8.cu && ./heatsim_v8 4098 1000 > "$OUT/gpu_run.txt"
fi
rm -f emulate_v8 emulate_v8_bug emulate_matmul heat_v1 heatsim_v8
echo "all done: results are in $OUT/"
