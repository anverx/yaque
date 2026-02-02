"""Local SQLite database for storing puzzles and play history."""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# Current schema version - increment when making schema changes
SCHEMA_VERSION = 2

# Database will be initialized with actual path when app starts
_db_path: Optional[str] = None
_connection: Optional[sqlite3.Connection] = None


def init_db(data_dir: str) -> None:
    """Initialize the database in the given directory."""
    global _db_path, _connection

    os.makedirs(data_dir, exist_ok=True)
    _db_path = os.path.join(data_dir, 'yaque.db')

    _connection = sqlite3.connect(_db_path, check_same_thread=False)
    _connection.row_factory = sqlite3.Row

    _create_tables()
    _run_migrations()


def _create_tables() -> None:
    """Create database tables if they don't exist."""
    cursor = _connection.cursor()

    # Config table for key-value settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS puzzles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            size INTEGER NOT NULL,
            daily_date TEXT,
            seed INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            puzzle_id INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            duration_ms INTEGER,
            completed INTEGER NOT NULL DEFAULT 0,
            fun_rating INTEGER,
            elapsed_seconds INTEGER DEFAULT 0,
            board_state TEXT,
            FOREIGN KEY (puzzle_id) REFERENCES puzzles (id)
        )
    ''')

    # Index for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_puzzles_code ON puzzles (code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_puzzles_daily_date ON puzzles (daily_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_plays_puzzle_id ON plays (puzzle_id)')

    _connection.commit()


def _run_migrations() -> None:
    """Run any necessary schema migrations."""
    current_version = int(get_config('schema_version', '0'))

    if current_version < 1:
        # Migration 1: Add elapsed_seconds and board_state to plays
        cursor = _connection.cursor()
        cursor.execute("PRAGMA table_info(plays)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'elapsed_seconds' not in columns:
            cursor.execute('ALTER TABLE plays ADD COLUMN elapsed_seconds INTEGER DEFAULT 0')
        if 'board_state' not in columns:
            cursor.execute('ALTER TABLE plays ADD COLUMN board_state TEXT')
        _connection.commit()

    if current_version < 2:
        # Migration 2: (placeholder for future migrations)
        pass

    # Update schema version
    set_config('schema_version', str(SCHEMA_VERSION))


# -----------------------------------------------------------------------------
# Config operations (key-value store)
# -----------------------------------------------------------------------------

def get_config(key: str, default: str = None) -> Optional[str]:
    """Get a config value by key."""
    cursor = _connection.cursor()
    cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
    row = cursor.fetchone()
    return row['value'] if row else default


def set_config(key: str, value: str) -> None:
    """Set a config value."""
    cursor = _connection.cursor()
    cursor.execute('''
        INSERT INTO config (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    ''', (key, value))
    _connection.commit()


def delete_config(key: str) -> None:
    """Delete a config value."""
    cursor = _connection.cursor()
    cursor.execute('DELETE FROM config WHERE key = ?', (key,))
    _connection.commit()


def close_db() -> None:
    """Close the database connection."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None


# -----------------------------------------------------------------------------
# Puzzle operations
# -----------------------------------------------------------------------------

def save_puzzle(code: str, size: int, daily_date: str = None, seed: int = None) -> int:
    """Save a puzzle and return its ID. Returns existing ID if puzzle already exists."""
    cursor = _connection.cursor()

    # Check if puzzle already exists
    cursor.execute('SELECT id FROM puzzles WHERE code = ?', (code,))
    row = cursor.fetchone()
    if row:
        return row['id']

    # Insert new puzzle
    cursor.execute('''
        INSERT INTO puzzles (code, size, daily_date, seed)
        VALUES (?, ?, ?, ?)
    ''', (code, size, daily_date, seed))

    _connection.commit()
    return cursor.lastrowid


def get_puzzle_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Get a puzzle by its code."""
    cursor = _connection.cursor()
    cursor.execute('SELECT * FROM puzzles WHERE code = ?', (code,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_puzzle_by_id(puzzle_id: int) -> Optional[Dict[str, Any]]:
    """Get a puzzle by its ID."""
    cursor = _connection.cursor()
    cursor.execute('SELECT * FROM puzzles WHERE id = ?', (puzzle_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_daily_puzzles(daily_date: str) -> List[Dict[str, Any]]:
    """Get all puzzles for a given date."""
    cursor = _connection.cursor()
    cursor.execute(
        'SELECT * FROM puzzles WHERE daily_date = ? ORDER BY size',
        (daily_date,)
    )
    return [dict(row) for row in cursor.fetchall()]


# -----------------------------------------------------------------------------
# Play operations
# -----------------------------------------------------------------------------

def start_play(puzzle_id: int) -> int:
    """Start a new play session and return its ID."""
    cursor = _connection.cursor()
    started_at = datetime.now().isoformat()

    cursor.execute('''
        INSERT INTO plays (puzzle_id, started_at)
        VALUES (?, ?)
    ''', (puzzle_id, started_at))

    _connection.commit()
    return cursor.lastrowid


def complete_play(play_id: int, duration_ms: int) -> None:
    """Mark a play as completed with the given duration."""
    cursor = _connection.cursor()
    cursor.execute('''
        UPDATE plays
        SET completed = 1, duration_ms = ?
        WHERE id = ?
    ''', (duration_ms, play_id))
    _connection.commit()


def rate_play(play_id: int, fun_rating: int) -> None:
    """Add a fun rating to a play (e.g., 1-5 stars)."""
    cursor = _connection.cursor()
    cursor.execute('''
        UPDATE plays
        SET fun_rating = ?
        WHERE id = ?
    ''', (fun_rating, play_id))
    _connection.commit()


def get_play(play_id: int) -> Optional[Dict[str, Any]]:
    """Get a play by its ID."""
    cursor = _connection.cursor()
    cursor.execute('SELECT * FROM plays WHERE id = ?', (play_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_plays_for_puzzle(puzzle_id: int) -> List[Dict[str, Any]]:
    """Get all plays for a given puzzle, ordered by start time."""
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT * FROM plays
        WHERE puzzle_id = ?
        ORDER BY started_at DESC
    ''', (puzzle_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_best_time_for_puzzle(puzzle_id: int) -> Optional[int]:
    """Get the best (shortest) completion time for a puzzle in ms."""
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT MIN(duration_ms) as best_time
        FROM plays
        WHERE puzzle_id = ? AND completed = 1
    ''', (puzzle_id,))
    row = cursor.fetchone()
    return row['best_time'] if row and row['best_time'] is not None else None


def get_play_stats() -> Dict[str, Any]:
    """Get overall play statistics."""
    cursor = _connection.cursor()

    cursor.execute('SELECT COUNT(*) as total FROM plays')
    total_plays = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) as completed FROM plays WHERE completed = 1')
    completed_plays = cursor.fetchone()['completed']

    cursor.execute('''
        SELECT AVG(duration_ms) as avg_time
        FROM plays
        WHERE completed = 1
    ''')
    avg_time = cursor.fetchone()['avg_time']

    return {
        'total_plays': total_plays,
        'completed_plays': completed_plays,
        'average_time_ms': int(avg_time) if avg_time else None,
    }


def get_recent_plays(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent plays with puzzle info."""
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT p.*, pz.code, pz.size, pz.daily_date
        FROM plays p
        JOIN puzzles pz ON p.puzzle_id = pz.id
        ORDER BY p.started_at DESC
        LIMIT ?
    ''', (limit,))
    return [dict(row) for row in cursor.fetchall()]


# -----------------------------------------------------------------------------
# Game state operations
# -----------------------------------------------------------------------------

def save_game_state(play_id: int, elapsed_seconds: int, cell_marks: List[List[int]]) -> None:
    """Save the current game state for resuming later."""
    cursor = _connection.cursor()
    board_state = json.dumps(cell_marks)
    cursor.execute('''
        UPDATE plays
        SET elapsed_seconds = ?, board_state = ?
        WHERE id = ?
    ''', (elapsed_seconds, board_state, play_id))
    _connection.commit()


def get_incomplete_play(puzzle_id: int) -> Optional[Dict[str, Any]]:
    """Get the most recent incomplete play for a puzzle (for resuming)."""
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT * FROM plays
        WHERE puzzle_id = ? AND completed = 0
        ORDER BY started_at DESC
        LIMIT 1
    ''', (puzzle_id,))
    row = cursor.fetchone()
    if row:
        result = dict(row)
        if result.get('board_state'):
            result['board_state'] = json.loads(result['board_state'])
        return result
    return None


def is_daily_completed(daily_date: str, size: int) -> bool:
    """Check if a daily puzzle has been completed."""
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM plays p
        JOIN puzzles pz ON p.puzzle_id = pz.id
        WHERE pz.daily_date = ? AND pz.size = ? AND p.completed = 1
    ''', (daily_date, size))
    return cursor.fetchone()['count'] > 0


def get_daily_completion_status(daily_date: str) -> Dict[int, bool]:
    """Get completion status for all sizes on a given date."""
    return {
        size: is_daily_completed(daily_date, size)
        for size in [6, 7, 8]
    }
