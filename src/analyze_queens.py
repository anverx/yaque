"""Analyze queen placement distribution to detect bias."""

from __future__ import annotations

import random
from collections import defaultdict


def place_queens_backtrack(size: int) -> list[tuple[int, int]]:
    """OLD algorithm - backtracking with random row order."""
    def is_valid(placed: dict[int, int], row: int, col: int) -> bool:
        for r, c in placed.items():
            if c == col:
                return False
            if abs(r - row) <= 1 and abs(c - col) <= 1:
                return False
        return True

    def backtrack(row_idx: int, rows: list[int], placed: dict[int, int]) -> dict[int, int] | None:
        if row_idx == size:
            return placed.copy()
        row = rows[row_idx]
        cols = list(range(size))
        random.shuffle(cols)
        for col in cols:
            if is_valid(placed, row, col):
                placed[row] = col
                result = backtrack(row_idx + 1, rows, placed)
                if result is not None:
                    return result
                del placed[row]
        return None

    rows = list(range(size))
    random.shuffle(rows)
    result = backtrack(0, rows, {})
    if result is None:
        raise ValueError(f"Cannot place {size} queens")
    return [(r, result[r]) for r in range(size)]


def place_queens_rejection(size: int) -> list[tuple[int, int]]:
    """NEW algorithm - rejection sampling with diagonal filter."""
    mean = (size - 1) / 2.0
    var = sum((r - mean) ** 2 for r in range(size)) / size
    max_corr = 0.5

    for _ in range(10000):
        cols = list(range(size))
        random.shuffle(cols)
        if not all(abs(cols[i] - cols[i + 1]) >= 2 for i in range(size - 1)):
            continue
        cov = sum((r - mean) * (cols[r] - mean) for r in range(size)) / size
        if var > 0 and abs(cov / var) > max_corr:
            continue
        return [(row, cols[row]) for row in range(size)]
    raise ValueError(f"Cannot place {size} queens")


# Use rejection algorithm by default
place_queens = place_queens_rejection


def correlation(queens: list[tuple[int, int]]) -> float:
    """Compute Pearson correlation between row and column indices."""
    n = len(queens)
    mean = (n - 1) / 2.0
    var = sum((r - mean) ** 2 for r in range(n)) / n
    cols = [c for _, c in queens]
    cov = sum((r - mean) * (cols[r] - mean) for r in range(n)) / n
    return cov / var if var > 0 else 0


