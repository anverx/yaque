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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
