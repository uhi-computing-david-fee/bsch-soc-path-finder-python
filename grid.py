"""The shared movement rules, file format and search result."""
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import NamedTuple


class Cell(NamedTuple):
    row: int
    column: int


@dataclass
class SearchResult:
    path: list[Cell] | None
    expansions: int


# Keep the same neighbour order as C#. Together with FIFO priority ties this
# makes both starters select the same route when several have equal cost.
DIRECTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1),
              (-1, 1), (1, 1), (1, -1), (-1, -1)]


class Grid:
    def __init__(self, terrain, start: Cell, goal: Cell):
        self.terrain = tuple(tuple(row) for row in terrain)
        self.rows = len(self.terrain)
        self.columns = len(self.terrain[0]) if self.rows else 0
        if not self.columns or any(len(row) != self.columns for row in self.terrain):
            raise ValueError("Grid rows must be nonempty and equally wide.")
        if any(cost not in range(10) for row in self.terrain for cost in row):
            raise ValueError("Terrain must be 0..9.")
        self.start, self.goal = start, goal
        if not self.is_open(start) or not self.is_open(goal):
            raise ValueError("Start and goal must be traversable and inside the grid.")

    def is_open(self, cell):
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.columns and self.terrain[r][c] != 0

    def can_move(self, source, target):
        if not self.is_open(source) or not self.is_open(target):
            return False
        dr, dc = target.row - source.row, target.column - source.column
        if max(abs(dr), abs(dc)) != 1:
            return False
        if dr and dc:
            return (self.is_open(Cell(target.row, source.column))
                    and self.is_open(Cell(source.row, target.column)))
        return True

    def neighbours(self, source):
        for dr, dc in DIRECTIONS:
            target = Cell(source.row + dr, source.column + dc)
            if self.can_move(source, target):
                yield target

    def move_cost(self, source, target):
        if not self.can_move(source, target):
            raise ValueError("Illegal grid move.")
        diagonal = source.row != target.row and source.column != target.column
        return self.terrain[target.row][target.column] * (sqrt(2) if diagonal else 1)

    def euclidean(self, cell):
        return sqrt((self.goal.row - cell.row) ** 2 + (self.goal.column - cell.column) ** 2)

    def reconstruct(self, parent):
        current = self.goal
        path = [current]
        while current != self.start:
            current = parent.get(current)
            if current is None or len(path) > self.rows * self.columns:
                raise ValueError("Broken or cyclic parent chain.")
            path.append(current)
        return path[::-1]

    def validate_and_cost(self, path):
        if not path or path[0] != self.start or path[-1] != self.goal:
            raise ValueError("Path must run from start to goal.")
        if len(set(path)) != len(path):
            raise ValueError("Path contains a repeated cell.")
        cost = 0.0
        for a, b in zip(path, path[1:]):
            cost += self.move_cost(a, b)
        return cost

    @classmethod
    def load(cls, file):
        lines = [s.strip() for s in Path(file).read_text(encoding="utf-8-sig").splitlines()
                 if s.strip() and not s.lstrip().startswith(";")]
        if len(lines) < 4 or lines[0] != "GRID 1":
            raise ValueError("Expected GRID 1, START, GOAL and map rows.")

        def read_cell(line, label):
            parts = line.split()
            if len(parts) != 3 or parts[0] != label:
                raise ValueError(f"Expected {label} row column.")
            return Cell(int(parts[1]), int(parts[2]))

        symbols = dict(zip("#.123456789", [0, 1, *range(1, 10)]))
        try:
            terrain = [[symbols[ch] for ch in line] for line in lines[3:]]
        except KeyError as exc:
            raise ValueError("Use #, . or digits 1..9 in map rows.") from exc
        return cls(terrain, read_cell(lines[1], "START"), read_cell(lines[2], "GOAL"))

    def save(self, file, comments):
        with Path(file).open("x", encoding="utf-8") as out:
            print("GRID 1", file=out)
            for comment in comments:
                print("; " + comment, file=out)
            print("START", *self.start, file=out)
            print("GOAL", *self.goal, file=out)
            for row in self.terrain:
                print("".join(str(value) if value else "#" for value in row), file=out)
