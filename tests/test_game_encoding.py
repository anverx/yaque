"""Tests for game encoding/decoding functions."""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game import Game
from game_encoding import (
    encode_game,
    decode_game,
    encode_game_b64,
    decode_game_b64,
    encode_board_state,
    decode_board_state,
    _bits_needed,
    _pack_bits,
    _unpack_bits,
)


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
        game = Game(8, max_solutions=100)
        code = game.encode()

        # 8x8 should encode to ~18 bytes raw, ~24 chars base64
        assert len(code) < 30, f"Encoding too long: {len(code)} chars"

    def test_different_games_different_codes(self):
        """Different games should produce different codes."""
        game1 = Game(7, seed=12345, max_solutions=100)
        game2 = Game(7, seed=54321, max_solutions=100)

        code1 = game1.encode()
        code2 = game2.encode()

        assert code1 != code2, "Different games should have different codes"

    def test_invalid_code_raises(self):
        """Invalid code should raise an exception."""
        with pytest.raises(Exception):
            Game.from_code("invalid_garbage_code!!!")


class TestBoardStateEncoding:
    """Test board state encoding/decoding for save/restore."""

    @pytest.mark.parametrize("size", [6, 7, 8])
    def test_encode_decode_roundtrip(self, size):
        """Encoding then decoding should return original board state."""
        # Create a board with various cell states
        cell_marks = [[((r + c) % 3) for c in range(size)] for r in range(size)]

        encoded = encode_board_state(cell_marks)
        decoded = decode_board_state(encoded)

        assert decoded == cell_marks

    def test_encode_decode_empty_board(self):
        """Empty board should encode/decode correctly."""
        cell_marks = [[0] * 6 for _ in range(6)]

        encoded = encode_board_state(cell_marks)
        decoded = decode_board_state(encoded)

        assert decoded == cell_marks

    def test_encode_decode_full_board(self):
        """Board with all queens should encode/decode correctly."""
        cell_marks = [[1] * 7 for _ in range(7)]

        encoded = encode_board_state(cell_marks)
        decoded = decode_board_state(encoded)

        assert decoded == cell_marks

    def test_encode_decode_mixed_board(self):
        """Board with mixed marks should encode/decode correctly."""
        cell_marks = [
            [0, 1, 2, 0, 1, 2, 0, 1],
            [2, 0, 1, 2, 0, 1, 2, 0],
            [1, 2, 0, 1, 2, 0, 1, 2],
            [0, 1, 2, 0, 1, 2, 0, 1],
            [2, 0, 1, 2, 0, 1, 2, 0],
            [1, 2, 0, 1, 2, 0, 1, 2],
            [0, 1, 2, 0, 1, 2, 0, 1],
            [2, 0, 1, 2, 0, 1, 2, 0],
        ]

        encoded = encode_board_state(cell_marks)
        decoded = decode_board_state(encoded)

        assert decoded == cell_marks

    def test_encoding_is_compact(self):
        """Board state encoding should be compact."""
        # 8x8: 64 cells * 2 bits = 128 bits = 16 bytes + 1 size byte = 17 bytes
        # Base64: ~24 chars
        cell_marks = [[0] * 8 for _ in range(8)]
        encoded = encode_board_state(cell_marks)

        assert len(encoded) <= 24, f"8x8 encoding too long: {len(encoded)} chars"

        # 6x6: 36 cells * 2 bits = 72 bits = 9 bytes + 1 size byte = 10 bytes
        # Base64: ~16 chars
        cell_marks = [[0] * 6 for _ in range(6)]
        encoded = encode_board_state(cell_marks)

        assert len(encoded) <= 16, f"6x6 encoding too long: {len(encoded)} chars"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
