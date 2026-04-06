"""Logic and data access for calendar features."""

from __future__ import annotations

from datetime import date, timedelta
from enum import Enum
from typing import NamedTuple

import database

_MONTH_NAMES = (
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
)


def _last_day_of_month(year: int, month: int) -> int:
    """Return the last day of the given month."""
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - date(year, month, 1)).days


class CompletionStatus(Enum):
    """Status of a daily puzzle completion."""
    GOLD = 'gold'      # Completed on the same day
    SILVER = 'silver'  # Completed on a later day


class CalendarData(NamedTuple):
    """All data needed to render a calendar month."""
    month_name: str
    streak_text: str
    protected_dates: set[str]
    month_status: dict[str, dict]
    month_crown: CompletionStatus | None


class CalendarState:
    """Tracks current year/month, handles navigation and data fetching."""

    def __init__(self) -> None:
        today = date.today()
        self.year = today.year
        self.month = today.month

    def is_past_month(self) -> bool:
        today = date.today()
        return (
            self.year < today.year
            or (self.year == today.year and self.month < today.month)
        )

    def prev_month(self) -> None:
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1

    def next_month(self) -> bool:
        """Advance to next month. Returns False if already at current month."""
        today = date.today()
        if self.year == today.year and self.month >= today.month:
            return False
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        return True

    def fetch_data(self) -> CalendarData:
        """Fetch all data needed to render the current month."""
        info = get_streak_info()
        month_status = get_month_completion_status(self.year, self.month)

        last_day = _last_day_of_month(self.year, self.month)
        month_crown = (
            get_month_crown(month_status, self.year, self.month, last_day)
            if self.is_past_month() else None
        )

        return CalendarData(
            month_name=f'{_MONTH_NAMES[self.month]} {self.year}',
            streak_text=format_streak_text(info.streak, info.protections_available),
            protected_dates=set(info.protected_dates),
            month_status=month_status,
            month_crown=month_crown,
        )


class StreakInfo(NamedTuple):
    """Streak calculation result with protection details."""

    streak: int                # Total length including protected days
    protections_available: int # Remaining protection points (0-2)
    protections_used: int      # Points consumed by gap days
    protected_dates: list[str] # ISO dates of protected gaps


# Streak protection milestones and cap
_PROTECTION_MILESTONES = [10, 30]
_MAX_BANKED = 2


def _is_gap_protected(gap: date, played_dates: set[str]) -> bool:
    """Check if a gap day is protected by earned points.

    Looks back from the gap for consecutive play days:
    - 10 consecutive before gap → protected (1 point earned)
    - If a skip exists in those 10, check 30 before that skip →
      if all played, both gaps protected (2 points earned)
    - Otherwise streak is broken
    """
    for i in range(1, 11):
        d_str = (gap - timedelta(days=i)).isoformat()
        if d_str not in played_dates:
            # Found inner gap. Check 30 days before it.
            inner_gap = gap - timedelta(days=i)
            for j in range(1, 31):
                d2_str = (inner_gap - timedelta(days=j)).isoformat()
                if d2_str not in played_dates:
                    return False
            return True
    return True


def compute_streak(played_dates: set[str], ref_date: date) -> StreakInfo:
    """Compute streak info from a set of played dates (pure function).

    Uses a backward walk from ref_date to find streak extent, then a
    forward pass over the streak to compute banked protection points.
    """
    if not played_dates:
        return StreakInfo(0, 0, 0, [])

    today_str = ref_date.isoformat()
    yesterday_str = (ref_date - timedelta(days=1)).isoformat()

    # Determine streak end (grace period)
    if today_str in played_dates:
        end = ref_date
    elif yesterday_str in played_dates:
        end = ref_date - timedelta(days=1)
    else:
        return StreakInfo(0, 0, 0, [])

    # Backward walk to find streak start
    d = end
    while True:
        prev = d - timedelta(days=1)
        prev_str = prev.isoformat()
        if prev_str in played_dates or _is_gap_protected(prev, played_dates):
            d = prev
        else:
            break
    start = d

    # Forward pass over the streak to compute details
    banked = 0
    consecutive = 0
    protected_dates: list[str] = []

    d = start
    streak_len = 0
    while d <= end:
        d_str = d.isoformat()
        streak_len += 1
        if d_str in played_dates:
            consecutive += 1
            if banked < _MAX_BANKED and consecutive in _PROTECTION_MILESTONES:
                banked += 1
        else:
            banked -= 1
            consecutive = 0
            protected_dates.append(d_str)
        d += timedelta(days=1)

    return StreakInfo(
        streak=streak_len,
        protections_available=banked,
        protections_used=len(protected_dates),
        protected_dates=protected_dates,
    )


def get_month_completion_status(year: int, month: int) -> dict[str, dict]:
    """Get completion status for all days in a month.

    Wraps database raw data into CompletionStatus enums.
    """
    _STATUS_MAP = {'gold': CompletionStatus.GOLD, 'silver': CompletionStatus.SILVER}
    raw = database.get_month_completion_raw(year, month)
    return {
        date_str: {
            size: _STATUS_MAP.get(status)
            for size, status in sizes.items()
        }
        for date_str, sizes in raw.items()
    }


def get_streak_info() -> StreakInfo:
    """Calculate the current streak with protection points."""
    played_dates = database.get_played_dates()
    return compute_streak(played_dates, date.today())


def get_current_streak() -> int:
    """Return the current streak length."""
    return get_streak_info().streak


def get_month_crown(
    month_status: dict[str, dict], year: int, month: int, last_day: int,
) -> CompletionStatus | None:
    """Return CompletionStatus.GOLD, SILVER, or None for the month crown.

    Gold: every day has all-gold crowns.
    Silver: every day is completed (mix of gold/silver).
    None: has incomplete days.
    """
    all_gold = True
    for day in range(1, last_day + 1):
        date_str = f'{year:04d}-{month:02d}-{day:02d}'
        day_status = month_status.get(date_str, {})
        if not day_status or not all(v in (CompletionStatus.GOLD, CompletionStatus.SILVER) for v in day_status.values()):
            return None
        if not all(v == CompletionStatus.GOLD for v in day_status.values()):
            all_gold = False
    return CompletionStatus.GOLD if all_gold else CompletionStatus.SILVER


def format_streak_text(streak: int, protections_available: int) -> str:
    """Format streak display text."""
    if streak <= 0:
        return 'Start a streak by playing today!'
    text = f'Current streak: {streak} day{"s" if streak != 1 else ""}'
    # Only reveal protection info once streak reaches 10 (easter egg)
    if streak >= 10 and protections_available > 0:
        text += f'  |  {protections_available} protection{"s" if protections_available > 1 else ""}'
    return text
