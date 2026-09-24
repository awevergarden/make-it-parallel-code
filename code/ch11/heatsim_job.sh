#!/bin/bash
# heatsim_job.sh -- an example Slurm batch script for HeatSim v6.
# Make It Parallel, Chapter 11. Submit with:  sbatch heatsim_job.sh
# Partition names, module names, and limits differ between clusters;
# check your site's documentation.
#SBATCH --job-name=heatsim
#SBATCH --nodes=4                 # four machines
#SBATCH --ntasks-per-node=16      # 16 MPI processes on each
#SBATCH --time=00:10:00           # wall-clock limit (hh:mm:ss)
#SBATCH --output=heatsim-%j.out   # %j becomes the job number

module load openmpi               # site-specific module name
mpicc -std=c17 -O2 -fopenmp-simd -o heatsim_v6 heatsim_v6.c
srun ./heatsim_v6 8192 1000       # srun starts all 64 processes
