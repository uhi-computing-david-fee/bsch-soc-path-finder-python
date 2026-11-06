"""Run this file from an IDE or terminal to open the experiment menu."""
import csv
import os
import sys
from dataclasses import replace
from math import isfinite
from pathlib import Path
from time import perf_counter_ns

import dijkstra
import student_algorithms
from grid import Cell, Grid
from grid_generator import GenerationSettings, generate

# SETTINGS: start here. All relative paths use the folder containing main.py.
INPUT_PATH = Path("Data/Examples/terrain-choice.grid")
RESULTS_FILE = Path("Results/results.csv")
REPETITIONS = 5
RUN_A_STAR = False
RUN_WEIGHTED_A_STAR = False
WEIGHTS = [1.25, 1.5, 2.0, 3.0]

# Every size x density x pattern x seed is generated (36 grids by default).
GENERATION = GenerationSettings(
    output_folder=Path("Data/Generated/batch-01"),
    sizes=[(30, 40), (60, 80)],
    obstacle_densities=[0.0, 0.15],
    patterns=["random", "wall", "terrain-band"],
    grids_per_combination=3,
    first_seed=100,
    minimum_cost=1,
    maximum_cost=1,
    gap_rows=3,
    band_width=3,
    band_cost=9,
    start=None,  # Top-left by default. To choose explicitly use Cell(row, column).
    goal=None,   # Bottom-right by default.
)

HEADER = ("Dataset,Rows,Columns,StartRow,StartColumn,GoalRow,GoalColumn,Algorithm,"
          "Weight,Trial,Status,NodesExpanded,Steps,PathCost,OptimalCost,GapPercent,"
          "BoundCost,WithinBound,ElapsedMilliseconds").split(",")


def pick(prompt, paths):
    options = sorted(paths)
    if not options:
        print("No grids found. Generate a batch or add .grid files to Data.")
        return None
    print(prompt)
    for number, option in enumerate(options, 1):
        print(f"{number}  {option}")
    while True:
        answer = input("Number (0 to go back): ").strip()
        if answer == "0":
            return None
        if answer in {str(i) for i in range(1, len(options) + 1)}:
            return options[int(answer) - 1]
        print(f"Choose a number from 0 to {len(options)}.")


def check_result(grid, result, optimum, weight):
    if result.expansions < 1:
        raise ValueError("Count the start expansion.")
    if (result.path is None) != (optimum is None):
        raise ValueError("Reachability differs from Dijkstra.")
    if result.path is None:
        return None
    cost = grid.validate_and_cost(result.path)
    if cost < optimum - 1e-9 * max(1, optimum):
        raise ValueError("Path cost is below the Dijkstra reference.")
    bound = optimum * weight
    if cost > bound + 1e-9 * max(1, bound):
        raise ValueError("Path cost exceeds the expected bound. Check your algorithm.")
    return cost


def run_trials(grid, file, optimum, algorithm, weight, search, writer):
    factor = 1 if weight is None else weight
    check_result(grid, search(), optimum, factor)  # Untimed warm-up.
    for trial in range(1, REPETITIONS + 1):
        start_time = perf_counter_ns()
        result = search()
        milliseconds = (perf_counter_ns() - start_time) / 1_000_000
        cost = check_result(grid, result, optimum, factor)
        found = result.path is not None
        status = "FOUND" if found else "NO_PATH"
        gap = 100 * max(0, cost - optimum) / optimum if optimum else None
        bound = optimum * factor if found else None
        steps = len(result.path) - 1 if found else None
        writer.writerow([file, grid.rows, grid.columns, *grid.start, *grid.goal,
                         algorithm, weight, trial, status, result.expansions, steps, cost,
                         optimum, gap, bound, True if found else None, milliseconds])
        print(f"  {algorithm} w={weight if weight is not None else ''} trial {trial}: "
              f"{status}, cost={cost}, expanded={result.expansions}, ms={milliseconds:.4f}")
        if trial == 1 and found and len(result.path) <= 30:
            print("    " + " -> ".join(f"({r},{c})" for r, c in result.path))


