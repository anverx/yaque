"""Profile where 8x8 generation actually spends its time."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

import game
import solver as cy_solver


def profile_generation(size=8, num_attempts=5000):
    """Time the components of one round of best-of-N generation."""
    g = game.Game.__new__(game.Game)
    g.size = size
    g.queen_placement = 'backtrack'
    g._cancel_check = None

    t_place = 0.0
    t_kingdoms = 0.0
    t_count = 0.0
    n = num_attempts

    for _ in range(n):
        t = time.perf_counter()
        queens = g._place_queens(size)
        t_place += time.perf_counter() - t

        t = time.perf_counter()
        kingdoms = g.create_kingdoms(queens, 'mixed')
        t_kingdoms += time.perf_counter() - t

        t = time.perf_counter()
        _ = cy_solver.count_solutions(kingdoms, max_count=2)
        t_count += time.perf_counter() - t

    total = t_place + t_kingdoms + t_count
    print(f"\n=== {size}x{size}, {n} iterations ===")
    print(f"  _place_queens:     {t_place:6.2f}s  ({100*t_place/total:5.1f}%)")
    print(f"  create_kingdoms:   {t_kingdoms:6.2f}s  ({100*t_kingdoms/total:5.1f}%)")
    print(f"  count_solutions:   {t_count:6.2f}s  ({100*t_count/total:5.1f}%)")
    print(f"  TOTAL:             {total:6.2f}s")
    print(f"  per-iter:          {1000*total/n:.2f} ms")


if __name__ == '__main__':
    profile_generation(8, 5000)
    profile_generation(9, 5000)
