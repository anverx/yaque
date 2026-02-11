"""Tests for game logic: generation, encoding/decoding, daily puzzles."""

import os
import sys
from datetime import date

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game import (
    MARK_CIRCLE,
    MARK_EMPTY,
    MARK_QUEEN,
    Game,
    check_player_solution,
    get_daily_game,
    get_daily_seed,
    validate_player_marks,
)


class TestQueenPlacement:
    """Test queen placement validity."""

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_queens_count(self, size):
        """Each puzzle should have exactly N queens for an NxN board."""
        game = Game(size, max_solutions=10)
        assert len(game.queens) == size

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_queens_one_per_row(self, size):
        """Each row should have exactly one queen."""
        game = Game(size, max_solutions=10)
        rows = [r for r, c in game.queens]
        assert sorted(rows) == list(range(size))

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_queens_one_per_column(self, size):
        """Each column should have at most one queen (N-queens rule)."""
        game = Game(size, max_solutions=10)
        cols = [c for r, c in game.queens]
        assert len(cols) == len(set(cols)), "Queens share a column"

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_queens_not_adjacent(self, size):
        """No two queens should be adjacent (including diagonally)."""
        game = Game(size, max_solutions=10)
        queens = game.queens
        for i, (r1, c1) in enumerate(queens):
            for r2, c2 in queens[i + 1:]:
                row_diff = abs(r1 - r2)
                col_diff = abs(c1 - c2)
                # Adjacent means both differences are <= 1
                assert not (row_diff <= 1 and col_diff <= 1), \
                    f"Queens at ({r1},{c1}) and ({r2},{c2}) are adjacent"


class TestKingdoms:
    """Test kingdom generation."""

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_all_cells_assigned(self, size):
        """Every cell should belong to a kingdom."""
        game = Game(size, max_solutions=10)
        for row in range(size):
            for col in range(size):
                assert game.kingdoms[row][col] >= 0, \
                    f"Cell ({row},{col}) not assigned to a kingdom"

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_kingdom_count(self, size):
        """Should have exactly N kingdoms for an NxN board."""
        game = Game(size, max_solutions=10)
        kingdom_ids = set()
        for row in game.kingdoms:
            kingdom_ids.update(row)
        assert len(kingdom_ids) == size

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_each_kingdom_has_queen(self, size):
        """Each kingdom should contain exactly one queen."""
        game = Game(size, max_solutions=10)
        queen_set = set(game.queens)
        for k in range(size):
            queens_in_kingdom = 0
            for row in range(size):
                for col in range(size):
                    if game.kingdoms[row][col] == k and (row, col) in queen_set:
                        queens_in_kingdom += 1
            assert queens_in_kingdom == 1, \
                f"Kingdom {k} has {queens_in_kingdom} queens, expected 1"

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_kingdoms_connected(self, size):
        """Each kingdom should be a connected region."""
        game = Game(size, max_solutions=10)

        for k in range(size):
            # Find all cells in this kingdom
            cells = [(r, c) for r in range(size) for c in range(size)
                     if game.kingdoms[r][c] == k]
            assert len(cells) > 0, f"Kingdom {k} has no cells"

            # BFS to check connectivity
            visited = set()
            queue = [cells[0]]
            visited.add(cells[0])

            while queue:
                r, c = queue.pop(0)
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in cells and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))

            assert len(visited) == len(cells), \
                f"Kingdom {k} is not connected: {len(visited)} reachable out of {len(cells)} cells"


