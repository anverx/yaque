"""Tests for database module."""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import database
import game_encoding


def _make_temp_db():
    """Create a temporary database directory and initialize."""
    temp_dir = tempfile.mkdtemp()
    database.init_db(temp_dir)
    return temp_dir


def _cleanup_db(temp_dir):
    """Close database and remove temp directory."""
    database.close_db()
    shutil.rmtree(temp_dir)


class TestPuzzleOperations(unittest.TestCase):
    """Test puzzle CRUD operations."""

    def setUp(self):
        self.temp_dir = _make_temp_db()

    def tearDown(self):
        _cleanup_db(self.temp_dir)

    def test_save_puzzle(self):
        """Should save a puzzle and return its ID."""
        puzzle_id = database.save_puzzle(
            code='ABC123',
            size=7,
            daily_date='2025-06-15',
            seed=42
        )
        self.assertIsNotNone(puzzle_id, 'should return an ID')
        self.assertGreater(puzzle_id, 0, 'ID should be positive')

    def test_save_duplicate_puzzle_returns_existing_id(self):
        """Saving same puzzle twice should return existing ID."""
        id1 = database.save_puzzle(code='ABC123', size=7)
        id2 = database.save_puzzle(code='ABC123', size=7)
        self.assertEqual(id1, id2, 'duplicate should return same ID')

    def test_get_puzzle_by_code(self):
        """Should retrieve puzzle by code."""
        database.save_puzzle(code='XYZ789', size=8, daily_date='2025-01-01')

        puzzle = database.get_puzzle_by_code('XYZ789')

        self.assertIsNotNone(puzzle, 'puzzle should be found')
        self.assertEqual(puzzle['code'], 'XYZ789', 'code should match')
        self.assertEqual(puzzle['size'], 8, 'size should match')
        self.assertEqual(puzzle['daily_date'], '2025-01-01', 'date should match')

    def test_get_puzzle_by_code_not_found(self):
        """Should return None for non-existent code."""
        puzzle = database.get_puzzle_by_code('NONEXISTENT')
        self.assertIsNone(puzzle, 'should return None')

    def test_get_puzzle_by_id(self):
        """Should retrieve puzzle by ID."""
        puzzle_id = database.save_puzzle(code='TEST1', size=6)

        puzzle = database.get_puzzle_by_id(puzzle_id)

        self.assertIsNotNone(puzzle, 'puzzle should be found')
        self.assertEqual(puzzle['id'], puzzle_id, 'ID should match')
        self.assertEqual(puzzle['code'], 'TEST1', 'code should match')

    def test_get_daily_puzzles(self):
        """Should retrieve all puzzles for a date, ordered by size."""
        database.save_puzzle(code='D1', size=8, daily_date='2025-06-15')
        database.save_puzzle(code='D2', size=6, daily_date='2025-06-15')
        database.save_puzzle(code='D3', size=7, daily_date='2025-06-15')
        database.save_puzzle(code='OTHER', size=7, daily_date='2025-06-16')

        puzzles = database.get_daily_puzzles('2025-06-15')

        self.assertEqual(len(puzzles), 3, 'should find 3 puzzles')
        self.assertEqual(puzzles[0]['size'], 6, 'first should be 6')
        self.assertEqual(puzzles[1]['size'], 7, 'second should be 7')
        self.assertEqual(puzzles[2]['size'], 8, 'third should be 8')


