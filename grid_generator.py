"""Batch generation is supplied. Students choose the settings in main.py."""
import csv
from dataclasses import dataclass
from itertools import groupby, product
from math import isfinite
from pathlib import Path
from dijkstra import find_path
from grid import Cell, Grid


@dataclass
class GenerationSettings:
    output_folder: Path
    sizes: list[tuple[int, int]]
    obstacle_densities: list[float]
    patterns: list[str]
    grids_per_combination: int
    first_seed: int
    minimum_cost: int
    maximum_cost: int
    gap_rows: int
    band_width: int
    band_cost: int
    start: Cell | None = None
    goal: Cell | None = None


class _SeededRandom:
    """Compatibility with seeded System.Random in the .NET 8 teaching starter.

    Students can skip this class. Using the same sequence lets the same settings
    and seed create the same terrain in both languages.
    """
    maximum = 2**31 - 1

    @staticmethod
    def _subtract(a, b):
        # The source algorithm performs subtraction with signed 32-bit integers.
        difference = (a - b + 2**31) % 2**32 - 2**31
        return difference + _SeededRandom.maximum if difference < 0 else difference

    def __init__(self, seed):
        table = [0] * 56
        previous = 161803398 - min(abs(seed), self.maximum)
        table[55] = previous
        current = 1
        for i in range(1, 55):
            index = 21 * i % 55
            table[index] = current
            current = self._subtract(previous, current)
            previous = table[index]
        for _ in range(4):
            for i in range(1, 56):
                table[i] = self._subtract(table[i], table[1 + (i + 30) % 55])
        self.table = table
        self.left, self.right = 0, 21

    def fraction(self):
        self.left = self.left % 55 + 1
        self.right = self.right % 55 + 1
        value = self._subtract(self.table[self.left], self.table[self.right])
        if value == self.maximum:
            value -= 1
        self.table[self.left] = value
        return value * (1.0 / self.maximum)


def generate(settings: GenerationSettings):
    s = settings
    count = len(s.sizes) * len(s.patterns) * len(s.obstacle_densities) * s.grids_per_combination
    if not 1 <= count <= 10000:
        raise ValueError("Choose between 1 and 10,000 grids per batch.")
    if not 1 <= s.minimum_cost <= s.maximum_cost <= 9 or not 1 <= s.band_cost <= 9:
        raise ValueError("Terrain costs must be in the range 1..9.")
    if not -(2**31) <= s.first_seed <= s.first_seed + s.grids_per_combination - 1 < 2**31:
        raise ValueError("Seeds must fit within a signed 32-bit integer.")
    for density in s.obstacle_densities:
        if not isfinite(density) or not 0 <= density <= 1:
            raise ValueError("Use obstacle probabilities between 0 and 1.")
    for pattern in s.patterns:
        if pattern not in {"random", "wall", "terrain-band"}:
            raise ValueError("Patterns are random, wall or terrain-band.")
    for rows, columns in s.sizes:
        if not (3 <= rows <= 1000 and 3 <= columns <= 1000
                and 1 <= s.gap_rows < rows and 1 <= s.band_width < columns - 1):
            raise ValueError("Sizes must be 3..1000 and the gap and band must fit.")
        for cell in (s.start, s.goal):
            if cell is not None and not (0 <= cell.row < rows and 0 <= cell.column < columns):
                raise ValueError("Start and goal must fit every selected size.")

    folder = Path(s.output_folder)
    folder.mkdir(parents=True, exist_ok=True)
    if any(folder.iterdir()):
        raise ValueError("The output folder must be empty. Choose another batch folder.")
    seeds = range(s.first_seed, s.first_seed + s.grids_per_combination)
    combinations = product(s.sizes, s.obstacle_densities, s.patterns, seeds)
    with (folder / "manifest.csv").open("x", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow("File Rows Columns Pattern Seed ObstacleProbability ActualObstacleFraction MinimumCost MaximumCost GapRows BandWidth BandCost Reachable OptimalCost".split())
        for index, ((rows, columns), density, pattern, seed) in enumerate(combinations, 1):
            rng = _SeededRandom(seed)
            terrain = []
            for r in range(rows):
                row = []
                for c in range(columns):
                    # Draw both values, including when the first draw blocks a cell.
                    blocked = rng.fraction() < density
                    cost = s.minimum_cost + int(rng.fraction() * (s.maximum_cost - s.minimum_cost + 1))
                    row.append(0 if blocked else cost)
                terrain.append(row)
            for r in range(rows - s.gap_rows):
                if pattern == "wall":
                    terrain[r][columns // 2] = 0
                elif pattern == "terrain-band":
                    first = (columns - s.band_width) // 2
                    for c in range(first, first + s.band_width):
                        if terrain[r][c]:
                            terrain[r][c] = s.band_cost
            start = s.start or Cell(0, 0)
            goal = s.goal or Cell(rows - 1, columns - 1)
            for cell in (start, goal):
                terrain[cell.row][cell.column] = s.minimum_cost
            grid = Grid(terrain, start, goal)
            reference = find_path(grid)
            reachable = reference.path is not None
            optimum = grid.validate_and_cost(reference.path) if reachable else None
            fraction = sum(row.count(0) for row in terrain) / (rows * columns)
            name = f"grid-{index:04}-{pattern}-{rows}x{columns}-seed{seed}.grid"
            grid.save(folder / name, [
                "Generated by Python PathfindingStarter v1 using the .NET 8 compatible seed sequence.",
                f"pattern={pattern}; seed={seed}; rows={rows}; columns={columns}",
                f"obstacleProbability={density}; actualObstacleFraction={fraction}",
                f"backgroundCosts={s.minimum_cost}..{s.maximum_cost}; gapRows={s.gap_rows}; bandWidth={s.band_width}; bandCost={s.band_cost}",
                "Endpoints forced open at minimum cost. All generated grids are saved.",
                f"reachable={reachable}; DijkstraCost={optimum if reachable else 'NA'}",
                "Move cost = destination terrain times 1 or sqrt(2); no corner cutting.",
            ])
            _save_preview(folder / (name + ".svg"), grid)
            writer.writerow([name, rows, columns, pattern, seed, density, fraction, s.minimum_cost,
                             s.maximum_cost, s.gap_rows, s.band_width, s.band_cost, reachable, optimum])
            print(f"Saved {name}: {'reachable' if reachable else 'NO PATH'}")
    print(f"Saved {count} grids, previews and manifest.csv in {folder}.")


def _save_preview(file, grid):
    colours = ["#222831", "#f4f5f7", "#fff0d6", "#ffe0b2", "#ffcc80",
               "#ffb74d", "#ffa726", "#fb8c00", "#ef6c00", "#d84315"]
    with file.open("x", encoding="utf-8") as out:
        print(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {grid.columns} {grid.rows}" width="800" height="800" shape-rendering="crispEdges">', file=out)
        for r, row in enumerate(grid.terrain):
            c = 0
            for value, group in groupby(row):
                width = sum(1 for _ in group)
                print(f'<rect x="{c}" y="{r}" width="{width}" height="1" fill="{colours[value]}"/>', file=out)
                c += width
        for cell, colour in [(grid.start, "#00c853"), (grid.goal, "#e91e63")]:
            print(f'<rect x="{cell.column}" y="{cell.row}" width="1" height="1" fill="{colour}"/>', file=out)
        print("</svg>", file=out)
