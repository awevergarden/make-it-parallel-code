"""hetero.py -- partitioning a matrix among processors of unequal speed.
Make It Parallel, Chapter 13.

Four processors with relative speeds 1, 1, 2, and 4 share the work of
C = A * B on a unit square. Each gets a rectangle whose area matches its
speed. The communication each needs is proportional to its rectangle's
half-perimeter (width + height). Compare horizontal strips with the best
"column-based" arrangement (rectangles stacked in columns), found by
trying every way to group the processors into columns.
Run:  python3 hetero.py      (prints CSV)
"""
from itertools import permutations
from math import sqrt

speeds = [1, 1, 2, 4]
areas = [s / sum(speeds) for s in speeds]

def set_partitions(items):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for part in set_partitions(rest):
        for k in range(len(part)):
            yield part[:k] + [[first] + part[k]] + part[k + 1:]
        yield [[first]] + part

def half_perimeters(columns):
    total = 0.0
    for col in columns:
        w = sum(areas[i] for i in col)          # column width = its share
        total += sum(w + areas[i] / w for i in col)
    return total

strips = sum(1 + a for a in areas)              # full-width strips
best = min(set_partitions(list(range(len(areas)))), key=half_perimeters)
bound = sum(2 * sqrt(a) for a in areas)         # squares: the lower bound
equal_time = max(0.25 / s for s in speeds)      # equal quarters, slowest wins
prop_time = areas[0] / speeds[0]                # proportional: all finish together
print("quantity,value")
print(f"strips_half_perimeter,{strips:.3f}")
print(f"columns_half_perimeter,{half_perimeters(best):.3f}")
print(f"columns_grouping,{' | '.join('+'.join(str(speeds[i]) for i in c) for c in best)}")
print(f"lower_bound,{bound:.3f}")
print(f"equal_split_time,{equal_time:.4f}")
print(f"proportional_time,{prop_time:.4f}")
