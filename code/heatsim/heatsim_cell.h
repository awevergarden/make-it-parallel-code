/*
 * heatsim_cell.h -- the per-thread work of HeatSim version 8's kernels.
 * Make It Parallel, companion code (Chapter 14).
 *
 * Every function here runs on the GPU (called from the kernels in
 * heatsim_v8.cu) and on the CPU (called from code/ch14/emulate_v8.c,
 * which replays every block and thread to check the index arithmetic).
 * A block of BX x BY threads updates a BX-wide, BY-tall patch of cells.
 */
#ifndef HEATSIM_CELL_H
#define HEATSIM_CELL_H

#if defined(__CUDACC__) || defined(__CUDA__)
#define HD __host__ __device__
#else
#define HD
#endif

#define BX 32                    /* threads per block along a row    */
#define BY 8                     /* rows of threads per block        */
#define TW (BX + 2)              /* tile width including the halo    */

/* The interior cell (i, j) that thread (tx, ty) of block (bx, by) owns. */
HD static inline void cell_of(int bx, int by, int tx, int ty, int *i, int *j)
{
    *i = 1 + by * BY + ty;
    *j = 1 + bx * BX + tx;
}

/* Simple kernel: read the four neighbors straight from global memory. */
HD static inline void simple_update(const double *cur, double *next, int n,
                                    int bx, int by, int tx, int ty)
{
    int i, j;
    cell_of(bx, by, tx, ty, &i, &j);
    if (i < n - 1 && j < n - 1)             /* skip threads past the edge */
        next[i * n + j] = 0.25 * (cur[(i - 1) * n + j] + cur[(i + 1) * n + j]
                                + cur[i * n + j - 1] + cur[i * n + j + 1]);
}

/* Tiled kernel, phase 1: copy this thread's cell, and the halo cells
   next to the block's edges, into the shared tile. */
HD static inline void tile_load(const double *cur, double *tile, int n,
                                int bx, int by, int tx, int ty)
{
    int i, j;
    cell_of(bx, by, tx, ty, &i, &j);
    int ti = ty + 1, tj = tx + 1;
    if (i > n - 1 || j > n - 1)             /* entirely outside the grid */
        return;
    tile[ti * TW + tj] = cur[i * n + j];
    if (ty == 0)
        tile[0 * TW + tj] = cur[(i - 1) * n + j];
    if (ty == BY - 1 && i + 1 <= n - 1)
        tile[(BY + 1) * TW + tj] = cur[(i + 1) * n + j];
    if (tx == 0)
        tile[ti * TW + 0] = cur[i * n + j - 1];
#ifndef BUG_NO_RIGHT_HALO                    /* Chapter 14's Bug Hunt */
    if (tx == BX - 1 && j + 1 <= n - 1)
        tile[ti * TW + BX + 1] = cur[i * n + j + 1];
#endif
}

/* Tiled kernel, phase 2 (after every thread has loaded): update the cell
   from the tile, in the same order of additions as version 1. */
HD static inline void tile_compute(const double *tile, double *next, int n,
                                   int bx, int by, int tx, int ty)
{
    int i, j;
    cell_of(bx, by, tx, ty, &i, &j);
    int ti = ty + 1, tj = tx + 1;
    if (i < n - 1 && j < n - 1)
        next[i * n + j] = 0.25 * (tile[(ti - 1) * TW + tj] + tile[(ti + 1) * TW + tj]
                                + tile[ti * TW + tj - 1] + tile[ti * TW + tj + 1]);
}

#endif
