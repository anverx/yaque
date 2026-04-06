"""Logic and data access for calendar features."""

from __future__ import annotations

from datetime import date
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
        info = database.get_streak_info()
        month_status = database.get_month_completion_status(self.year, self.month)

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
        if not all(v in (CompletionStatus.GOLD, CompletionStatus.SILVER) for v in day_status.values()):
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
