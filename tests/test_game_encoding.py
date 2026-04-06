"""Tests for game encoding/decoding functions."""

import os
import sys
import unittest

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


class TestBitPacking(unittest.TestCase):
    """Test bit packing utilities."""

    def test_bits_needed(self):
        """Test _bits_needed function."""
        cases = [(1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (8, 3), (9, 4)]
        for n, expected in cases:
            with self.subTest(n=n):
                self.assertEqual(_bits_needed(n), expected,
                                 f'bits_needed({n})')

    def test_pack_unpack_roundtrip(self):
        """Packing then unpacking should return original values."""
        values = [3, 1, 4, 1, 5, 9, 2, 6]
        bits = 4

        packed = _pack_bits(values, bits)
        unpacked = _unpack_bits(packed, len(values), bits)

        self.assertEqual(unpacked, values, 'roundtrip should preserve values')

    def test_pack_unpack_various_bit_sizes(self):
        """Test packing with various bit sizes."""
        for bits in [1, 2, 3, 4, 5, 6, 7, 8]:
            with self.subTest(bits=bits):
                max_val = (1 << bits) - 1
                values = [i % (max_val + 1) for i in range(10)]

                packed = _pack_bits(values, bits)
                unpacked = _unpack_bits(packed, len(values), bits)

                self.assertEqual(unpacked, values, f'failed for {bits} bits')


class TestEncoding(unittest.TestCase):
    """Test game encoding and decoding."""

    def test_encode_decode_roundtrip(self):
        """Encoding then decoding should return the same game."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                game = Game(size, max_solutions=100)

                encoded = encode_game(game.kingdoms, game.queens)
                decoded_kingdoms, decoded_queens = decode_game(encoded)

                self.assertEqual(decoded_kingdoms, game.kingdoms, 'kingdoms mismatch')
                self.assertEqual(decoded_queens, game.queens, 'queens mismatch')

    def test_encode_decode_b64_roundtrip(self):
        """Base64 encoding then decoding should return the same game."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                game = Game(size, max_solutions=100)

                code = encode_game_b64(game.kingdoms, game.queens)
                decoded_kingdoms, decoded_queens = decode_game_b64(code)

                self.assertEqual(decoded_kingdoms, game.kingdoms, 'kingdoms mismatch')
                self.assertEqual(decoded_queens, game.queens, 'queens mismatch')

    def test_game_from_code(self):
        """Game.from_code should properly reconstruct a game."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                original = Game(size, max_solutions=100)
                code = original.encode()

                restored = Game.from_code(code)

                self.assertEqual(restored.size, original.size, 'size mismatch')
                self.assertEqual(restored.kingdoms, original.kingdoms, 'kingdoms mismatch')
                self.assertEqual(restored.queens, original.queens, 'queens mismatch')

    def test_encoding_is_compact(self):
        """Encoded games should be reasonably compact."""
        game = Game(8, max_solutions=100)
        code = game.encode()
        self.assertLess(len(code), 30, f'encoding too long: {len(code)} chars')

    def test_different_games_different_codes(self):
        """Different games should produce different codes."""
        game1 = Game(7, seed=12345, max_solutions=100)
        game2 = Game(7, seed=54321, max_solutions=100)

        code1 = game1.encode()
        code2 = game2.encode()

        self.assertNotEqual(code1, code2, 'different games should have different codes')

    def test_invalid_code_raises(self):
        """Invalid code should raise an exception."""
        with self.assertRaises(Exception, msg='invalid code should raise'):
            Game.from_code("invalid_garbage_code!!!")


class TestBoardStateEncoding(unittest.TestCase):
    """Test board state encoding/decoding for save/restore."""

    def test_encode_decode_roundtrip(self):
        """Encoding then decoding should return original board state."""
        for size in [6, 7, 8]:
            with self.subTest(size=size):
                cell_marks = [[((r + c) % 3) for c in range(size)]
                              for r in range(size)]

                encoded = encode_board_state(cell_marks)
                decoded = decode_board_state(encoded)

                self.assertEqual(decoded, cell_marks, 'roundtrip should preserve state')

    def test_encode_decode_empty_board(self):
        """Empty board should encode/decode correctly."""
        cell_marks = [[0] * 6 for _ in range(6)]

        encoded = encode_board_state(cell_marks)
        decoded = decode_board_state(encoded)

        self.assertEqual(decoded, cell_marks, 'empty board roundtrip')

    def test_encode_decode_full_board(self):
        """Board with all queens should encode/decode correctly."""
        cell_marks = [[1] * 7 for _ in range(7)]

        encoded = encode_board_state(cell_marks)
        decoded = decode_board_state(encoded)

        self.assertEqual(decoded, cell_marks, 'full board roundtrip')

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

        self.assertEqual(decoded, cell_marks, 'mixed board roundtrip')

    def test_encoding_is_compact(self):
        """Board state encoding should be compact."""
        cell_marks = [[0] * 8 for _ in range(8)]
        encoded = encode_board_state(cell_marks)
        self.assertLessEqual(len(encoded), 24,
                             f'8x8 encoding too long: {len(encoded)} chars')

        cell_marks = [[0] * 6 for _ in range(6)]
        encoded = encode_board_state(cell_marks)
        self.assertLessEqual(len(encoded), 16,
                             f'6x6 encoding too long: {len(encoded)} chars')


if __name__ == "__main__":
    unittest.main()
