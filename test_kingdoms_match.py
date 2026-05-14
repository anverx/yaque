"""Verify Cython create_kingdoms produces identical results to Python."""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

import game
import solver as cy_solver


def py_create_kingdoms(queens, size, kingdom_strategy):
    """Pure Python reference — copied from the original Game.create_kingdoms."""
    g = game.Game.__new__(game.Game)
    g.size = size
    # Disable cython for this call
    saved = game._cy_solver
    game._cy_solver = None
    try:
        return g.create_kingdoms(queens, kingdom_strategy)
    finally:
        game._cy_solver = saved


mismatches = 0
checks = 0
for seed in range(100):
    for size in [6, 7, 8]:
        for strategy in ['classic', 'jagged', 'mixed']:
            random.seed(seed)
            queens = game.Game.place_queens(game.Game.__new__(game.Game), size)

            random.seed(seed + 1000)  # different seed for kingdom growth
            py_result = py_create_kingdoms(queens, size, strategy)

            random.seed(seed + 1000)
            cy_result = cy_solver.create_kingdoms(queens, size, strategy)

            checks += 1
            if py_result != cy_result:
                mismatches += 1
                if mismatches <= 3:
                    print(f"MISMATCH seed={seed} size={size} strat={strategy}")
                    print(f"  py: {py_result}")
                    print(f"  cy: {cy_result}")

print(f"\nChecked {checks}, mismatches: {mismatches}")