def analyze_queen_distribution(size: int, num_samples: int = 1000) -> None:
    """Generate many queen placements and analyze distribution."""

    cell_counts: dict[tuple[int, int], int] = defaultdict(int)
    abs_corrs: list[float] = []
    main_diag_count = 0
    anti_diag_count = 0
    near_main_diag = 0
    near_anti_diag = 0

    print(f"Generating {num_samples} queen placements of size {size}x{size}...")

    for i in range(num_samples):
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{num_samples}")

        queens = place_queens(size)
        abs_corrs.append(abs(correlation(queens)))

        for row, col in queens:
            cell_counts[(row, col)] += 1
            if row == col:
                main_diag_count += 1
            if row + col == size - 1:
                anti_diag_count += 1
            if abs(row - col) <= 1:
                near_main_diag += 1
            if abs(row + col - (size - 1)) <= 1:
                near_anti_diag += 1

    total_queens = num_samples * size
    expected_per_cell = num_samples / size

    print(f"\n{'='*50}")
    print(f"QUEEN DISTRIBUTION ANALYSIS ({size}x{size}, {num_samples} samples)")
    print(f"{'='*50}")

    # Heatmap
    print(f"\nCell frequency heatmap (expected ~{expected_per_cell:.0f} per cell):")
    print("    " + "".join(f"{c:6d}" for c in range(size)))
    print("    " + "-" * (size * 6))
    for row in range(size):
        counts = [cell_counts[(row, col)] for col in range(size)]
        print(f"{row:2d} |" + "".join(f"{c:6d}" for c in counts))

    # Diagonal analysis
    print("\nDiagonal analysis:")
    print(f"  Main diagonal (row==col): {main_diag_count} ({100*main_diag_count/total_queens:.1f}%)")
    print(f"  Anti-diagonal: {anti_diag_count} ({100*anti_diag_count/total_queens:.1f}%)")
    print(f"  Expected if uniform: {100/size:.1f}%")

    near_diag_cells_per_row = [min(3, row + 2, size - row + 1) for row in range(size)]
    total_near_cells = sum(near_diag_cells_per_row)
    expected_near_pct = 100 * total_near_cells / (size * size)
    print(f"\nNear-diagonal (within 1 cell of diagonal):")
    print(f"  Near main diagonal: {near_main_diag} ({100*near_main_diag/total_queens:.1f}%)")
    print(f"  Near anti-diagonal: {near_anti_diag} ({100*near_anti_diag/total_queens:.1f}%)")
    print(f"  Expected if uniform: ~{expected_near_pct:.1f}%")

    # Correlation analysis
    avg_corr = sum(abs_corrs) / len(abs_corrs)
    high_corr = sum(1 for c in abs_corrs if c > 0.5)
    print(f"\nCorrelation analysis:")
    print(f"  Mean |corr|: {avg_corr:.3f}")
    print(f"  |corr| > 0.5: {high_corr} ({100*high_corr/num_samples:.1f}%)")
    print(f"  Max |corr|: {max(abs_corrs):.3f}")


def visualize_placements(size: int, count: int = 5) -> None:
    """Show several queen placements."""
    print(f"\n{count} sample {size}x{size} placements:")
    print("-" * 40)

    for _ in range(count):
        queens = place_queens(size)
        queen_set = set(queens)

        for row in range(size):
            line = ""
            for col in range(size):
                if (row, col) in queen_set:
                    line += "Q "
                else:
                    line += ". "
            print(line)

        corr = correlation(queens)
        near_main = sum(1 for r, c in queens if abs(r - c) <= 1)
        print(f"  corr: {corr:+.3f}, near_main: {near_main}")
        print()


def compare_algorithms(size: int, num_samples: int = 2000) -> None:
    """Compare backtracking vs rejection sampling."""
    print(f"\n{'='*60}")
    print(f"COMPARING ALGORITHMS ({size}x{size}, {num_samples} samples each)")
    print(f"{'='*60}")

    for name, func in [("Backtracking", place_queens_backtrack),
                        ("Rejection sampling", place_queens_rejection)]:
        cell_counts: dict[tuple[int, int], int] = defaultdict(int)
        abs_corrs: list[float] = []

        for _ in range(num_samples):
            queens = func(size)
            abs_corrs.append(abs(correlation(queens)))
            for row, col in queens:
                cell_counts[(row, col)] += 1

        expected = num_samples / size
        max_ratios = []
        for row in range(size):
            counts = [cell_counts[(row, col)] for col in range(size)]
            if min(counts) > 0:
                max_ratios.append(max(counts) / min(counts))

        avg_ratio = sum(max_ratios) / len(max_ratios)
        avg_corr = sum(abs_corrs) / len(abs_corrs)
        high_corr = sum(1 for c in abs_corrs if c > 0.5)

        print(f"\n{name}:")
        print(f"  Avg max/min ratio per row: {avg_ratio:.2f}x")
        print(f"  Mean |correlation|: {avg_corr:.3f}")
        print(f"  |corr| > 0.5: {high_corr} ({100*high_corr/num_samples:.1f}%)")


if __name__ == "__main__":
    compare_algorithms(8, num_samples=2000)

    print("\n" + "=" * 60)
    print("REJECTION SAMPLING ANALYSIS")
    print("=" * 60)

    visualize_placements(8, count=5)

    for size in [6, 7, 8]:
        analyze_queen_distribution(size, num_samples=2000)
