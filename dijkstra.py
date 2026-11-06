"""Supplied exact baseline. Adapt this bookkeeping in student_algorithms.py."""
from heapq import heappop, heappush
from itertools import count
from math import inf
from grid import Grid, SearchResult


def find_path(grid: Grid) -> SearchResult:
    best_cost = {grid.start: 0.0}
    parent = {}
    sequence = count()
    expansions = 0

    # Entries contain (priority, insertion order, g when queued, cell).
    # The sequence number makes equal priorities first-in, first-out.
    frontier = [(0.0, next(sequence), 0.0, grid.start)]
    while frontier:
        _, _, g, current = heappop(frontier)
        if g > best_cost[current]:
            continue  # An improved entry superseded this one.

        expansions += 1  # Includes the goal. Stale entries are excluded.
        if current == grid.goal:
            return SearchResult(grid.reconstruct(parent), expansions)

        for neighbour in grid.neighbours(current):
            new_g = g + grid.move_cost(current, neighbour)
            if new_g < best_cost.get(neighbour, inf):
                best_cost[neighbour] = new_g
                parent[neighbour] = current
                heappush(frontier, (new_g, next(sequence), new_g, neighbour))

    return SearchResult(None, expansions)
