"""Tests for database module."""

import pytest
import os
import sys
import tempfile
import shutil

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    database.init_db(temp_dir)
    yield temp_dir
    database.close_db()
    shutil.rmtree(temp_dir)


class TestPuzzleOperations:
    """Test puzzle CRUD operations."""

    def test_save_puzzle(self, temp_db):
        """Should save a puzzle and return its ID."""
        puzzle_id = database.save_puzzle(
            code='ABC123',
            size=7,
            daily_date='2025-06-15',
            seed=42
        )
        assert puzzle_id is not None
        assert puzzle_id > 0

    def test_save_duplicate_puzzle_returns_existing_id(self, temp_db):
        """Saving same puzzle twice should return existing ID."""
        id1 = database.save_puzzle(code='ABC123', size=7)
        id2 = database.save_puzzle(code='ABC123', size=7)
        assert id1 == id2

    def test_get_puzzle_by_code(self, temp_db):
        """Should retrieve puzzle by code."""
        database.save_puzzle(code='XYZ789', size=8, daily_date='2025-01-01')

        puzzle = database.get_puzzle_by_code('XYZ789')

        assert puzzle is not None
        assert puzzle['code'] == 'XYZ789'
        assert puzzle['size'] == 8
        assert puzzle['daily_date'] == '2025-01-01'

    def test_get_puzzle_by_code_not_found(self, temp_db):
        """Should return None for non-existent code."""
        puzzle = database.get_puzzle_by_code('NONEXISTENT')
        assert puzzle is None

    def test_get_puzzle_by_id(self, temp_db):
        """Should retrieve puzzle by ID."""
        puzzle_id = database.save_puzzle(code='TEST1', size=6)

        puzzle = database.get_puzzle_by_id(puzzle_id)

        assert puzzle is not None
        assert puzzle['id'] == puzzle_id
        assert puzzle['code'] == 'TEST1'

    def test_get_daily_puzzles(self, temp_db):
        """Should retrieve all puzzles for a date, ordered by size."""
        database.save_puzzle(code='D1', size=8, daily_date='2025-06-15')
        database.save_puzzle(code='D2', size=6, daily_date='2025-06-15')
        database.save_puzzle(code='D3', size=7, daily_date='2025-06-15')
        database.save_puzzle(code='OTHER', size=7, daily_date='2025-06-16')

        puzzles = database.get_daily_puzzles('2025-06-15')

        assert len(puzzles) == 3
        assert puzzles[0]['size'] == 6
        assert puzzles[1]['size'] == 7
        assert puzzles[2]['size'] == 8


class TestPlayOperations:
    """Test play tracking operations."""

    def test_start_play(self, temp_db):
        """Should start a play session."""
        puzzle_id = database.save_puzzle(code='PLAY1', size=7)

        play_id = database.start_play(puzzle_id)

        assert play_id is not None
        assert play_id > 0

    def test_complete_play(self, temp_db):
        """Should mark play as completed with duration."""
        puzzle_id = database.save_puzzle(code='PLAY2', size=7)
        play_id = database.start_play(puzzle_id)

        database.complete_play(play_id, duration_ms=45000)

        play = database.get_play(play_id)
        assert play['completed'] == 1
        assert play['duration_ms'] == 45000

    def test_rate_play(self, temp_db):
        """Should add rating to play."""
        puzzle_id = database.save_puzzle(code='PLAY3', size=7)
        play_id = database.start_play(puzzle_id)
        database.complete_play(play_id, duration_ms=30000)

        database.rate_play(play_id, fun_rating=5)

        play = database.get_play(play_id)
        assert play['fun_rating'] == 5

    def test_get_plays_for_puzzle(self, temp_db):
        """Should get all plays for a puzzle."""
        puzzle_id = database.save_puzzle(code='PLAY4', size=7)
        database.start_play(puzzle_id)
        database.start_play(puzzle_id)
        database.start_play(puzzle_id)

        plays = database.get_plays_for_puzzle(puzzle_id)

        assert len(plays) == 3

    def test_get_best_time_for_puzzle(self, temp_db):
        """Should return best completion time."""
        puzzle_id = database.save_puzzle(code='PLAY5', size=7)

        # Create some completed plays with different times
        play1 = database.start_play(puzzle_id)
        database.complete_play(play1, duration_ms=60000)

        play2 = database.start_play(puzzle_id)
        database.complete_play(play2, duration_ms=45000)  # Best time

        play3 = database.start_play(puzzle_id)
        database.complete_play(play3, duration_ms=55000)

        # One incomplete play
        database.start_play(puzzle_id)

        best = database.get_best_time_for_puzzle(puzzle_id)
        assert best == 45000

    def test_get_best_time_no_completions(self, temp_db):
        """Should return None if no completed plays."""
        puzzle_id = database.save_puzzle(code='PLAY6', size=7)
        database.start_play(puzzle_id)  # Not completed

        best = database.get_best_time_for_puzzle(puzzle_id)
        assert best is None


class TestStatistics:
    """Test statistics functions."""

    def test_get_play_stats(self, temp_db):
        """Should return overall statistics."""
        puzzle_id = database.save_puzzle(code='STATS1', size=7)

        # 3 plays, 2 completed
        play1 = database.start_play(puzzle_id)
        database.complete_play(play1, duration_ms=40000)

        play2 = database.start_play(puzzle_id)
        database.complete_play(play2, duration_ms=60000)

        database.start_play(puzzle_id)  # Not completed

        stats = database.get_play_stats()

        assert stats['total_plays'] == 3
        assert stats['completed_plays'] == 2
        assert stats['average_time_ms'] == 50000

    def test_get_recent_plays(self, temp_db):
        """Should return recent plays with puzzle info."""
        puzzle_id = database.save_puzzle(code='RECENT1', size=7, daily_date='2025-06-15')
        play1 = database.start_play(puzzle_id)
        database.complete_play(play1, duration_ms=30000)

        play2 = database.start_play(puzzle_id)

        plays = database.get_recent_plays(limit=10)

        assert len(plays) == 2
        assert plays[0]['code'] == 'RECENT1'
        assert plays[0]['size'] == 7