class TestPlayOperations(unittest.TestCase):
    """Test play tracking operations."""

    def setUp(self):
        self.temp_dir = _make_temp_db()

    def tearDown(self):
        _cleanup_db(self.temp_dir)

    def test_start_play(self):
        """Should start a play session."""
        puzzle_id = database.save_puzzle(code='PLAY1', size=7)

        play_id = database.start_play(puzzle_id)

        self.assertIsNotNone(play_id, 'should return an ID')
        self.assertGreater(play_id, 0, 'ID should be positive')

    def test_complete_play(self):
        """Should mark play as completed with duration."""
        puzzle_id = database.save_puzzle(code='PLAY2', size=7)
        play_id = database.start_play(puzzle_id)

        database.complete_play(play_id, duration_ms=45000)

        play = database.get_play(play_id)
        self.assertEqual(play['completed'], 1, 'should be completed')
        self.assertEqual(play['duration_ms'], 45000, 'duration should match')

    def test_rate_play(self):
        """Should add rating to play."""
        puzzle_id = database.save_puzzle(code='PLAY3', size=7)
        play_id = database.start_play(puzzle_id)
        database.complete_play(play_id, duration_ms=30000)

        database.rate_play(play_id, fun_rating=5)

        play = database.get_play(play_id)
        self.assertEqual(play['fun_rating'], 5, 'rating should match')

    def test_get_plays_for_puzzle(self):
        """Should get all plays for a puzzle."""
        puzzle_id = database.save_puzzle(code='PLAY4', size=7)
        database.start_play(puzzle_id)
        database.start_play(puzzle_id)
        database.start_play(puzzle_id)

        plays = database.get_plays_for_puzzle(puzzle_id)

        self.assertEqual(len(plays), 3, 'should have 3 plays')

    def test_get_best_time_for_puzzle(self):
        """Should return best completion time."""
        puzzle_id = database.save_puzzle(code='PLAY5', size=7)

        play1 = database.start_play(puzzle_id)
        database.complete_play(play1, duration_ms=60000)

        play2 = database.start_play(puzzle_id)
        database.complete_play(play2, duration_ms=45000)  # Best time

        play3 = database.start_play(puzzle_id)
        database.complete_play(play3, duration_ms=55000)

        database.start_play(puzzle_id)  # Incomplete

        best = database.get_best_time_for_puzzle(puzzle_id)
        self.assertEqual(best, 45000, 'best time should be 45000')

    def test_get_best_time_no_completions(self):
        """Should return None if no completed plays."""
        puzzle_id = database.save_puzzle(code='PLAY6', size=7)
        database.start_play(puzzle_id)  # Not completed

        best = database.get_best_time_for_puzzle(puzzle_id)
        self.assertIsNone(best, 'should return None')


class TestStatistics(unittest.TestCase):
    """Test statistics functions."""

    def setUp(self):
        self.temp_dir = _make_temp_db()

    def tearDown(self):
        _cleanup_db(self.temp_dir)

    def test_get_play_stats(self):
        """Should return overall statistics."""
        puzzle_id = database.save_puzzle(code='STATS1', size=7)

        play1 = database.start_play(puzzle_id)
        database.complete_play(play1, duration_ms=40000)

        play2 = database.start_play(puzzle_id)
        database.complete_play(play2, duration_ms=60000)

        database.start_play(puzzle_id)  # Not completed

        stats = database.get_play_stats()

        self.assertEqual(stats['total_plays'], 3, 'total plays')
        self.assertEqual(stats['completed_plays'], 2, 'completed plays')
        self.assertEqual(stats['average_time_ms'], 50000, 'average time')

    def test_get_recent_plays(self):
        """Should return recent plays with puzzle info."""
        puzzle_id = database.save_puzzle(code='RECENT1', size=7,
                                         daily_date='2025-06-15')
        play1 = database.start_play(puzzle_id)
        database.complete_play(play1, duration_ms=30000)

        database.start_play(puzzle_id)

        plays = database.get_recent_plays(limit=10)

        self.assertEqual(len(plays), 2, 'should have 2 plays')
        self.assertEqual(plays[0]['code'], 'RECENT1', 'code should match')
        self.assertEqual(plays[0]['size'], 7, 'size should match')


