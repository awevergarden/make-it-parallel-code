#!/bin/sh
# check_tools.sh -- check that the tools this book uses are installed and work.
# Make It Parallel, Appendix A.
#     sh check_tools.sh
# Compiles and runs a tiny test for each tool, rather than only checking that
# a command exists, and prints one line per tool: ok, MISSING, or FAILED.
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
pass=0; fail=0
report() {     # report NAME STATUS [DETAIL]
    printf '%-26s %s %s\n' "$1" "$2" "$3"
    if [ "$2" = ok ]; then pass=$((pass + 1)); else fail=$((fail + 1)); fi
}
has() { command -v "$1" > /dev/null 2>&1; }

cat > "$T/c17.c" << 'C'
#include <stdio.h>
_Static_assert(__STDC_VERSION__ >= 201710L, "needs C17");
int main(void) { printf("ok\n"); return 0; }
C
cat > "$T/omp.c" << 'C'
#include <omp.h>
#include <stdio.h>
int main(void) {
    int n = 0;
    #pragma omp parallel reduction(+:n)
    n += 1;
    printf("%d\n", n);
    return 0;
}
C
cat > "$T/pth.c" << 'C'
#include <pthread.h>
#include <stdio.h>
static void *work(void *arg) { *(int *)arg = 42; return NULL; }
int main(void) {
    int x = 0; pthread_t t;
    pthread_create(&t, NULL, work, &x);
    pthread_join(t, NULL);
    printf("%d\n", x);
    return 0;
}
C
cat > "$T/mpi.c" << 'C'
#include <mpi.h>
#include <stdio.h>
int main(int argc, char *argv[]) {
    int r, p, s;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &r);
    MPI_Comm_size(MPI_COMM_WORLD, &p);
    MPI_Reduce(&r, &s, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
    if (r == 0) printf("%d %d\n", p, s);
    MPI_Finalize();
    return 0;
}
C

if has gcc; then
    if gcc -std=c17 -O2 -Wall -o "$T/c17" "$T/c17.c" 2> /dev/null && "$T/c17" > /dev/null
    then report "C compiler (C17)" ok "$(gcc -dumpfullversion 2> /dev/null || gcc -dumpversion)"
    else report "C compiler (C17)" FAILED; fi
    if gcc -std=c17 -O2 -pthread -o "$T/pth" "$T/pth.c" 2> /dev/null && [ "$("$T/pth")" = 42 ]
    then report "POSIX threads" ok
    else report "POSIX threads" FAILED; fi
    if gcc -std=c17 -O2 -fopenmp -o "$T/omp" "$T/omp.c" 2> /dev/null \
       && [ "$(OMP_NUM_THREADS=2 "$T/omp")" = 2 ]
    then report "OpenMP" ok "(2 threads ran)"
    else report "OpenMP" FAILED "(on macOS, use Homebrew's gcc-NN)"; fi
else
    report "C compiler (C17)" MISSING
fi
if has make; then report "make" ok; else report "make" MISSING; fi
if has mpicc && has mpirun; then
    if [ "$(id -u)" = 0 ]; then
        export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
    fi
    if mpicc -std=c17 -O2 -o "$T/mpi" "$T/mpi.c" 2> /dev/null \
       && out=$(mpirun --oversubscribe -np 2 "$T/mpi" 2> /dev/null || mpirun -np 2 "$T/mpi" 2> /dev/null) \
       && [ "$out" = "2 1" ]
    then report "MPI (2 processes)" ok "$(mpirun --version 2>&1 | head -1)"
    else report "MPI (2 processes)" FAILED; fi
else
    report "MPI (2 processes)" MISSING
fi
if has python3; then
    if python3 -c "import numpy, matplotlib" 2> /dev/null
    then report "Python, NumPy, Matplotlib" ok "$(python3 --version 2>&1)"
    else report "Python, NumPy, Matplotlib" MISSING "(install numpy and matplotlib)"; fi
else
    report "Python, NumPy, Matplotlib" MISSING
fi
for tool in gdb valgrind; do        # useful, but optional
    if has $tool; then report "$tool (optional)" ok; else printf '%-26s %s\n' "$tool (optional)" "not installed"; fi
done
if has nvcc; then printf '%-26s %s\n' "CUDA (optional)" "nvcc found"; fi
echo "$pass passed, $fail missing or failed"
[ "$fail" = 0 ]