class TestConfig:
    """Test config key-value store."""

    def test_get_set_config(self, temp_db):
        """Should store and retrieve config values."""
        database.set_config('test_key', 'test_value')
        assert database.get_config('test_key') == 'test_value'

    def test_get_config_default(self, temp_db):
        """Should return default for missing keys."""
        assert database.get_config('missing', 'default') == 'default'
        assert database.get_config('missing') is None

    def test_set_config_overwrites(self, temp_db):
        """Should overwrite existing values."""
        database.set_config('key', 'value1')
        database.set_config('key', 'value2')
        assert database.get_config('key') == 'value2'

    def test_delete_config(self, temp_db):
        """Should delete config values."""
        database.set_config('to_delete', 'value')
        database.delete_config('to_delete')
        assert database.get_config('to_delete') is None

    def test_schema_version_set(self, temp_db):
        """Schema version should be set after init."""
        version = database.get_config('schema_version')
        assert version is not None
        assert int(version) >= 1


class TestGameState:
    """Test game state save/restore operations."""

    def test_save_game_state(self, temp_db):
        """Should save board state and elapsed time."""
        puzzle_id = database.save_puzzle(code='STATE1', size=7)
        play_id = database.start_play(puzzle_id)

        cell_marks = [[0, 1, 2], [1, 0, 2], [2, 1, 0]]
        database.save_game_state(play_id, elapsed_seconds=45, cell_marks=cell_marks)

        play = database.get_play(play_id)
        assert play['elapsed_seconds'] == 45

    def test_get_incomplete_play(self, temp_db):
        """Should get the most recent incomplete play with board state."""
        puzzle_id = database.save_puzzle(code='STATE2', size=7)

        # Complete play
        play1 = database.start_play(puzzle_id)
        database.complete_play(play1, duration_ms=30000)

        # Incomplete play with state
        play2 = database.start_play(puzzle_id)
        cell_marks = [[0, 1], [2, 0]]
        database.save_game_state(play2, elapsed_seconds=20, cell_marks=cell_marks)

        incomplete = database.get_incomplete_play(puzzle_id)

        assert incomplete is not None
        assert incomplete['id'] == play2
        assert incomplete['elapsed_seconds'] == 20
        assert incomplete['board_state'] == cell_marks

    def test_get_incomplete_play_none_when_all_complete(self, temp_db):
        """Should return None if all plays are complete."""
        puzzle_id = database.save_puzzle(code='STATE3', size=7)
        play_id = database.start_play(puzzle_id)
        database.complete_play(play_id, duration_ms=30000)

        incomplete = database.get_incomplete_play(puzzle_id)
        assert incomplete is None


class TestDailyCompletion:
    """Test daily puzzle completion tracking."""

    def test_is_daily_completed_true(self, temp_db):
        """Should return True when daily puzzle is completed."""
        puzzle_id = database.save_puzzle(
            code='DAILY1', size=7, daily_date='2025-06-15'
        )
        play_id = database.start_play(puzzle_id)
        database.complete_play(play_id, duration_ms=30000)

        assert database.is_daily_completed('2025-06-15', 7) is True

    def test_is_daily_completed_false(self, temp_db):
        """Should return False when daily puzzle is not completed."""
        database.save_puzzle(code='DAILY2', size=7, daily_date='2025-06-15')

        assert database.is_daily_completed('2025-06-15', 7) is False

    def test_get_daily_completion_status(self, temp_db):
        """Should return completion status for all sizes."""
        # Complete 6x6 and 8x8
        p6 = database.save_puzzle(code='D6', size=6, daily_date='2025-06-15')
        play6 = database.start_play(p6)
        database.complete_play(play6, duration_ms=20000)

        p8 = database.save_puzzle(code='D8', size=8, daily_date='2025-06-15')
        play8 = database.start_play(p8)
        database.complete_play(play8, duration_ms=40000)

        # 7x7 not played
        status = database.get_daily_completion_status('2025-06-15')

        assert status[6] is True
        assert status[7] is False
        assert status[8] is True

    def test_get_daily_completion_status_started_not_finished(self, temp_db):
        """Puzzle started but not completed should show as incomplete."""
        p7 = database.save_puzzle(code='D7', size=7, daily_date='2025-06-15')
        database.start_play(p7)  # Started but not completed

        status = database.get_daily_completion_status('2025-06-15')

        assert status[7] is False

    def test_get_daily_completion_status_no_puzzles(self, temp_db):
        """Should return all False when no puzzles exist for date."""
        status = database.get_daily_completion_status('2025-01-01')

        assert status[6] is False
        assert status[7] is False
        assert status[8] is False

    def test_get_daily_completion_status_different_dates(self, temp_db):
        """Completions on other dates should not affect today's status."""
        # Complete puzzle on different date
        p_other = database.save_puzzle(code='OTHER', size=7, daily_date='2025-06-14')
        play_other = database.start_play(p_other)
        database.complete_play(play_other, duration_ms=30000)

        # Check today's status (no puzzles)
        status = database.get_daily_completion_status('2025-06-15')

        assert status[7] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
