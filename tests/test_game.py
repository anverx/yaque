"""Tests for game logic: generation, encoding/decoding, daily puzzles."""

import pytest
from datetime import date, timedelta
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game import (
    Game,
    get_daily_seed,
    get_daily_game,
)
from encoding import (
    encode_game,
    decode_game,
    encode_game_b64,
    decode_game_b64,
    _bits_needed,
    _pack_bits,
    _unpack_bits,
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


class TestEncoding:
    """Test game encoding and decoding."""

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_encode_decode_roundtrip(self, size):
        """Encoding then decoding should return the same game."""
        game = Game(size, max_solutions=100)

        encoded = encode_game(game.kingdoms, game.queens)
        decoded_kingdoms, decoded_queens = decode_game(encoded)

        assert decoded_kingdoms == game.kingdoms, "Kingdoms mismatch after decode"
        assert decoded_queens == game.queens, "Queens mismatch after decode"

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_encode_decode_b64_roundtrip(self, size):
        """Base64 encoding then decoding should return the same game."""
        game = Game(size, max_solutions=100)

        code = encode_game_b64(game.kingdoms, game.queens)
        decoded_kingdoms, decoded_queens = decode_game_b64(code)

        assert decoded_kingdoms == game.kingdoms, "Kingdoms mismatch after b64 decode"
        assert decoded_queens == game.queens, "Queens mismatch after b64 decode"

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_game_from_code(self, size):
        """Game.from_code should properly reconstruct a game."""
        original = Game(size, max_solutions=100)
        code = original.encode()

        restored = Game.from_code(code)

        assert restored.size == original.size
        assert restored.kingdoms == original.kingdoms
        assert restored.queens == original.queens

    def test_encoding_is_compact(self):
        """Encoded games should be reasonably compact."""
        game = Game(8, max_solutions=10)
        code = game.encode()

        # 8x8 should encode to ~18 bytes raw, ~24 chars base64
        assert len(code) < 30, f"Encoding too long: {len(code)} chars"

    def test_different_games_different_codes(self):
        """Different games should produce different codes."""
        game1 = Game(7, seed=12345, max_solutions=10)
        game2 = Game(7, seed=54321, max_solutions=10)

        code1 = game1.encode()
        code2 = game2.encode()

        assert code1 != code2, "Different games should have different codes"


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


class TestBitPacking:
    """Test bit packing utilities."""

    def test_bits_needed(self):
        """Test _bits_needed function."""
        assert _bits_needed(1) == 1
        assert _bits_needed(2) == 1
        assert _bits_needed(3) == 2
        assert _bits_needed(4) == 2
        assert _bits_needed(5) == 3
        assert _bits_needed(8) == 3
        assert _bits_needed(9) == 4

    def test_pack_unpack_roundtrip(self):
        """Packing then unpacking should return original values."""
        values = [3, 1, 4, 1, 5, 9, 2, 6]
        bits = 4

        packed = _pack_bits(values, bits)
        unpacked = _unpack_bits(packed, len(values), bits)

        assert unpacked == values

    def test_pack_unpack_various_bit_sizes(self):
        """Test packing with various bit sizes."""
        for bits in [1, 2, 3, 4, 5, 6, 7, 8]:
            max_val = (1 << bits) - 1
            values = [i % (max_val + 1) for i in range(10)]

            packed = _pack_bits(values, bits)
            unpacked = _unpack_bits(packed, len(values), bits)

            assert unpacked == values, f"Failed for {bits} bits"


class TestConflictDetection:
    """Test conflict detection logic (same as in board_widget)."""

    def find_conflicts(self, queens):
        """Find conflicts among placed queens."""
        conflicts = set()
        for i, (r1, c1) in enumerate(queens):
            for r2, c2 in queens[i + 1:]:
                # Same row or column
                if r1 == r2 or c1 == c2:
                    conflicts.add((r1, c1))
                    conflicts.add((r2, c2))
                # Adjacent (including diagonal)
                elif abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1:
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


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_code_raises(self):
        """Invalid code should raise an exception."""
        with pytest.raises(Exception):
            Game.from_code("invalid_garbage_code!!!")

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
