"""topology.py -- properties of five network topologies with 64 nodes.
Make It Parallel, Chapter 11.

For each topology, builds the graph and computes the node degree, the
number of links, the diameter and average distance (by breadth-first
search), and the number of links cut when the nodes are split into two
halves along the topology's natural dividing line. For these regular
topologies that natural cut gives the bisection width.
Run:  python3 topology.py        (prints CSV)
"""
from collections import deque
from itertools import product

P = 64

def ring():
    return {v: {(v - 1) % P, (v + 1) % P} for v in range(P)}, lambda v: v < P // 2

def mesh(torus):
    k = 8
    g = {}
    for r, c in product(range(k), range(k)):
        nb = set()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if torus:
                nb.add((rr % k) * k + cc % k)
            elif 0 <= rr < k and 0 <= cc < k:
                nb.add(rr * k + cc)
        g[r * k + c] = nb
    return g, lambda v: v % k < k // 2          # split into left and right halves

def hypercube():
    d = 6
    return {v: {v ^ (1 << i) for i in range(d)} for v in range(P)}, lambda v: v < P // 2

def full():
    return {v: set(range(P)) - {v} for v in range(P)}, lambda v: v < P // 2

def props(name, g, half):
    degrees = sorted({len(n) for n in g.values()})
    links = sum(len(n) for n in g.values()) // 2
    total, diameter = 0, 0
    for s in g:                                  # BFS from every node
        dist = {s: 0}
        q = deque([s])
        while q:
            u = q.popleft()
            for w in g[u]:
                if w not in dist:
                    dist[w] = dist[u] + 1
                    q.append(w)
        diameter = max(diameter, max(dist.values()))
        total += sum(dist.values())
    avg = total / (P * (P - 1))
    cut = sum(1 for u in g for w in g[u] if u < w and half(u) != half(w))
    deg = str(degrees[0]) if len(degrees) == 1 else f"{degrees[0]}-{degrees[-1]}"
    print(f"{name},{deg},{links},{diameter},{avg:.2f},{cut}")

print("topology,degree,links,diameter,avg_distance,bisection")
props("ring", *ring())
props("mesh 8x8", *mesh(False))
props("torus 8x8", *mesh(True))
props("hypercube 6D", *hypercube())
props("fully connected", *full())
