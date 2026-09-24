# Make It Parallel — Companion Code

This repository holds the programs, measurement kits, and data for the book
*Make It Parallel*: every program printed in the book, the kits that
reproduce its measurements, and the book's own measured results.

## Getting started

Install the tools described in the book's Appendix A (GCC, make, Open MPI,
Python 3 with NumPy and Matplotlib), then:

```sh
sh code/appA/check_tools.sh   # check that every tool works
make                          # build every chapter's programs
make check                    # run the quick tests (under a minute)
```

To work with one chapter, go to its folder: `make` builds its programs, and
each program's first comment says how to run it.

## What is here

| Folder | Contents |
|---|---|
| `code/chNN/` | the programs of Chapter NN, a `Makefile`, and the chapter's kit, `run_chNN.sh` |
| `code/heatsim/` | HeatSim versions 1 to 8, the book's running example |
| `code/common/` | the timer and barrier headers shared by many programs |
| `code/appA/` | `check_tools.sh`, from Appendix A |
| `kit/` | scripts that turn kit results into the book's numbers (`values_chNN.py`) and figures (`figs_chNN.py`), the performance models, and `setup_cuda.sh` |
| `data/chNN/` | the results measured for the book, from which its numbers were produced |
| `tests/` | the quick tests run by `make check` |

## Reproducing a chapter's measurements

Each kit reruns its chapter's experiments and writes the results to a folder:

```sh
cd code/ch07
sh run_ch07.sh ~/results-ch07
cd ../..
python3 kit/values_ch07.py ~/results-ch07 --machine "my laptop"
```

The values script writes `data/ch07/values.json` with your numbers in place of
ours (use a copy of the repository, or `git checkout data/` to restore ours).
Your results will differ from the book's: comparing them is the point.
The figure scripts, such as `python3 kit/figs_ch07.py figures/ch07`, draw the
chapter's figures from the data; they use the Carlito font if it is
installed (package `fonts-crosextra-carlito` on Ubuntu) and a default font
otherwise.

Some kits need MPI and run many processes on one machine
(`--oversubscribe`); the GPU programs of Chapter 14 need an NVIDIA GPU and
the CUDA Toolkit (`make cuda`), and otherwise can be checked with the CPU
emulators in `code/ch14`.

## If MPI programs run very slowly

On some virtual machines, including cloud and CI machines, Open MPI keeps
waiting processes spinning, and processes that share a core then starve one
another: a run that should take a second can take minutes. Ask waiting
processes to yield the processor, and let the operating system place them:

```sh
mpirun --oversubscribe --bind-to none --mca mpi_yield_when_idle 1 -np 4 ./program
```

For OpenMP threads, `export OMP_WAIT_POLICY=passive` has the same effect.
`make check` uses these settings.

## Feedback

Found a bug, or a result that differs a lot from the book's? Please open an
issue, or send a pull request with a fix.

## License

The code, scripts, and data are released under the MIT License (see
`LICENSE`). The files in `kit/data` are Karl Rupp's Microprocessor Trend
Data, licensed under CC BY 4.0 (see `kit/data/README.md`). The book itself
is not covered by this license.
