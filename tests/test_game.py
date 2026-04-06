"""Tests for game logic: generation, encoding/decoding, daily puzzles."""

import os
import sys
import unittest
from datetime import date

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


class TestQueenPlacement(unittest.TestCase):
    """Test queen placement validity."""

    def test_queens_count(self):
        """Each puzzle should have exactly N queens for an NxN board."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                game = Game(size, max_solutions=10)
                self.assertEqual(len(game.queens), size, f'{size}x{size} queen count')

    def test_queens_one_per_row(self):
        """Each row should have exactly one queen."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                game = Game(size, max_solutions=10)
                rows = [r for r, c in game.queens]
                self.assertEqual(sorted(rows), list(range(size)),
                                 'should have one queen per row')

    def test_queens_one_per_column(self):
        """Each column should have at most one queen (N-queens rule)."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                game = Game(size, max_solutions=10)
                cols = [c for r, c in game.queens]
                self.assertEqual(len(cols), len(set(cols)), 'queens share a column')

    def test_queens_not_adjacent(self):
        """No two queens should be adjacent (including diagonally)."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                game = Game(size, max_solutions=10)
                queens = game.queens
                for i, (r1, c1) in enumerate(queens):
                    for r2, c2 in queens[i + 1:]:
                        row_diff = abs(r1 - r2)
                        col_diff = abs(c1 - c2)
                        self.assertFalse(
                            row_diff <= 1 and col_diff <= 1,
                            f'queens at ({r1},{c1}) and ({r2},{c2}) are adjacent',
                        )


class TestKingdoms(unittest.TestCase):
    """Test kingdom generation."""

    def test_all_cells_assigned(self):
        """Every cell should belong to a kingdom."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                game = Game(size, max_solutions=10)
                for row in range(size):
                    for col in range(size):
                        self.assertGreaterEqual(
                            game.kingdoms[row][col], 0,
                            f'cell ({row},{col}) not assigned',
                        )

    def test_kingdom_count(self):
        """Should have exactly N kingdoms for an NxN board."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                game = Game(size, max_solutions=10)
                kingdom_ids = set()
                for row in game.kingdoms:
                    kingdom_ids.update(row)
                self.assertEqual(len(kingdom_ids), size, 'kingdom count')

    def test_each_kingdom_has_queen(self):
        """Each kingdom should contain exactly one queen."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                game = Game(size, max_solutions=10)
                queen_set = set(game.queens)
                for k in range(size):
                    queens_in_kingdom = sum(
                        1 for row in range(size) for col in range(size)
                        if game.kingdoms[row][col] == k and (row, col) in queen_set
                    )
                    self.assertEqual(queens_in_kingdom, 1,
                                     f'kingdom {k} has {queens_in_kingdom} queens')

    def test_kingdoms_connected(self):
        """Each kingdom should be a connected region."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                game = Game(size, max_solutions=10)

                for k in range(size):
                    cells = [(r, c) for r in range(size) for c in range(size)
                             if game.kingdoms[r][c] == k]
                    self.assertGreater(len(cells), 0, f'kingdom {k} has no cells')

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

                    self.assertEqual(
                        len(visited), len(cells),
                        f'kingdom {k} not connected: {len(visited)}/{len(cells)}',
                    )


class TestDailyPuzzles(unittest.TestCase):
    """Test daily puzzle generation."""

    def test_same_date_same_puzzle(self):
        """Same date and size should produce the same puzzle."""
        test_date = date(2025, 6, 15)

        game1 = get_daily_game(test_date, 7, max_solutions=10)
        game2 = get_daily_game(test_date, 7, max_solutions=10)

        self.assertEqual(game1.kingdoms, game2.kingdoms, 'kingdoms should match')
        self.assertEqual(game1.queens, game2.queens, 'queens should match')

    def test_different_dates_different_puzzles(self):
        """Different dates should produce different puzzles."""
        date1 = date(2025, 6, 15)
        date2 = date(2025, 6, 16)

        game1 = get_daily_game(date1, 7, max_solutions=10)
        game2 = get_daily_game(date2, 7, max_solutions=10)

        self.assertTrue(
            game1.queens != game2.queens or game1.kingdoms != game2.kingdoms,
            'different dates should produce different puzzles',
        )

    def test_different_sizes_different_puzzles(self):
        """Same date but different sizes should produce different puzzles."""
        test_date = date(2025, 6, 15)

        game6 = get_daily_game(test_date, 6, max_solutions=10)
        game7 = get_daily_game(test_date, 7, max_solutions=10)

        self.assertNotEqual(game6.size, game7.size, 'sizes should differ')

    def test_daily_seed_deterministic(self):
        """Daily seed generation should be deterministic."""
        test_date = date(2025, 1, 1)

        seed1 = get_daily_seed(test_date, 7)
        seed2 = get_daily_seed(test_date, 7)

        self.assertEqual(seed1, seed2, 'seeds should match')


