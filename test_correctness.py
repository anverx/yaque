"""Verify Cython solver produces the same results as pure Python."""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

import game
import solver as cy_solver


def py_count_solutions(kingdoms, max_count=2):
    """Pure Python count_solutions reference."""
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

    count = [0]
    def backtrack(kingdom_idx, placed):
        if count[0] >= max_count:
            return
        if kingdom_idx == num_kingdoms:
            count[0] += 1
            return
        for row, col in kingdom_cells[kingdom_idx]:
            if is_valid_placement(placed, row, col):
                placed.append((row, col))
                backtrack(kingdom_idx + 1, placed)
                placed.pop()
                if count[0] >= max_count:
                    return

    backtrack(0, [])
    return count[0]


# Disable Cython solver to test pure Python generation, then compare counts
random.seed(42)
mismatches = 0
checks = 0
for _ in range(50):
    size = random.choice([6, 7, 8])
    # Create a random game with cython disabled so we get an arbitrary kingdoms layout
    g = game.Game(size=size, max_solutions=999, max_attempts=1)
    kingdoms = g.kingdoms

    for max_count in [1, 2, 5, 100]:
        py = py_count_solutions(kingdoms, max_count)
        cy = cy_solver.count_solutions(kingdoms, max_count)
        checks += 1
        if py != cy:
            mismatches += 1
            print(f"MISMATCH size={size} max_count={max_count}: py={py} cy={cy}")

print(f"\nChecked {checks}, mismatches: {mismatches}")
