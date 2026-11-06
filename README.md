# Pathfinding Experiment (Python)

A console starter for investigating search effort and path quality in Science of Computing & Digital Media (UI110010). Dijkstra supplies the optimal cost for each grid. Your task is to implement Euclidean A*, then use the same function to investigate heuristic weighting.

## Run the project

Extract the entire ZIP and run `main.py` in your IDE, or open a terminal in its folder and run:

```bash
python main.py
```

Requires Python 3.10 or later and uses only the standard library. On systems where the interpreter is called `python3`, use `python3 main.py`. All data, generated grids and results are located relative to `main.py`, including when an IDE uses another working directory.

| Choice | Action |
|---|---|
| 1 | Run the default terrain example |
| 2 | Choose a folder and then one grid by number |
| 3 | Run every grid in a chosen folder, including subfolders |
| 4 | Generate a fresh batch from the settings in `main.py` |
| 0 | Exit, or go back from a selection list |

## What is supplied

| File | Purpose |
|---|---|
| `main.py` | Menu, experiment settings, validation, timing and CSV |
| `grid.py` | Grid files, neighbours, move costs, Euclidean estimate and path reconstruction |
| `dijkstra.py` | Working exact search and expansion counter |
| `student_algorithms.py` | Your A* and weighted A* implementation point |
| `grid_generator.py` | Batch generation, previews and reference costs |

## Where to add your algorithm

Open `student_algorithms.py`. The function contains a step-by-step checklist:

```python
def a_star(grid: Grid, weight: float) -> SearchResult:
```

1. Start with `find_path` in `dijkstra.py`. You can copy its bookkeeping into `a_star`. For ordinary A*, give a cell priority equal to its cost so far plus `grid.euclidean(cell)`. The queue entry keeps that priority and the cost so far in separate positions.
2. Set `RUN_A_STAR = True` in `main.py`, restart, and try menu choice **1**. The runner calls your function with weight 1 and checks its path cost against Dijkstra. Two equally cheap paths can take different routes.
3. Multiply the estimate by `weight` when queuing the start and each improved neighbour. Set `RUN_WEIGHTED_A_STAR = True`, choose `WEIGHTS` and restart. The menu runs your function once per weight in each trial.

Use the same neighbour order and queue tie rule as Dijkstra. Count a cell after removing a current entry from the queue, including the goal. Skip stale entries and let improved cells return to the queue. Return `SearchResult(grid.reconstruct(parent), expansions)` at the goal or `SearchResult(None, expansions)` if the queue empties.

## Make your own environments

Edit `GENERATION` at the top of `main.py`. Choose **4** after restarting. Every combination of size, obstacle probability, pattern and seed produces one saved grid. Defaults produce 36. The menu creates a fresh folder for each batch. Use **2** or **3** to select the new files immediately.

| Setting | What you choose |
|---|---|
| `sizes`, `start`, `goal` | Grid dimensions and endpoints in zero-based (row, column) order |
| `obstacle_densities` | Background probability of an obstacle |
| `patterns` | Random terrain, a central wall, or an expensive central terrain band |
| `first_seed`, `grids_per_combination` | First seed and number of instances per combination |
| `minimum_cost`, `maximum_cost` | Inclusive range of background terrain costs, from 1 to 9 |
| `gap_rows`, `band_width`, `band_cost` | Bottom rows left outside the added feature, and width and cost of a terrain band |

Background obstacles can still occupy the gap. Endpoints are always open at minimum cost. Every grid is saved, including unreachable ones. The batch manifest records reachability, optimal cost and the actual obstacle fraction. SVG previews show the layout. Use the saved files as your inputs when comparing algorithms or languages.

## Measurements

Each enabled configuration gets one untimed warm-up and `REPETITIONS` timed runs. Search setup and path reconstruction are timed. Loading, validation, final costing and output are outside the timer. `NodesExpanded` counts non-stale queue removals, including the goal and any re-expansions.

Results append to `Results/results.csv` with the same columns as the C# starter. They include path cost, steps, expansions, elapsed milliseconds and percentage gap relative to Dijkstra. The gap is blank for unreachable goals or zero optimal cost. A failed path or bound check stops that action before writing the failed trial.

The generators use the same seeded sequence and movement rules. For a comparison between languages, keep the exact grid files and compare cost and expansion counts. Record timings separately for each runtime.
