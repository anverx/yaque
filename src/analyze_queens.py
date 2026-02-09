"""Analyze queen placement distribution to detect bias."""

from __future__ import annotations

import random
from collections import defaultdict


def place_queens_old(size: int) -> list[tuple[int, int]]:
    """OLD algorithm - row-by-row from row 0."""
    def is_valid(queens: list[tuple[int, int]], row: int, col: int) -> bool:
        for r, c in queens:
            if c == col:
                return False
            if abs(r - row) <= 1 and abs(c - col) <= 1:
                return False
        return True

    def backtrack(row: int, queens: list[tuple[int, int]]) -> list[tuple[int, int]] | None:
        if row == size:
            return queens[:]
        cols = list(range(size))
        random.shuffle(cols)
        for col in cols:
            if is_valid(queens, row, col):
                queens.append((row, col))
                result = backtrack(row + 1, queens)
                if result is not None:
                    return result
                queens.pop()
        return None

    result = backtrack(0, [])
    if result is None:
        raise ValueError(f"Cannot place {size} queens")
    return result


def place_queens_new(size: int) -> list[tuple[int, int]]:
    """NEW algorithm - random row order."""
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


# Use new algorithm by default
place_queens = place_queens_new


def analyze_queen_distribution(size: int, num_samples: int = 1000) -> None:
    """Generate many queen placements and analyze distribution."""

    # Count how often each cell has a queen
    cell_counts: dict[tuple[int, int], int] = defaultdict(int)

    # Count column usage per row
    row_col_counts: dict[int, dict[int, int]] = {r: defaultdict(int) for r in range(size)}

    # Track diagonal patterns
    main_diag_count = 0
    anti_diag_count = 0
    near_main_diag = 0
    near_anti_diag = 0

    print(f"Generating {num_samples} queen placements of size {size}x{size}...")

    for i in range(num_samples):
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{num_samples}")

        queens = place_queens(size)

        for row, col in queens:
            cell_counts[(row, col)] += 1
            row_col_counts[row][col] += 1

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

    # Min/max per row
    print(f"\nMin/Max frequency per row:")
    for row in range(size):
        counts = [cell_counts[(row, col)] for col in range(size)]
        min_c, max_c = min(counts), max(counts)
        ratio = max_c / min_c if min_c > 0 else float('inf')
        print(f"  Row {row}: min={min_c}, max={max_c}, ratio={ratio:.2f}x")

    # Column totals
    print(f"\nColumn totals (expected {num_samples} each):")
    col_totals = [sum(cell_counts[(r, c)] for r in range(size)) for c in range(size)]
    print("  " + "  ".join(f"c{c}:{t}" for c, t in enumerate(col_totals)))

    # Diagonal analysis
    print(f"\nDiagonal analysis:")
    print(f"  Main diagonal (row==col): {main_diag_count} ({100*main_diag_count/total_queens:.1f}%)")
    print(f"  Anti-diagonal: {anti_diag_count} ({100*anti_diag_count/total_queens:.1f}%)")
    print(f"  Expected if uniform: {100/size:.1f}%")

    print(f"\nNear-diagonal (within 1 cell of diagonal):")
    # Calculate expected: for each row, how many cells are within 1 of main diagonal?
    # Row 0: cols 0,1 (2 cells); Row 1: cols 0,1,2 (3 cells); ...; Row n-1: cols n-2,n-1 (2 cells)
    near_diag_cells_per_row = [min(3, row + 2, size - row + 1) for row in range(size)]
    total_near_cells = sum(near_diag_cells_per_row)
    expected_near_pct = 100 * total_near_cells / (size * size)
    print(f"  Near main diagonal: {near_main_diag} ({100*near_main_diag/total_queens:.1f}%)")
    print(f"  Near anti-diagonal: {near_anti_diag} ({100*near_anti_diag/total_queens:.1f}%)")
    print(f"  Expected if uniform: ~{expected_near_pct:.1f}%")


def visualize_placements(size: int, count: int = 5) -> None:
    """Show several queen placements."""
    print(f"\n{count} sample {size}x{size} placements:")
    print("-" * 40)

    for i in range(count):
        queens = place_queens(size)
        queen_set = set(queens)

        # Print board
        for row in range(size):
            line = ""
            for col in range(size):
                if (row, col) in queen_set:
                    line += "Q "
                else:
                    line += ". "
            print(line)

        # Stats
        main_diag = sum(1 for r, c in queens if r == c)
        anti_diag = sum(1 for r, c in queens if r + c == size - 1)
        near_main = sum(1 for r, c in queens if abs(r - c) <= 1)

        print(f"  diag: {main_diag}, anti: {anti_diag}, near_main: {near_main}")
        print()


def compare_algorithms(size: int, num_samples: int = 2000) -> None:
    """Compare old vs new algorithm."""
    print(f"\n{'='*60}")
    print(f"COMPARING ALGORITHMS ({size}x{size}, {num_samples} samples each)")
    print(f"{'='*60}")

    for name, func in [("OLD (row-by-row)", place_queens_old), ("NEW (random row order)", place_queens_new)]:
        cell_counts: dict[tuple[int, int], int] = defaultdict(int)

        for _ in range(num_samples):
            queens = func(size)
            for row, col in queens:
                cell_counts[(row, col)] += 1

        expected = num_samples / size

        # Calculate max ratio per row
        max_ratios = []
        for row in range(size):
            counts = [cell_counts[(row, col)] for col in range(size)]
            if min(counts) > 0:
                max_ratios.append(max(counts) / min(counts))

        avg_ratio = sum(max_ratios) / len(max_ratios)
        worst_ratio = max(max_ratios)

        print(f"\n{name}:")
        print(f"  Avg max/min ratio per row: {avg_ratio:.2f}x")
        print(f"  Worst row ratio: {worst_ratio:.2f}x")

        # Show corner vs center bias
        corners = sum(cell_counts[(r, c)] for r, c in [(0, 0), (0, size-1), (size-1, 0), (size-1, size-1)])
        center_cells = [(size//2-1, size//2-1), (size//2-1, size//2), (size//2, size//2-1), (size//2, size//2)]
        center = sum(cell_counts[(r, c)] for r, c in center_cells)
        print(f"  4 corners total: {corners} (expected {4*expected:.0f})")
        print(f"  4 center cells total: {center} (expected {4*expected:.0f})")


if __name__ == "__main__":
    # Compare algorithms
    compare_algorithms(8, num_samples=2000)

    print("\n" + "=" * 60)
    print("DETAILED ANALYSIS OF NEW ALGORITHM")
    print("=" * 60)

    # Show sample placements with new algorithm
    visualize_placements(8, count=5)

    # Detailed analysis
    for size in [8]:
        analyze_queen_distribution(size, num_samples=2000)