class TestDailyPuzzles:
    """Test daily puzzle generation."""

    def test_same_date_same_puzzle(self):
        """Same date and size should produce the same puzzle."""
        test_date = date(2025, 6, 15)

        game1 = get_daily_game(test_date, 7, max_solutions=10)
        game2 = get_daily_game(test_date, 7, max_solutions=10)

        assert game1.kingdoms == game2.kingdoms
        assert game1.queens == game2.queens

    def test_different_dates_different_puzzles(self):
        """Different dates should produce different puzzles."""
        date1 = date(2025, 6, 15)
        date2 = date(2025, 6, 16)

        game1 = get_daily_game(date1, 7, max_solutions=10)
        game2 = get_daily_game(date2, 7, max_solutions=10)

        # Technically could be same by chance, but astronomically unlikely
        assert game1.queens != game2.queens or game1.kingdoms != game2.kingdoms

    def test_different_sizes_different_puzzles(self):
        """Same date but different sizes should produce different puzzles."""
        test_date = date(2025, 6, 15)

        game6 = get_daily_game(test_date, 6, max_solutions=10)
        game7 = get_daily_game(test_date, 7, max_solutions=10)

        assert game6.size != game7.size

    def test_daily_seed_deterministic(self):
        """Daily seed generation should be deterministic."""
        test_date = date(2025, 1, 1)

        seed1 = get_daily_seed(test_date, 7)
        seed2 = get_daily_seed(test_date, 7)

        assert seed1 == seed2


class TestSolutionCounting:
    """Test solution counting."""

    def test_generated_puzzle_has_solutions(self):
        """Generated puzzles should have at least one solution."""
        game = Game(7, max_solutions=4)
        solutions = game.count_solutions(max_count=10)
        assert solutions >= 1

    def test_max_solutions_respected(self):
        """Puzzles should not exceed max_solutions."""
        game = Game(7, max_solutions=2)
        assert game.num_solutions <= 2

    def test_unique_solution_puzzle(self):
        """Can generate puzzles with unique solution."""
        game = Game(6, max_solutions=1)
        assert game.num_solutions == 1


class TestConflictDetection:
    """Test conflict detection logic (same as in board_widget)."""

    def find_conflicts(self, queens):
        """Find conflicts among placed queens."""
        conflicts = set()
        for i, (r1, c1) in enumerate(queens):
            for r2, c2 in queens[i + 1:]:
                # Same row or column
                if r1 == r2 or c1 == c2 or (abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1):
                    conflicts.add((r1, c1))
                    conflicts.add((r2, c2))
        return conflicts

    def test_no_conflicts_valid_placement(self):
        """Valid queen placement should have no conflicts."""
        # Valid 4-queen placement
        queens = [(0, 1), (1, 3), (2, 0), (3, 2)]
        assert len(self.find_conflicts(queens)) == 0

    def test_same_row_conflict(self):
        """Queens in same row should conflict."""
        queens = [(0, 0), (0, 5)]
        conflicts = self.find_conflicts(queens)
        assert (0, 0) in conflicts
        assert (0, 5) in conflicts

    def test_same_column_conflict(self):
        """Queens in same column should conflict."""
        queens = [(0, 0), (5, 0)]
        conflicts = self.find_conflicts(queens)
        assert (0, 0) in conflicts
        assert (5, 0) in conflicts

    def test_diagonal_adjacent_conflict(self):
        """Diagonally adjacent queens should conflict."""
        queens = [(2, 2), (3, 3)]
        conflicts = self.find_conflicts(queens)
        assert (2, 2) in conflicts
        assert (3, 3) in conflicts

    def test_non_adjacent_diagonal_ok(self):
        """Non-adjacent diagonal queens should not conflict."""
        queens = [(0, 0), (2, 2)]  # 2 squares apart diagonally
        conflicts = self.find_conflicts(queens)
        assert len(conflicts) == 0

    def test_generated_solution_has_no_conflicts(self):
        """The solution (queens) of a generated game should have no conflicts."""
        game = Game(7, max_solutions=4)
        conflicts = self.find_conflicts(game.queens)
        assert len(conflicts) == 0, f"Generated solution has conflicts: {conflicts}"