class TestConfig(unittest.TestCase):
    """Test config key-value store."""

    def setUp(self):
        self.temp_dir = _make_temp_db()

    def tearDown(self):
        _cleanup_db(self.temp_dir)

    def test_get_set_config(self):
        """Should store and retrieve config values."""
        database.set_config('test_key', 'test_value')
        self.assertEqual(database.get_config('test_key'), 'test_value',
                         'should retrieve stored value')

    def test_get_config_default(self):
        """Should return default for missing keys."""
        self.assertEqual(database.get_config('missing', 'default'), 'default',
                         'should return explicit default')
        self.assertIsNone(database.get_config('missing'),
                          'should return None by default')

    def test_set_config_overwrites(self):
        """Should overwrite existing values."""
        database.set_config('key', 'value1')
        database.set_config('key', 'value2')
        self.assertEqual(database.get_config('key'), 'value2',
                         'should overwrite')

    def test_delete_config(self):
        """Should delete config values."""
        database.set_config('to_delete', 'value')
        database.delete_config('to_delete')
        self.assertIsNone(database.get_config('to_delete'),
                          'should be deleted')

    def test_schema_version_set(self):
        """Schema version should be set after init."""
        version = database.get_config('schema_version')
        self.assertIsNotNone(version, 'version should exist')
        self.assertGreaterEqual(int(version), 1, 'version should be >= 1')


class TestGameState(unittest.TestCase):
    """Test game state save/restore operations."""

    def setUp(self):
        self.temp_dir = _make_temp_db()

    def tearDown(self):
        _cleanup_db(self.temp_dir)

    def test_save_game_state(self):
        """Should save board state and elapsed time."""
        puzzle_id = database.save_puzzle(code='STATE1', size=7)
        play_id = database.start_play(puzzle_id)

        cell_marks = [[0, 1, 2], [1, 0, 2], [2, 1, 0]]
        encoded = game_encoding.encode_board_state(cell_marks)
        database.save_game_state(play_id, elapsed_seconds=45, board_state=encoded)

        play = database.get_play(play_id)
        self.assertEqual(play['elapsed_seconds'], 45, 'elapsed should match')
        self.assertEqual(play['board_state'], encoded, 'board state should match')

    def test_get_incomplete_play(self):
        """Should get the most recent incomplete play with board state."""
        puzzle_id = database.save_puzzle(code='STATE2', size=7)

        play1 = database.start_play(puzzle_id)
        database.complete_play(play1, duration_ms=30000)

        play2 = database.start_play(puzzle_id)
        cell_marks = [[0, 1], [2, 0]]
        encoded = game_encoding.encode_board_state(cell_marks)
        database.save_game_state(play2, elapsed_seconds=20, board_state=encoded)

        incomplete = database.get_incomplete_play(puzzle_id)

        self.assertIsNotNone(incomplete, 'should find incomplete play')
        self.assertEqual(incomplete['id'], play2, 'should be the right play')
        self.assertEqual(incomplete['elapsed_seconds'], 20, 'elapsed should match')
        decoded = game_encoding.decode_board_state(incomplete['board_state'])
        self.assertEqual(decoded, cell_marks, 'board state should roundtrip')

    def test_get_incomplete_play_none_when_all_complete(self):
        """Should return None if all plays are complete."""
        puzzle_id = database.save_puzzle(code='STATE3', size=7)
        play_id = database.start_play(puzzle_id)
        database.complete_play(play_id, duration_ms=30000)

        incomplete = database.get_incomplete_play(puzzle_id)
        self.assertIsNone(incomplete, 'should return None')

    def test_get_latest_play_returns_completed(self):
        """Should return latest play even if completed."""
        puzzle_id = database.save_puzzle(code='STATE4', size=7)

        play1 = database.start_play(puzzle_id)
        cell_marks = [[0, 1], [2, 0]]
        encoded = game_encoding.encode_board_state(cell_marks)
        database.save_game_state(play1, elapsed_seconds=30, board_state=encoded)
        database.complete_play(play1, duration_ms=30000)

        latest = database.get_latest_play(puzzle_id)

        self.assertIsNotNone(latest, 'should find latest play')
        self.assertEqual(latest['id'], play1, 'should be the right play')
        self.assertEqual(latest['completed'], 1, 'should be completed')
        decoded = game_encoding.decode_board_state(latest['board_state'])
        self.assertEqual(decoded, cell_marks, 'board state should roundtrip')

    def test_get_latest_play_returns_most_recent(self):
        """Should return the most recent play regardless of status."""
        puzzle_id = database.save_puzzle(code='STATE5', size=7)

        play1 = database.start_play(puzzle_id)
        database.complete_play(play1, duration_ms=30000)

        play2 = database.start_play(puzzle_id)
        cell_marks = [[1, 0], [0, 1]]
        encoded = game_encoding.encode_board_state(cell_marks)
        database.save_game_state(play2, elapsed_seconds=15, board_state=encoded)

        latest = database.get_latest_play(puzzle_id)

        self.assertIsNotNone(latest, 'should find latest play')
        self.assertEqual(latest['id'], play2, 'should be most recent')
        self.assertEqual(latest['completed'], 0, 'should be incomplete')