class TestSolutionCounting(unittest.TestCase):
    """Test solution counting."""

    def test_generated_puzzle_has_solutions(self):
        """Generated puzzles should have at least one solution."""
        game = Game(7, max_solutions=4)
        solutions = game.count_solutions(max_count=10)
        self.assertGreaterEqual(solutions, 1, 'should have at least one solution')

    def test_max_solutions_respected(self):
        """Puzzles should not exceed max_solutions."""
        game = Game(7, max_solutions=2)
        self.assertLessEqual(game.num_solutions, 2, 'should not exceed max')

    def test_unique_solution_puzzle(self):
        """Can generate puzzles with unique solution."""
        game = Game(6, max_solutions=1)
        self.assertEqual(game.num_solutions, 1, 'should have exactly 1 solution')


class TestConflictDetection(unittest.TestCase):
    """Test conflict detection logic (same as in board_widget)."""

    def find_conflicts(self, queens):
        """Find conflicts among placed queens."""
        conflicts = set()
        for i, (r1, c1) in enumerate(queens):
            for r2, c2 in queens[i + 1:]:
                if r1 == r2 or c1 == c2 or (abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1):
                    conflicts.add((r1, c1))
                    conflicts.add((r2, c2))
        return conflicts

    def test_no_conflicts_valid_placement(self):
        """Valid queen placement should have no conflicts."""
        queens = [(0, 1), (1, 3), (2, 0), (3, 2)]
        self.assertEqual(len(self.find_conflicts(queens)), 0, 'no conflicts expected')

    def test_same_row_conflict(self):
        """Queens in same row should conflict."""
        queens = [(0, 0), (0, 5)]
        conflicts = self.find_conflicts(queens)
        self.assertIn((0, 0), conflicts, 'first queen should conflict')
        self.assertIn((0, 5), conflicts, 'second queen should conflict')

    def test_same_column_conflict(self):
        """Queens in same column should conflict."""
        queens = [(0, 0), (5, 0)]
        conflicts = self.find_conflicts(queens)
        self.assertIn((0, 0), conflicts, 'first queen should conflict')
        self.assertIn((5, 0), conflicts, 'second queen should conflict')

    def test_diagonal_adjacent_conflict(self):
        """Diagonally adjacent queens should conflict."""
        queens = [(2, 2), (3, 3)]
        conflicts = self.find_conflicts(queens)
        self.assertIn((2, 2), conflicts, 'first queen should conflict')
        self.assertIn((3, 3), conflicts, 'second queen should conflict')

    def test_non_adjacent_diagonal_ok(self):
        """Non-adjacent diagonal queens should not conflict."""
        queens = [(0, 0), (2, 2)]
        conflicts = self.find_conflicts(queens)
        self.assertEqual(len(conflicts), 0, 'non-adjacent should not conflict')

    def test_generated_solution_has_no_conflicts(self):
        """The solution (queens) of a generated game should have no conflicts."""
        game = Game(7, max_solutions=4)
        conflicts = self.find_conflicts(game.queens)
        self.assertEqual(len(conflicts), 0, f'generated solution has conflicts: {conflicts}')


