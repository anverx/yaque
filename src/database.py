"""Local SQLite database for storing puzzles and play history."""

import os
import sqlite3
from datetime import date, datetime, timedelta
from typing import Any

# Current schema version - increment when making schema changes
SCHEMA_VERSION = 5

# Database will be initialized with actual path when app starts
_db_path: str | None = None
_connection: sqlite3.Connection | None = None


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
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            generation_time_ms INTEGER,
            num_solutions INTEGER,
            kingdom_strategy TEXT,
            generation_attempts INTEGER,
            difficulty_score INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            puzzle_id INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
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
    """Run schema migrations for existing databases, or set version for new ones."""
    existing_version = get_config('schema_version')

    # New database - just set current schema version
    if existing_version is None:
        set_config('schema_version', str(SCHEMA_VERSION))
        return

    # Existing database - run migrations if needed
    current_version = int(existing_version)
    if current_version >= SCHEMA_VERSION:
        return

    # Migration 1 -> 2: Add elapsed_seconds and board_state to plays
    if current_version < 2:
        cursor = _connection.cursor()
        cursor.execute("PRAGMA table_info(plays)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'elapsed_seconds' not in columns:
            cursor.execute('ALTER TABLE plays ADD COLUMN elapsed_seconds INTEGER DEFAULT 0')
        if 'board_state' not in columns:
            cursor.execute('ALTER TABLE plays ADD COLUMN board_state TEXT')
        _connection.commit()

    # Migration 2 -> 3: Add completed_at to plays
    if current_version < 3:
        cursor = _connection.cursor()
        cursor.execute("PRAGMA table_info(plays)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'completed_at' not in columns:
            cursor.execute('ALTER TABLE plays ADD COLUMN completed_at TEXT')
        _connection.commit()

    # Migration 3 -> 4: Add generation_time_ms and num_solutions to puzzles
    if current_version < 4:
        cursor = _connection.cursor()
        cursor.execute("PRAGMA table_info(puzzles)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'generation_time_ms' not in columns:
            cursor.execute('ALTER TABLE puzzles ADD COLUMN generation_time_ms INTEGER')
        if 'num_solutions' not in columns:
            cursor.execute('ALTER TABLE puzzles ADD COLUMN num_solutions INTEGER')
        if 'kingdom_strategy' not in columns:
            cursor.execute('ALTER TABLE puzzles ADD COLUMN kingdom_strategy TEXT')
        _connection.commit()

    # Migration 4 -> 5: Add generation_attempts and difficulty_score to puzzles
    if current_version < 5:
        cursor = _connection.cursor()
        cursor.execute("PRAGMA table_info(puzzles)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'generation_attempts' not in columns:
            cursor.execute('ALTER TABLE puzzles ADD COLUMN generation_attempts INTEGER')
        if 'difficulty_score' not in columns:
            cursor.execute('ALTER TABLE puzzles ADD COLUMN difficulty_score INTEGER')
        _connection.commit()

    set_config('schema_version', str(SCHEMA_VERSION))


# -----------------------------------------------------------------------------
# Config operations (key-value store)
# -----------------------------------------------------------------------------

def get_config(key: str, default: str | None = None) -> str | None:
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


def reset_db() -> None:
    """Wipe and rebuild the database from scratch."""
    global _connection, _db_path
    if _connection:
        _connection.close()
        _connection = None
    if _db_path and os.path.exists(_db_path):
        os.remove(_db_path)
        _connection = sqlite3.connect(_db_path, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _create_tables()


# -----------------------------------------------------------------------------
# Puzzle operations
# -----------------------------------------------------------------------------

def save_puzzle(
    code: str,
    size: int,
    daily_date: str | None = None,
    seed: int | None = None,
    generation_time_ms: int | None = None,
    num_solutions: int | None = None,
    kingdom_strategy: str | None = None,
    generation_attempts: int | None = None,
    difficulty_score: int | None = None
) -> int:
    """Save a puzzle and return its ID. Returns existing ID if puzzle already exists."""
    cursor = _connection.cursor()

    # Check if puzzle already exists
    cursor.execute('SELECT id FROM puzzles WHERE code = ?', (code,))
    row = cursor.fetchone()
    if row:
        return row['id']

    # Insert new puzzle
    cursor.execute('''
        INSERT INTO puzzles (code, size, daily_date, seed, generation_time_ms, num_solutions,
                             kingdom_strategy, generation_attempts, difficulty_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (code, size, daily_date, seed, generation_time_ms, num_solutions,
          kingdom_strategy, generation_attempts, difficulty_score))

    _connection.commit()
    return cursor.lastrowid


def get_puzzle_by_code(code: str) -> dict[str, Any] | None:
    """Get a puzzle by its code."""
    cursor = _connection.cursor()
    cursor.execute('SELECT * FROM puzzles WHERE code = ?', (code,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_puzzle_by_id(puzzle_id: int) -> dict[str, Any] | None:
    """Get a puzzle by its ID."""
    cursor = _connection.cursor()
    cursor.execute('SELECT * FROM puzzles WHERE id = ?', (puzzle_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_daily_puzzles(daily_date: str) -> list[dict[str, Any]]:
    """Get all puzzles for a given date."""
    cursor = _connection.cursor()
    cursor.execute(
        'SELECT * FROM puzzles WHERE daily_date = ? ORDER BY size',
        (daily_date,)
    )
    return [dict(row) for row in cursor.fetchall()]


def get_daily_puzzle(daily_date: str, size: int) -> dict[str, Any] | None:
    """Get a specific daily puzzle by date and size."""
    cursor = _connection.cursor()
    cursor.execute(
        'SELECT * FROM puzzles WHERE daily_date = ? AND size = ?',
        (daily_date, size)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


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
    completed_at = datetime.now().isoformat()
    cursor.execute('''
        UPDATE plays
        SET completed = 1, duration_ms = ?, completed_at = ?
        WHERE id = ?
    ''', (duration_ms, completed_at, play_id))
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


def get_play(play_id: int) -> dict[str, Any] | None:
    """Get a play by its ID."""
    cursor = _connection.cursor()
    cursor.execute('SELECT * FROM plays WHERE id = ?', (play_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_plays_for_puzzle(puzzle_id: int) -> list[dict[str, Any]]:
    """Get all plays for a given puzzle, ordered by start time."""
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT * FROM plays
        WHERE puzzle_id = ?
        ORDER BY started_at DESC
    ''', (puzzle_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_best_time_for_puzzle(puzzle_id: int) -> int | None:
    """Get the best (shortest) completion time for a puzzle in ms."""
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT MIN(duration_ms) as best_time
        FROM plays
        WHERE puzzle_id = ? AND completed = 1
    ''', (puzzle_id,))
    row = cursor.fetchone()
    return row['best_time'] if row and row['best_time'] is not None else None


def get_play_stats() -> dict[str, Any]:
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


def get_recent_plays(limit: int = 10) -> list[dict[str, Any]]:
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

def save_game_state(play_id: int, elapsed_seconds: int, board_state: str) -> None:
    """Save the current game state for resuming later.

    Args:
        play_id: The play session ID
        elapsed_seconds: Time elapsed in seconds
        board_state: Encoded board state string (from game_encoding.encode_board_state)
    """
    cursor = _connection.cursor()
    cursor.execute('''
        UPDATE plays
        SET elapsed_seconds = ?, board_state = ?
        WHERE id = ?
    ''', (elapsed_seconds, board_state, play_id))
    _connection.commit()


def get_incomplete_play(puzzle_id: int) -> dict[str, Any] | None:
    """Get the most recent incomplete play for a puzzle (for resuming).

    Returns dict with board_state as encoded string (use game_encoding.decode_board_state).
    """
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT * FROM plays
        WHERE puzzle_id = ? AND completed = 0
        ORDER BY started_at DESC
        LIMIT 1
    ''', (puzzle_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_latest_play(puzzle_id: int) -> dict[str, Any] | None:
    """Get the most recent play for a puzzle (completed or not).

    Returns dict with board_state as encoded string (use game_encoding.decode_board_state).
    """
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT * FROM plays
        WHERE puzzle_id = ?
        ORDER BY started_at DESC
        LIMIT 1
    ''', (puzzle_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


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


def get_all_plays(limit: int = 20, offset: int = 0, sort_by: str = 'time') -> list[dict[str, Any]]:
    """Get plays for the logbook with pagination and sorting.

    Args:
        limit: Maximum number of records to return
        offset: Number of records to skip
        sort_by: Sort order - 'time' (default), 'size', 'duration', or 'rating'
                 For size/duration/rating, shows only best play per puzzle.
    """
    cursor = _connection.cursor()

    if sort_by == 'time':
        # Show all plays, most recent first
        cursor.execute('''
            SELECT p.id, p.started_at, p.completed_at, p.duration_ms, p.completed,
                   p.fun_rating, pz.code, pz.size, pz.daily_date
            FROM plays p
            JOIN puzzles pz ON p.puzzle_id = pz.id
            ORDER BY p.started_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
    elif sort_by == 'size':
        # One entry per puzzle, sorted by size (largest first)
        cursor.execute('''
            SELECT p.id, p.started_at, p.completed_at, p.duration_ms, p.completed,
                   p.fun_rating, pz.code, pz.size, pz.daily_date
            FROM plays p
            JOIN puzzles pz ON p.puzzle_id = pz.id
            WHERE p.id = (
                SELECT p2.id FROM plays p2
                WHERE p2.puzzle_id = p.puzzle_id
                ORDER BY p2.duration_ms ASC NULLS LAST, p2.started_at DESC
                LIMIT 1
            )
            ORDER BY pz.size DESC, p.started_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
    elif sort_by == 'duration':
        # One entry per puzzle (best time), sorted by duration (longest first = hardest)
        cursor.execute('''
            SELECT p.id, p.started_at, p.completed_at, p.duration_ms, p.completed,
                   p.fun_rating, pz.code, pz.size, pz.daily_date
            FROM plays p
            JOIN puzzles pz ON p.puzzle_id = pz.id
            WHERE p.completed = 1 AND p.id = (
                SELECT p2.id FROM plays p2
                WHERE p2.puzzle_id = p.puzzle_id AND p2.completed = 1
                ORDER BY p2.duration_ms ASC
                LIMIT 1
            )
            ORDER BY p.duration_ms DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
    elif sort_by == 'rating':
        # One entry per puzzle (highest rated), sorted by rating
        cursor.execute('''
            SELECT p.id, p.started_at, p.completed_at, p.duration_ms, p.completed,
                   p.fun_rating, pz.code, pz.size, pz.daily_date
            FROM plays p
            JOIN puzzles pz ON p.puzzle_id = pz.id
            WHERE p.fun_rating IS NOT NULL AND p.id = (
                SELECT p2.id FROM plays p2
                WHERE p2.puzzle_id = p.puzzle_id AND p2.fun_rating IS NOT NULL
                ORDER BY p2.fun_rating DESC
                LIMIT 1
            )
            ORDER BY p.fun_rating DESC, p.started_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
    else:
        # Fallback to time sort
        cursor.execute('''
            SELECT p.id, p.started_at, p.completed_at, p.duration_ms, p.completed,
                   p.fun_rating, pz.code, pz.size, pz.daily_date
            FROM plays p
            JOIN puzzles pz ON p.puzzle_id = pz.id
            ORDER BY p.started_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

    return [dict(row) for row in cursor.fetchall()]


def get_plays_count(sort_by: str = 'time') -> int:
    """Get total number of plays for the given sort mode.

    For time sort, returns all plays. For other sorts, returns unique puzzles.
    """
    cursor = _connection.cursor()

    if sort_by == 'time':
        cursor.execute('SELECT COUNT(*) as count FROM plays')
    elif sort_by == 'duration':
        # Count unique puzzles with completed plays
        cursor.execute('''
            SELECT COUNT(DISTINCT puzzle_id) as count
            FROM plays WHERE completed = 1
        ''')
    elif sort_by == 'rating':
        # Count unique puzzles with ratings
        cursor.execute('''
            SELECT COUNT(DISTINCT puzzle_id) as count
            FROM plays WHERE fun_rating IS NOT NULL
        ''')
    else:  # size or fallback
        # Count unique puzzles
        cursor.execute('SELECT COUNT(DISTINCT puzzle_id) as count FROM plays')

    return cursor.fetchone()['count']


def get_logbook_stats() -> dict[str, Any]:
    """Get statistics for the logbook."""
    cursor = _connection.cursor()

    # Total completed puzzles
    cursor.execute('SELECT COUNT(*) as count FROM plays WHERE completed = 1')
    total_completed = cursor.fetchone()['count']

    # Daily puzzles completed
    cursor.execute('''
        SELECT COUNT(*) as count FROM plays p
        JOIN puzzles pz ON p.puzzle_id = pz.id
        WHERE p.completed = 1 AND pz.daily_date IS NOT NULL
    ''')
    daily_completed = cursor.fetchone()['count']

    # Random puzzles completed
    cursor.execute('''
        SELECT COUNT(*) as count FROM plays p
        JOIN puzzles pz ON p.puzzle_id = pz.id
        WHERE p.completed = 1 AND pz.daily_date IS NULL
    ''')
    random_completed = cursor.fetchone()['count']

    # Gold stars (same-day completions)
    cursor.execute('''
        SELECT COUNT(*) as count FROM plays p
        JOIN puzzles pz ON p.puzzle_id = pz.id
        WHERE p.completed = 1 AND pz.daily_date IS NOT NULL
        AND date(p.completed_at) = pz.daily_date
    ''')
    gold_stars = cursor.fetchone()['count']

    # Best times by size
    cursor.execute('''
        SELECT pz.size, MIN(p.duration_ms) as best_time
        FROM plays p
        JOIN puzzles pz ON p.puzzle_id = pz.id
        WHERE p.completed = 1
        GROUP BY pz.size
    ''')
    best_times = {row['size']: row['best_time'] for row in cursor.fetchall()}

    # Total play time
    cursor.execute('SELECT SUM(duration_ms) as total FROM plays WHERE completed = 1')
    total_time_ms = cursor.fetchone()['total'] or 0

    return {
        'total_completed': total_completed,
        'daily_completed': daily_completed,
        'random_completed': random_completed,
        'gold_stars': gold_stars,
        'best_times': best_times,
        'total_time_ms': total_time_ms,
    }


def get_time_stats_by_size() -> dict[int, dict[str, Any]]:
    """Get best and average solve times grouped by puzzle size.

    Returns:
        Dict mapping size to {'best_time': ms, 'avg_time': ms, 'play_count': int}
    """
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT pz.size,
               MIN(p.duration_ms) as best_time,
               AVG(p.duration_ms) as avg_time,
               COUNT(*) as play_count
        FROM plays p
        JOIN puzzles pz ON p.puzzle_id = pz.id
        WHERE p.completed = 1
        GROUP BY pz.size
        ORDER BY pz.size
    ''')
    return {
        row['size']: {
            'best_time': row['best_time'],
            'avg_time': int(row['avg_time']) if row['avg_time'] else None,
            'play_count': row['play_count'],
        }
        for row in cursor.fetchall()
    }


def get_games_per_day(days: int = 30) -> list[tuple[str, dict[int, int]]]:
    """Get completed game counts per day broken down by board size.

    Returns:
        List of (date_str, {size: count}) tuples for each day, oldest first.
        Days with zero games are included with empty size dicts.
    """
    cursor = _connection.cursor()
    today = date.today()
    start = today - timedelta(days=days - 1)

    cursor.execute('''
        SELECT date(p.completed_at) as day, pz.size, COUNT(*) as count
        FROM plays p
        JOIN puzzles pz ON p.puzzle_id = pz.id
        WHERE p.completed = 1 AND date(p.completed_at) >= ?
        GROUP BY day, pz.size
        ORDER BY day
    ''', (start.isoformat(),))

    counts: dict[str, dict[int, int]] = {}
    for row in cursor.fetchall():
        day = row['day']
        if day not in counts:
            counts[day] = {}
        counts[day][row['size']] = row['count']

    # Fill in all days (including zeros)
    result = []
    d = start
    while d <= today:
        d_str = d.isoformat()
        result.append((d_str, counts.get(d_str, {})))
        d += timedelta(days=1)
    return result


def get_minutes_per_day(days: int = 30) -> list[tuple[str, dict[int, int]]]:
    """Get total play time in minutes per day, broken down by board size.

    Returns:
        List of (date_str, {size: minutes}) tuples for each day, oldest first.
        Days with zero games are included with empty size dicts.
    """
    cursor = _connection.cursor()
    today = date.today()
    start = today - timedelta(days=days - 1)

    cursor.execute('''
        SELECT date(p.completed_at) as day, pz.size, SUM(p.duration_ms) as total_ms
        FROM plays p
        JOIN puzzles pz ON p.puzzle_id = pz.id
        WHERE p.completed = 1 AND p.duration_ms IS NOT NULL
              AND date(p.completed_at) >= ?
        GROUP BY day, pz.size
        ORDER BY day
    ''', (start.isoformat(),))

    minutes: dict[str, dict[int, int]] = {}
    for row in cursor.fetchall():
        day = row['day']
        if day not in minutes:
            minutes[day] = {}
        # Round up to at least 1 minute if any time was spent
        mins = max(1, round(row['total_ms'] / 60000)) if row['total_ms'] else 0
        if mins > 0:
            minutes[day][row['size']] = mins

    result = []
    d = start
    while d <= today:
        d_str = d.isoformat()
        result.append((d_str, minutes.get(d_str, {})))
        d += timedelta(days=1)
    return result


def get_daily_completion_status(daily_date: str) -> dict[int, bool]:
    """Get completion status for all sizes on a given date (single query)."""
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT pz.size, MAX(p.completed) as won
        FROM puzzles pz
        LEFT JOIN plays p ON p.puzzle_id = pz.id AND p.completed = 1
        WHERE pz.daily_date = ?
        GROUP BY pz.size
    ''', (daily_date,))

    # Start with all sizes as incomplete
    status = {6: False, 7: False, 8: False}
    for row in cursor.fetchall():
        status[row['size']] = row['won'] == 1
    return status


def get_month_completion_raw(year: int, month: int) -> dict[str, dict[int, str | None]]:
    """Get completion status for all days in a month (single query).

    Returns dict mapping date strings to {size: status} dicts where status is:
    - None: not completed
    - 'gold': completed on the same day as daily_date
    - 'silver': completed on a later day
    """
    cursor = _connection.cursor()
    # Match dates like '2026-02-%' for February 2026
    date_pattern = f'{year:04d}-{month:02d}-%'

    cursor.execute('''
        SELECT pz.daily_date, pz.size, MIN(p.completed_at) as first_completed_at
        FROM puzzles pz
        LEFT JOIN plays p ON p.puzzle_id = pz.id AND p.completed = 1
        WHERE pz.daily_date LIKE ?
        GROUP BY pz.daily_date, pz.size
    ''', (date_pattern,))

    result = {}
    for row in cursor.fetchall():
        date_str = row['daily_date']
        if date_str not in result:
            result[date_str] = {6: None, 7: None, 8: None}

        completed_at = row['first_completed_at']
        if completed_at:
            # Compare just the date part (first 10 chars: YYYY-MM-DD)
            completed_date = completed_at[:10]
            if completed_date == date_str:
                result[date_str][row['size']] = 'gold'
            else:
                result[date_str][row['size']] = 'silver'

    return result


def get_played_dates() -> set[str]:
    """Return the set of dates where the daily puzzle was played on the day."""
    cursor = _connection.cursor()
    cursor.execute('''
        SELECT DISTINCT pz.daily_date
        FROM plays p
        JOIN puzzles pz ON p.puzzle_id = pz.id
        WHERE pz.daily_date IS NOT NULL
        AND date(p.started_at) = pz.daily_date
        ORDER BY pz.daily_date ASC
    ''')
    return {row['daily_date'] for row in cursor.fetchall()}


# -----------------------------------------------------------------------------
# Export functions (for dev menu)
# -----------------------------------------------------------------------------

def get_db_path() -> str | None:
    """Get the path to the database file."""
    return _db_path


def export_to_json() -> dict[str, Any]:
    """Export the entire database to a JSON-serializable dict."""
    cursor = _connection.cursor()

    # Export puzzles
    cursor.execute('SELECT * FROM puzzles ORDER BY id')
    puzzles = [dict(row) for row in cursor.fetchall()]

    # Export plays
    cursor.execute('SELECT * FROM plays ORDER BY id')
    plays = [dict(row) for row in cursor.fetchall()]

    # Export config
    cursor.execute('SELECT * FROM config')
    config = {row['key']: row['value'] for row in cursor.fetchall()}

    return {
        'exported_at': datetime.now().isoformat(),
        'schema_version': SCHEMA_VERSION,
        'puzzles': puzzles,
        'plays': plays,
        'config': config,
    }


def get_avg_generation_time(size: int, unique: bool) -> int | None:
    """Get average generation time in ms for a given size and uniqueness.

    Args:
        size: Board size
        unique: True for single-solution puzzles, False for multi-solution
    """
    cursor = _connection.cursor()
    if unique:
        cursor.execute('''
            SELECT AVG(generation_time_ms) as avg_time, COUNT(*) as cnt
            FROM puzzles
            WHERE size = ? AND generation_time_ms IS NOT NULL
            AND num_solutions = 1
        ''', (size,))
    else:
        cursor.execute('''
            SELECT AVG(generation_time_ms) as avg_time, COUNT(*) as cnt
            FROM puzzles
            WHERE size = ? AND generation_time_ms IS NOT NULL
            AND num_solutions > 1
        ''', (size,))
    row = cursor.fetchone()
    if row and row['avg_time'] and row['cnt'] >= 10:
        return int(row['avg_time'])
    return None


def get_generation_stats() -> dict[str, Any]:
    """Get statistics about puzzle generation times."""
    cursor = _connection.cursor()

    # Overall stats
    cursor.execute('''
        SELECT
            COUNT(*) as total,
            AVG(generation_time_ms) as avg_time,
            MIN(generation_time_ms) as min_time,
            MAX(generation_time_ms) as max_time,
            AVG(generation_attempts) as avg_attempts,
            AVG(difficulty_score) as avg_difficulty
        FROM puzzles
        WHERE generation_time_ms IS NOT NULL
    ''')
    overall = dict(cursor.fetchone())

    # Stats by size
    cursor.execute('''
        SELECT
            size,
            COUNT(*) as count,
            AVG(generation_time_ms) as avg_time,
            MIN(generation_time_ms) as min_time,
            MAX(generation_time_ms) as max_time,
            AVG(generation_attempts) as avg_attempts,
            AVG(difficulty_score) as avg_difficulty
        FROM puzzles
        WHERE generation_time_ms IS NOT NULL
        GROUP BY size
        ORDER BY size
    ''')
    by_size = [dict(row) for row in cursor.fetchall()]

    # Stats by num_solutions
    cursor.execute('''
        SELECT
            num_solutions,
            COUNT(*) as count,
            AVG(generation_time_ms) as avg_time
        FROM puzzles
        WHERE generation_time_ms IS NOT NULL AND num_solutions IS NOT NULL
        GROUP BY num_solutions
        ORDER BY num_solutions
    ''')
    by_solutions = [dict(row) for row in cursor.fetchall()]

    return {
        'overall': overall,
        'by_size': by_size,
        'by_solutions': by_solutions,
    }


def import_from_json(data: dict[str, Any]) -> dict[str, int]:
    """Import data from a JSON export into the database.

    Args:
        data: Dictionary from export_to_json() format

    Returns:
        Dict with counts of imported records: {'puzzles': n, 'plays': n}
    """
    cursor = _connection.cursor()
    puzzles_imported = 0
    plays_imported = 0

    # Map old puzzle IDs to new IDs for plays import
    puzzle_id_map = {}

    # Import puzzles
    for puzzle in data.get('puzzles', []):
        old_id = puzzle['id']
        # Check if puzzle already exists by code
        cursor.execute('SELECT id FROM puzzles WHERE code = ?', (puzzle['code'],))
        existing = cursor.fetchone()

        if existing:
            puzzle_id_map[old_id] = existing['id']
        else:
            cursor.execute('''
                INSERT INTO puzzles (code, size, daily_date, seed, created_at,
                                     generation_time_ms, num_solutions, kingdom_strategy,
                                     generation_attempts, difficulty_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                puzzle['code'],
                puzzle['size'],
                puzzle.get('daily_date'),
                puzzle.get('seed'),
                puzzle.get('created_at', datetime.now().isoformat()),
                puzzle.get('generation_time_ms'),
                puzzle.get('num_solutions'),
                puzzle.get('kingdom_strategy'),
                puzzle.get('generation_attempts'),
                puzzle.get('difficulty_score'),
            ))
            puzzle_id_map[old_id] = cursor.lastrowid
            puzzles_imported += 1

    # Import plays
    for play in data.get('plays', []):
        old_puzzle_id = play['puzzle_id']
        new_puzzle_id = puzzle_id_map.get(old_puzzle_id)

        if new_puzzle_id is None:
            continue  # Skip plays for puzzles we couldn't map

        # Check if this exact play already exists (by puzzle_id and started_at)
        cursor.execute('''
            SELECT id FROM plays WHERE puzzle_id = ? AND started_at = ?
        ''', (new_puzzle_id, play['started_at']))

        if cursor.fetchone():
            continue  # Already exists

        cursor.execute('''
            INSERT INTO plays (puzzle_id, started_at, completed_at, duration_ms,
                               completed, fun_rating, elapsed_seconds, board_state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_puzzle_id,
            play['started_at'],
            play.get('completed_at'),
            play.get('duration_ms'),
            play.get('completed', 0),
            play.get('fun_rating'),
            play.get('elapsed_seconds', 0),
            play.get('board_state'),
        ))
        plays_imported += 1

    _connection.commit()
    return {'puzzles': puzzles_imported, 'plays': plays_imported}
