"""Benchmark pure-Python vs Cython solver.

Run after building:
    python setup_solver.py build_ext --inplace
    python bench_solver.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from game import Game
import yaque_solver as cy_solver


def run_python_solver(kingdoms, max_count=100):
    """Replicates Game.find_all_solutions exactly."""
    no = len(kingdoms)
    num_kingdoms = no

    kingdom_cells = [[] for _ in range(num_kingdoms)]
    for row in range(no):
        for col in range(no):
            k = kingdoms[row][col]
            kingdom_cells[k].append((row, col))

    def is_valid_placement(placed, row, col):
        for placed_row, placed_col in placed:
            if placed_row == row or placed_col == col:
                return False
            if abs(placed_row - row) <= 1 and abs(placed_col - col) <= 1:
                return False
        return True

    solutions = []

    def backtrack(kingdom_idx, placed):
        if len(solutions) >= max_count:
            return
        if kingdom_idx == num_kingdoms:
            solutions.append(list(placed))
            return
        for row, col in kingdom_cells[kingdom_idx]:
            if is_valid_placement(placed, row, col):
                placed.append((row, col))
                backtrack(kingdom_idx + 1, placed)
                placed.pop()
                if len(solutions) >= max_count:
                    return

    backtrack(0, [])
    return solutions


def bench(size, max_count=100, runs=5):
    print(f"\n=== Size {size}x{size}, max_count={max_count}, runs={runs} ===")
    # Generate a real game to benchmark on
    game = Game(size=size)
    kingdoms = game.kingdoms

    # Python: total time over all runs
    py_solutions = None
    t = time.perf_counter()
    for _ in range(runs):
        py_solutions = run_python_solver(kingdoms, max_count)
    py_total = time.perf_counter() - t

    # Cython: total time over all runs
    cy_solutions = None
    t = time.perf_counter()
    for _ in range(runs):
        cy_solutions = cy_solver.find_all_solutions(kingdoms, max_count)
    cy_total = time.perf_counter() - t

    speedup = py_total / cy_total if cy_total > 0 else float('inf')

    print(f"  Python: {py_total:7.3f}s total ({py_total*1000/runs:.3f} ms/call)")
    print(f"  Cython: {cy_total:7.3f}s total ({cy_total*1000/runs:.3f} ms/call)")
    print(f"  Speedup: {speedup:.1f}x")
    print(f"  Solutions: py={len(py_solutions)} cy={len(cy_solutions)}")

    # Sanity check: same solutions (set of frozensets, order-independent)
    py_set = {frozenset(s) for s in py_solutions}
    cy_set = {frozenset(s) for s in cy_solutions}
    if py_set != cy_set:
        print(f"  WARNING: solutions differ!")
        print(f"    py-only: {py_set - cy_set}")
        print(f"    cy-only: {cy_set - py_set}")
    else:
        print(f"  OK Solutions match")


if __name__ == '__main__':
    for size in [6, 7, 8]:
        bench(size, max_count=100, runs=1000)
