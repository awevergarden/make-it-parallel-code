#!/bin/sh
# run_ch06.sh -- Chapter 6 benchmark kit, Make It Parallel.
#     cd code/ch06 && sh run_ch06.sh [OUTDIR]
# The 256- and 512-bit variants need a processor with AVX2 and
# AVX-512; on others, those runs are skipped.
set -e
CC=${CC:-gcc}
OUT=${1:-results}
mkdir -p "$OUT"
{
    echo "date: $(date)"
    echo "uname: $(uname -a)"
    echo "compiler: $($CC --version | head -1)"
    if command -v lscpu > /dev/null; then lscpu; else
        sysctl -n machdep.cpu.brand_string hw.ncpu 2> /dev/null || true; fi
} > "$OUT/machine.txt"
flags=$(grep -m1 -i "^flags" "$OUT/machine.txt" || true)
has() { echo "$flags" | grep -qw "$1"; }

W="-std=c17 -O2 -Wall -Wextra -Werror"
NOVEC="$W -Wno-unknown-pragmas"              # pragma ignored: scalar
V128="$W -fopenmp-simd"                      # baseline x86-64: SSE2
V256="$V128 -mavx2"
V512="$V128 -mavx512f -mprefer-vector-width=512"
widths="scalar v128"
has avx2 && widths="$widths v256"
has avx512f && widths="$widths v512"
cflags() {
    case $1 in scalar) echo "$NOVEC" ;; v128) echo "$V128" ;;
               v256) echo "$V256" ;; v512) echo "$V512" ;; esac; }

for w in $widths; do
    $CC $(cflags $w) -o daxpy_$w daxpy.c
    $CC $(cflags $w) -o matmul_$w matmul_v.c
    $CC $(cflags $w) -o heat_v3_$w ../heatsim/heatsim_v3.c 2> /dev/null || true
done
if [ "$(uname -m)" = "x86_64" ]; then
    $CC $W -DUSE_INTRINSICS -Wno-unknown-pragmas -o daxpy_intrin daxpy.c
fi
$CC $V128 -o reduce_strict reduce.c
$CC $V128 -O3 -ffast-math -o reduce_fast reduce.c
$CC $W -o heat_v1 ../heatsim/heatsim_seq.c
$CC $W -o heat_v2 ../heatsim/heatsim_v2.c

# ---- what did the compiler vectorize? (compile-time reports)
{
    echo "== heatsim_seq.c at -O2"
    $CC $W -fopt-info-vec -c ../heatsim/heatsim_seq.c -o /dev/null 2>&1 || true
    echo "== heatsim_seq.c at -O3"
    $CC $W -O3 -fopt-info-vec -c ../heatsim/heatsim_seq.c -o /dev/null 2>&1 || true
    echo "== heatsim_v3.c at -O2 -fopenmp-simd"
    $CC $V128 -fopt-info-vec -c ../heatsim/heatsim_v3.c -o /dev/null 2>&1 || true
} > "$OUT/vecinfo.txt"

# ---- correct first
for w in v128 $(has avx512f && echo v512); do
    ./heat_v3_$w 129 50000 | grep -q "25.0000 C" || { echo "v3 $w FAILED"; exit 1; }
    ./heat_v1 300 1001 1001 > /dev/null && mv snap_1001.bin a.bin
    ./heat_v3_$w 300 1001 1001 > /dev/null && mv snap_1001.bin b.bin
    cmp -s a.bin b.bin || { echo "v3 $w differs from v1"; exit 1; }
done
rm -f a.bin b.bin
ref=$(./matmul_scalar 256 | grep checksum)
for w in $widths; do
    [ "$(./matmul_$w 256 | grep checksum)" = "$ref" ] || { echo "matmul $w differs"; exit 1; }
done
echo "checks passed"

echo "variant,run,level,n,GFLOPs" > "$OUT/daxpy.csv"
for run in 1 2 3; do
    for w in $widths intrin; do
        [ -x ./daxpy_$w ] || continue
        ./daxpy_$w 2> /dev/null | awk -F, -v w=$w -v r=$run \
            'NR > 1 { print w "," r "," $0 }' >> "$OUT/daxpy.csv"
    done
done
echo "daxpy done"

echo "build,run,function,ns_per_add,sum" > "$OUT/reduce.csv"
for run in 1 2 3; do
    for b in strict fast; do
        ./reduce_$b | awk -F, -v b=$b -v r=$run \
            'NR > 1 { print b "," r "," $0 }' >> "$OUT/reduce.csv"
    done
done
echo "reduce done"

echo "variant,run,GFLOPs" > "$OUT/matmul.csv"
for run in 1 2 3; do
    for w in $widths; do
        echo "$w,$run,$(./matmul_$w 1024 | awk -F, '/GFLOPs/ { print $2 }')" >> "$OUT/matmul.csv"
    done
done
echo "matmul done"

echo "version,n,run,mlups" > "$OUT/heat.csv"
for n in 256 512 1024 2048 4096 6144; do
    steps=$(( 1000000000 / ((n - 2) * (n - 2)) ))
    [ "$steps" -lt 8 ] && steps=8
    for run in 1 2 3; do
        for v in v1 v2 v3_v128 $(has avx512f && echo v3_v512); do
            r=$(./heat_$v $n $steps | awk '/^time:/ { print $4 }')
            echo "$v,$n,$run,$r" >> "$OUT/heat.csv"
        done
    done
done
echo "heat sweep done"
# ---- vectorization patterns (Chapter 6 expansion)
# The scalar build needs -fno-tree-vectorize: with a constant trip count,
# GCC's -O2 vectorizes these loops even without the pragma.
$CC $W -fno-tree-vectorize -Wno-unknown-pragmas -o vp_scalar vpatterns.c
$CC $V128 -o vp_v128 vpatterns.c
has avx512f && $CC $V512 -o vp_v512 vpatterns.c
echo "build,run,kernel,ns_per_element" > "$OUT/vpatterns.csv"
for run in 1 2 3; do
    for b in scalar v128 v512; do
        [ -x ./vp_$b ] || continue
        ./vp_$b 2> /dev/null | awk -F, -v b=$b -v r=$run 'NR > 1 { print b "," r "," $0 }' >> "$OUT/vpatterns.csv"
    done
done
rm -f vp_scalar vp_v128 vp_v512
echo "patterns done"

rm -f daxpy_* matmul_* heat_* reduce_strict reduce_fast
echo "all done: results are in $OUT/"