class TestDailyCompletion(unittest.TestCase):
    """Test daily puzzle completion tracking."""

    def setUp(self):
        self.temp_dir = _make_temp_db()

    def tearDown(self):
        _cleanup_db(self.temp_dir)

    def test_is_daily_completed_true(self):
        """Should return True when daily puzzle is completed."""
        puzzle_id = database.save_puzzle(
            code='DAILY1', size=7, daily_date='2025-06-15'
        )
        play_id = database.start_play(puzzle_id)
        database.complete_play(play_id, duration_ms=30000)

        self.assertTrue(database.is_daily_completed('2025-06-15', 7),
                        'should be completed')

    def test_is_daily_completed_false(self):
        """Should return False when daily puzzle is not completed."""
        database.save_puzzle(code='DAILY2', size=7, daily_date='2025-06-15')

        self.assertFalse(database.is_daily_completed('2025-06-15', 7),
                         'should not be completed')

    def test_get_daily_completion_status(self):
        """Should return completion status for all sizes."""
        p6 = database.save_puzzle(code='D6', size=6, daily_date='2025-06-15')
        play6 = database.start_play(p6)
        database.complete_play(play6, duration_ms=20000)

        p8 = database.save_puzzle(code='D8', size=8, daily_date='2025-06-15')
        play8 = database.start_play(p8)
        database.complete_play(play8, duration_ms=40000)

        status = database.get_daily_completion_status('2025-06-15')

        self.assertTrue(status[6], '6x6 should be completed')
        self.assertFalse(status[7], '7x7 should not be completed')
        self.assertTrue(status[8], '8x8 should be completed')

    def test_get_daily_completion_status_started_not_finished(self):
        """Puzzle started but not completed should show as incomplete."""
        p7 = database.save_puzzle(code='D7', size=7, daily_date='2025-06-15')
        database.start_play(p7)

        status = database.get_daily_completion_status('2025-06-15')

        self.assertFalse(status[7], 'started but not finished')

    def test_get_daily_completion_status_no_puzzles(self):
        """Should return all False when no puzzles exist for date."""
        status = database.get_daily_completion_status('2025-01-01')

        self.assertFalse(status[6], 'no puzzles for 6')
        self.assertFalse(status[7], 'no puzzles for 7')
        self.assertFalse(status[8], 'no puzzles for 8')

    def test_get_daily_completion_status_different_dates(self):
        """Completions on other dates should not affect today's status."""
        p_other = database.save_puzzle(code='OTHER', size=7,
                                        daily_date='2025-06-14')
        play_other = database.start_play(p_other)
        database.complete_play(play_other, duration_ms=30000)

        status = database.get_daily_completion_status('2025-06-15')

        self.assertFalse(status[7], 'other date should not count')


if __name__ == "__main__":
    unittest.main()