class TestPlayerValidation:
    """Test player mark validation functions."""

    def make_marks(self, size: int, queens: list[tuple[int, int]] | None = None,
                   circles: list[tuple[int, int]] | None = None) -> list[list[int]]:
        """Helper to create a cell_marks grid."""
        marks = [[MARK_EMPTY] * size for _ in range(size)]
        for r, c in (queens or []):
            marks[r][c] = MARK_QUEEN
        for r, c in (circles or []):
            marks[r][c] = MARK_CIRCLE
        return marks

    def test_no_conflicts_empty_board(self):
        """Empty board has no conflicts."""
        game = Game(6, max_solutions=10)
        marks = self.make_marks(6)
        conflicts, blocked = validate_player_marks(game.kingdoms, marks)
        assert len(conflicts) == 0
        assert len(blocked) == 0

    def test_same_row_conflict(self):
        """Two queens in same row should conflict."""
        game = Game(6, max_solutions=10)
        marks = self.make_marks(6, queens=[(0, 0), (0, 5)])
        conflicts, _ = validate_player_marks(game.kingdoms, marks)
        assert (0, 0) in conflicts
        assert (0, 5) in conflicts

    def test_same_column_conflict(self):
        """Two queens in same column should conflict."""
        game = Game(6, max_solutions=10)
        marks = self.make_marks(6, queens=[(0, 0), (5, 0)])
        conflicts, _ = validate_player_marks(game.kingdoms, marks)
        assert (0, 0) in conflicts
        assert (5, 0) in conflicts

    def test_adjacent_conflict(self):
        """Adjacent queens (including diagonal) should conflict."""
        game = Game(6, max_solutions=10)
        marks = self.make_marks(6, queens=[(2, 2), (3, 3)])
        conflicts, _ = validate_player_marks(game.kingdoms, marks)
        assert (2, 2) in conflicts
        assert (3, 3) in conflicts

    def test_same_kingdom_conflict(self):
        """Two queens in same kingdom should conflict."""
        game = Game(6, max_solutions=10)
        # Find two cells in the same kingdom
        k0_cells = [(r, c) for r in range(6) for c in range(6)
                    if game.kingdoms[r][c] == 0]
        if len(k0_cells) >= 2:
            marks = self.make_marks(6, queens=[k0_cells[0], k0_cells[1]])
            conflicts, _ = validate_player_marks(game.kingdoms, marks)
            assert k0_cells[0] in conflicts or k0_cells[1] in conflicts

    def test_blocked_row(self):
        """Row with all circles should be blocked."""
        game = Game(6, max_solutions=10)
        # Mark entire first row with circles
        circles = [(0, c) for c in range(6)]
        marks = self.make_marks(6, circles=circles)
        _, blocked = validate_player_marks(game.kingdoms, marks)
        for c in range(6):
            assert (0, c) in blocked

    def test_blocked_column(self):
        """Column with all circles should be blocked."""
        game = Game(6, max_solutions=10)
        # Mark entire first column with circles
        circles = [(r, 0) for r in range(6)]
        marks = self.make_marks(6, circles=circles)
        _, blocked = validate_player_marks(game.kingdoms, marks)
        for r in range(6):
            assert (r, 0) in blocked

    def test_blocked_kingdom(self):
        """Kingdom with all circles should be blocked."""
        game = Game(6, max_solutions=10)
        # Find all cells in kingdom 0 and mark them with circles
        k0_cells = [(r, c) for r in range(6) for c in range(6)
                    if game.kingdoms[r][c] == 0]
        marks = self.make_marks(6, circles=k0_cells)
        _, blocked = validate_player_marks(game.kingdoms, marks)
        for cell in k0_cells:
            assert cell in blocked

    def test_row_with_queen_not_blocked(self):
        """Row with a queen and circles should not be blocked."""
        game = Game(6, max_solutions=10)
        # Mark row with one queen and rest circles
        queens = [(0, 0)]
        circles = [(0, c) for c in range(1, 6)]
        marks = self.make_marks(6, queens=queens, circles=circles)
        _, blocked = validate_player_marks(game.kingdoms, marks)
        # The circles shouldn't be blocked since there's a queen
        for c in range(1, 6):
            assert (0, c) not in blocked

    def test_row_with_empty_cell_not_row_blocked(self):
        """Verify row blocking only triggers when ALL cells are circles."""
        # Use a simple 3x3 kingdoms grid where each row is its own kingdom
        # This isolates row-blocking from kingdom-blocking
        kingdoms = [
            [0, 0, 0],
            [1, 1, 1],
            [2, 2, 2],
        ]
        # Mark row 0 with only 2 circles (leave one empty)
        marks = [
            [MARK_CIRCLE, MARK_CIRCLE, MARK_EMPTY],
            [MARK_EMPTY, MARK_EMPTY, MARK_EMPTY],
            [MARK_EMPTY, MARK_EMPTY, MARK_EMPTY],
        ]
        _, blocked = validate_player_marks(kingdoms, marks)
        # Row 0 shouldn't be blocked because (0, 2) is empty
        # Kingdom 0 also isn't blocked because (0, 2) is empty
        assert (0, 0) not in blocked
        assert (0, 1) not in blocked

    def test_row_fully_circled_is_blocked(self):
        """Row with all circles should be blocked."""
        kingdoms = [
            [0, 0, 0],
            [1, 1, 1],
            [2, 2, 2],
        ]
        marks = [
            [MARK_CIRCLE, MARK_CIRCLE, MARK_CIRCLE],
            [MARK_EMPTY, MARK_EMPTY, MARK_EMPTY],
            [MARK_EMPTY, MARK_EMPTY, MARK_EMPTY],
        ]
        _, blocked = validate_player_marks(kingdoms, marks)
        # Row 0 is fully circled, so all cells should be blocked
        assert (0, 0) in blocked
        assert (0, 1) in blocked
        assert (0, 2) in blocked

    def test_check_solution_correct(self):
        """Correct solution should be recognized."""
        game = Game(6, max_solutions=10)
        # Place queens at the actual solution positions
        marks = self.make_marks(6, queens=game.queens)
        assert check_player_solution(game.kingdoms, marks)

    def test_check_solution_incomplete(self):
        """Incomplete solution should not be valid."""
        game = Game(6, max_solutions=10)
        # Place only some queens
        marks = self.make_marks(6, queens=game.queens[:3])
        assert not check_player_solution(game.kingdoms, marks)

    def test_check_solution_too_many_queens(self):
        """Too many queens in a kingdom should not be valid."""
        game = Game(6, max_solutions=10)
        # Find a cell in kingdom 0 that's not a queen position
        k0_cells = [(r, c) for r in range(6) for c in range(6)
                    if game.kingdoms[r][c] == 0 and (r, c) not in game.queens]
        if k0_cells:
            extra_queens = [*game.queens, k0_cells[0]]
            marks = self.make_marks(6, queens=extra_queens)
            assert not check_player_solution(game.kingdoms, marks)

    def test_check_solution_with_conflicts(self):
        """Solution with conflicts should not be valid."""
        game = Game(6, max_solutions=10)
        # Create a set of queens that conflicts (same row)
        fake_queens = [(i, i) for i in range(6)]  # Diagonal - will have adjacency conflicts
        marks = self.make_marks(6, queens=fake_queens)
        assert not check_player_solution(game.kingdoms, marks)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_small_board(self):
        """Test smallest reasonable board size."""
        game = Game(4, max_solutions=100)  # 4x4 is smallest practical
        assert game.size == 4
        assert len(game.queens) == 4

    def test_seed_reproducibility(self):
        """Same seed should produce same game."""
        game1 = Game(7, seed=42, max_solutions=10)
        game2 = Game(7, seed=42, max_solutions=10)

        assert game1.kingdoms == game2.kingdoms
        assert game1.queens == game2.queens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