class TestPlayerValidation(unittest.TestCase):
    """Test player mark validation functions."""

    def make_marks(self, size, queens=None, circles=None):
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
        self.assertEqual(len(conflicts), 0, 'no conflicts on empty board')
        self.assertEqual(len(blocked), 0, 'no blocked on empty board')

    def test_same_row_conflict(self):
        """Two queens in same row should conflict."""
        game = Game(6, max_solutions=10)
        marks = self.make_marks(6, queens=[(0, 0), (0, 5)])
        conflicts, _ = validate_player_marks(game.kingdoms, marks)
        self.assertIn((0, 0), conflicts, 'first queen should conflict')
        self.assertIn((0, 5), conflicts, 'second queen should conflict')

    def test_same_column_conflict(self):
        """Two queens in same column should conflict."""
        game = Game(6, max_solutions=10)
        marks = self.make_marks(6, queens=[(0, 0), (5, 0)])
        conflicts, _ = validate_player_marks(game.kingdoms, marks)
        self.assertIn((0, 0), conflicts, 'first queen should conflict')
        self.assertIn((5, 0), conflicts, 'second queen should conflict')

    def test_adjacent_conflict(self):
        """Adjacent queens (including diagonal) should conflict."""
        game = Game(6, max_solutions=10)
        marks = self.make_marks(6, queens=[(2, 2), (3, 3)])
        conflicts, _ = validate_player_marks(game.kingdoms, marks)
        self.assertIn((2, 2), conflicts, 'first queen should conflict')
        self.assertIn((3, 3), conflicts, 'second queen should conflict')

    def test_same_kingdom_conflict(self):
        """Two queens in same kingdom should conflict."""
        game = Game(6, max_solutions=10)
        k0_cells = [(r, c) for r in range(6) for c in range(6)
                    if game.kingdoms[r][c] == 0]
        if len(k0_cells) >= 2:
            marks = self.make_marks(6, queens=[k0_cells[0], k0_cells[1]])
            conflicts, _ = validate_player_marks(game.kingdoms, marks)
            self.assertTrue(
                k0_cells[0] in conflicts or k0_cells[1] in conflicts,
                'same kingdom queens should conflict',
            )

    def test_blocked_row(self):
        """Row with all circles should be blocked."""
        game = Game(6, max_solutions=10)
        circles = [(0, c) for c in range(6)]
        marks = self.make_marks(6, circles=circles)
        _, blocked = validate_player_marks(game.kingdoms, marks)
        for c in range(6):
            self.assertIn((0, c), blocked, f'cell (0,{c}) should be blocked')

    def test_blocked_column(self):
        """Column with all circles should be blocked."""
        game = Game(6, max_solutions=10)
        circles = [(r, 0) for r in range(6)]
        marks = self.make_marks(6, circles=circles)
        _, blocked = validate_player_marks(game.kingdoms, marks)
        for r in range(6):
            self.assertIn((r, 0), blocked, f'cell ({r},0) should be blocked')

    def test_blocked_kingdom(self):
        """Kingdom with all circles should be blocked."""
        game = Game(6, max_solutions=10)
        k0_cells = [(r, c) for r in range(6) for c in range(6)
                    if game.kingdoms[r][c] == 0]
        marks = self.make_marks(6, circles=k0_cells)
        _, blocked = validate_player_marks(game.kingdoms, marks)
        for cell in k0_cells:
            self.assertIn(cell, blocked, f'cell {cell} should be blocked')

    def test_row_with_queen_not_blocked(self):
        """Row with a queen and circles should not be row-blocked."""
        # Use controlled kingdoms so kingdom-blocking doesn't interfere
        kingdoms = [
            [0, 0, 0],
            [1, 1, 1],
            [2, 2, 2],
        ]
        marks = [
            [MARK_QUEEN, MARK_CIRCLE, MARK_CIRCLE],
            [MARK_EMPTY, MARK_EMPTY, MARK_EMPTY],
            [MARK_EMPTY, MARK_EMPTY, MARK_EMPTY],
        ]
        _, blocked = validate_player_marks(kingdoms, marks)
        self.assertNotIn((0, 1), blocked, 'should not be blocked with queen in row')
        self.assertNotIn((0, 2), blocked, 'should not be blocked with queen in row')

    def test_row_with_empty_cell_not_row_blocked(self):
        """Verify row blocking only triggers when ALL cells are circles."""
        kingdoms = [
            [0, 0, 0],
            [1, 1, 1],
            [2, 2, 2],
        ]
        marks = [
            [MARK_CIRCLE, MARK_CIRCLE, MARK_EMPTY],
            [MARK_EMPTY, MARK_EMPTY, MARK_EMPTY],
            [MARK_EMPTY, MARK_EMPTY, MARK_EMPTY],
        ]
        _, blocked = validate_player_marks(kingdoms, marks)
        self.assertNotIn((0, 0), blocked, 'should not be blocked with empty cell')
        self.assertNotIn((0, 1), blocked, 'should not be blocked with empty cell')

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
        self.assertIn((0, 0), blocked, 'cell (0,0) should be blocked')
        self.assertIn((0, 1), blocked, 'cell (0,1) should be blocked')
        self.assertIn((0, 2), blocked, 'cell (0,2) should be blocked')

    def test_check_solution_correct(self):
        """Correct solution should be recognized."""
        game = Game(6, max_solutions=10)
        marks = self.make_marks(6, queens=game.queens)
        self.assertTrue(check_player_solution(game.kingdoms, marks),
                        'correct solution should be valid')

    def test_check_solution_incomplete(self):
        """Incomplete solution should not be valid."""
        game = Game(6, max_solutions=10)
        marks = self.make_marks(6, queens=game.queens[:3])
        self.assertFalse(check_player_solution(game.kingdoms, marks),
                         'incomplete solution should be invalid')

    def test_check_solution_too_many_queens(self):
        """Too many queens in a kingdom should not be valid."""
        game = Game(6, max_solutions=10)
        k0_cells = [(r, c) for r in range(6) for c in range(6)
                    if game.kingdoms[r][c] == 0 and (r, c) not in game.queens]
        if k0_cells:
            extra_queens = [*game.queens, k0_cells[0]]
            marks = self.make_marks(6, queens=extra_queens)
            self.assertFalse(check_player_solution(game.kingdoms, marks),
                             'too many queens should be invalid')

    def test_check_solution_with_conflicts(self):
        """Solution with conflicts should not be valid."""
        game = Game(6, max_solutions=10)
        fake_queens = [(i, i) for i in range(6)]
        marks = self.make_marks(6, queens=fake_queens)
        self.assertFalse(check_player_solution(game.kingdoms, marks),
                         'conflicting solution should be invalid')


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_small_board(self):
        """Test smallest reasonable board size."""
        game = Game(4, max_solutions=100)
        self.assertEqual(game.size, 4, 'size should be 4')
        self.assertEqual(len(game.queens), 4, 'should have 4 queens')

    def test_seed_reproducibility(self):
        """Same seed should produce same game."""
        game1 = Game(7, seed=42, max_solutions=10)
        game2 = Game(7, seed=42, max_solutions=10)

        self.assertEqual(game1.kingdoms, game2.kingdoms, 'kingdoms should match')
        self.assertEqual(game1.queens, game2.queens, 'queens should match')


if __name__ == "__main__":
    unittest.main()
