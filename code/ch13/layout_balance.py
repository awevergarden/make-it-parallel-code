"""layout_balance.py -- how evenly do block and block-cyclic layouts
share the work of an LU-style factorization?
Make It Parallel, Chapter 13.

In step k of Gaussian elimination on an N x N matrix, only the trailing
submatrix of rows and columns k+1..N-1 is updated. Count, for each
process of a 2 x 2 grid, how many element updates it performs over all
steps, for a 2D block layout and a 2D block-cyclic layout.
Run:  python3 layout_balance.py     (prints CSV)
"""
N, PR, PC = 64, 2, 2

def owner_block(i, j):
    return (i // (N // PR)) * PC + j // (N // PC)

def owner_cyclic(i, j, b=4):
    return ((i // b) % PR) * PC + (j // b) % PC

print("layout,process,updates")
for name, own in (("block", owner_block), ("block-cyclic", owner_cyclic)):
    work = [0] * (PR * PC)
    for k in range(N):
        for i in range(k + 1, N):
            for j in range(k + 1, N):
                work[own(i, j)] += 1
    for p_, w in enumerate(work):
        print(f"{name},{p_},{w}")
