"""Student implementation point. Ordinary and weighted A* share one function."""
from heapq import heappop, heappush
from itertools import count
from math import inf, isfinite
from grid import Grid, SearchResult


def a_star(grid: Grid, weight: float) -> SearchResult:
    if not isfinite(weight) or weight < 1:
        raise ValueError("Weight must be finite and at least 1.")

    # You can copy find_path from dijkstra.py below this check and adapt it.
    #
    # 1. Set up best_cost, parent, sequence and expansions as in Dijkstra.
    #    best_cost stores only the cost already paid to reach a cell (g).
    #
    # 2. Queue the start. Its g is zero. For ordinary A*, the priority is
    #    grid.euclidean(grid.start). For weighted A*, multiply this by weight.
    #    Keep the same tuple layout: (priority, next(sequence), g, cell).
    #
    # 3. Pop the lowest priority. Skip it if its g is stale. Otherwise count
    #    one expansion. If this cell is the goal, return
    #    SearchResult(grid.reconstruct(parent), expansions).
    #
    # 4. For each grid.neighbours(current), calculate
    #    new_g = g + grid.move_cost(current, neighbour).
    #    If new_g improves the recorded cost, update best_cost and parent.
    #    Use new_g + weight * grid.euclidean(neighbour) as its queue priority.
    #    Keep new_g itself in the third tuple slot. An improved cell can
    #    re-enter the queue even if it has already been expanded.
    #
    # 5. Repeat until the goal is popped or the queue empties. In the latter
    #    case return SearchResult(None, expansions).
    #
    # Try weight 1 first. Enable RUN_A_STAR in main.py and compare path costs
    # with Dijkstra. Then enable RUN_WEIGHTED_A_STAR to investigate other weights.
    raise NotImplementedError("Implement a_star in student_algorithms.py first.")