def run_experiment(path):
    if REPETITIONS < 1:
        raise ValueError("Use at least one repetition.")
    if RUN_WEIGHTED_A_STAR and not RUN_A_STAR:
        raise ValueError("Enable RUN_A_STAR first.")
    if any(not isfinite(w) or w <= 1 for w in WEIGHTS):
        raise ValueError("Weighted settings must be finite and greater than 1.")
    if not path.exists():
        raise ValueError(f"Grid file/folder not found: {path.resolve()}")
    files = sorted(path.rglob("*.grid")) if path.is_dir() else [path]
    if not files:
        raise ValueError("No .grid files in the selected folder.")
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = RESULTS_FILE.exists() and RESULTS_FILE.stat().st_size > 0
    if existing:
        with RESULTS_FILE.open(encoding="utf-8-sig", newline="") as old:
            if next(csv.reader(old), []) != HEADER:
                raise ValueError("CSV has a different format. Choose another results filename.")

    with RESULTS_FILE.open("a", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        if not existing:
            writer.writerow(HEADER)
        for file in files:
            grid = Grid.load(file)
            print(f"\n{file}: {grid.rows} rows x {grid.columns} columns")
            print(f"Start {grid.start}; goal {grid.goal}")
            reference = dijkstra.find_path(grid)
            optimum = grid.validate_and_cost(reference.path) if reference.path is not None else None
            run_trials(grid, file, optimum, "Dijkstra", None, lambda: dijkstra.find_path(grid), writer)
            if RUN_A_STAR:
                run_trials(grid, file, optimum, "A*", 1, lambda: student_algorithms.a_star(grid, 1), writer)
            if RUN_WEIGHTED_A_STAR:
                for weight in dict.fromkeys(WEIGHTS):
                    run_trials(grid, file, optimum, "Weighted A*", weight,
                               lambda w=weight: student_algorithms.a_star(grid, w), writer)
    print(f"Results appended to {RESULTS_FILE}. A* enabled: {RUN_A_STAR}; weighted: {RUN_WEIGHTED_A_STAR}.")


def menu():
    while True:
        print("\nPathfinding experiment\n1  Run the default example\n2  Choose a single grid"
              "\n3  Run a folder of grids\n4  Generate a batch of grids\n0  Exit")
        choice = input("Choice: ").strip()
        try:
            if choice == "0":
                return
            if choice == "1":
                run_experiment(INPUT_PATH)
            elif choice in ("2", "3"):
                data = Path("Data")
                if not data.is_dir():
                    raise ValueError(f"Place Data beside main.py in {Path.cwd()}.")
                folder = pick("Choose a grid folder", {file.parent for file in data.rglob("*.grid")})
                if folder is None:
                    continue
                selected = folder if choice == "3" else pick("Choose a grid", folder.glob("*.grid"))
                if selected is not None:
                    run_experiment(selected)
            elif choice == "4":
                output = GENERATION.output_folder
                suffix = 2
                while output.exists():
                    output = Path(f"{GENERATION.output_folder}-{suffix}")
                    suffix += 1
                generate(replace(GENERATION, output_folder=output))
            else:
                print("Choose a number from 0 to 4.")
        except (ValueError, OSError, NotImplementedError) as error:
            print(f"Could not complete this action. {error}")


if __name__ == "__main__":
    # IDE working directories vary. Anchor grid input AND generated output here.
    os.chdir(Path(__file__).resolve().parent)
    print(f"Project folder: {Path.cwd()}")
    try:
        args = sys.argv[1:]
        if not args:
            menu()
        elif args == ["generate"]:
            generate(GENERATION)
        elif args[0] == "run" and len(args) <= 2:
            run_experiment(Path(args[1]) if len(args) == 2 else INPUT_PATH)
        else:
            raise ValueError("Launch without arguments to open the menu.")
    except EOFError:
        pass
    except (ValueError, OSError, NotImplementedError) as error:
        sys.exit(f"Error: {error}")
