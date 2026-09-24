#!/bin/sh
# setup_cuda.sh -- a compile-only CUDA toolchain for a computer without an
# NVIDIA GPU (Make It Parallel, Chapter 14 and Appendix A).
# Clang compiles CUDA; NVIDIA's ptxas assembler, runtime headers, libdevice,
# cuRAND and CCCL headers come from NVIDIA's freely available PyPI packages,
# installed into a private Python virtual environment. The result, in
# $CUDA_MIN (default ~/.local/cuda-min), compiles host code and compiles
# device code to GPU machine code; it cannot link a runnable program
# (NVIDIA's fatbinary tool isn't among those packages) and needs no GPU.
# Needs Ubuntu or Debian (for Clang), Python 3, and about 1 GB of disk space.
#     sh kit/setup_cuda.sh
set -e
R=${CUDA_MIN:-$HOME/.local/cuda-min}
SUDO=""
[ "$(id -u)" = 0 ] || SUDO=sudo
if ! command -v clang++ > /dev/null || ! python3 -m venv --help > /dev/null 2>&1; then
    echo "installing clang and python3-venv (may ask for your password)"
    $SUDO apt-get update -qq
    $SUDO apt-get install -y -q clang python3-venv > /dev/null
fi
mkdir -p "$R"
[ -x "$R/venv/bin/pip" ] || python3 -m venv "$R/venv"
"$R/venv/bin/pip" install -q nvidia-cuda-nvcc-cu12 nvidia-cuda-runtime-cu12 \
    nvidia-curand-cu12 nvidia-cuda-cccl-cu12
N=$("$R/venv/bin/python" -c "import nvidia; print(list(nvidia.__path__)[0])")
rm -rf "$R/bin" "$R/include" "$R/nvvm" "$R/lib64"
mkdir -p "$R/bin" "$R/include" "$R/nvvm/libdevice" "$R/lib64"
ln -s "$N/cuda_nvcc/bin/ptxas" "$R/bin/ptxas"
cp -r "$N"/cuda_runtime/include/* "$N"/cuda_nvcc/include/* "$N"/curand/include/* "$R/include/"
cp -rn "$N"/cuda_cccl/include/* "$R/include/"
cp "$N/cuda_nvcc/nvvm/libdevice/libdevice.10.bc" "$R/nvvm/libdevice/"
cp -a "$N"/cuda_runtime/lib/* "$R/lib64/"
ln -sf libcudart.so.12 "$R/lib64/libcudart.so"
echo "CUDA Version 12.9" > "$R/version.txt"
clang --version | head -1
echo "compile-only CUDA toolchain in $R; compile device code with:"
echo "  clang++ -x cuda --cuda-path=$R --cuda-gpu-arch=sm_80 -Wno-unknown-cuda-version -O2 --cuda-device-only -S -o k.ptx FILE.cu"
echo "  $R/bin/ptxas -arch=sm_80 -v k.ptx -o k.cubin"
