"""Benchmark full puzzle generation with the Cython solver."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

import game
print(f"Cython solver loaded: {game._cy_solver is not None}")


def bench(size, runs=5):
    print(f"\n=== Size {size}x{size} (Cython) ===")
    times = []
    for i in range(runs):
        t = time.perf_counter()
        g = game.Game(size=size)
        dt = time.perf_counter() - t
        times.append(dt)
        print(f"  run {i+1}: {dt:.3f}s ({g.attempts} attempts, {g.num_solutions} sols)")
    print(f"  mean: {sum(times)/len(times):.3f}s")


if __name__ == '__main__':
    for size in [8, 9]:
        bench(size, runs=5)
