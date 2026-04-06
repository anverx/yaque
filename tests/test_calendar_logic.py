"""Tests for calendar logic: month crowns, streak text, navigation, last day."""

import os
import sys
import unittest
from datetime import date
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from calendar_logic import (
    CalendarState,
    CompletionStatus,
    _last_day_of_month,
    format_streak_text,
    get_month_crown,
)

G = CompletionStatus.GOLD
S = CompletionStatus.SILVER

# Fixed reference date for navigation tests
FIXED_TODAY = date(2026, 6, 15)


def _full_month(year: int, month: int, last_day: int,
                status: CompletionStatus) -> dict:
    """Build month_status with every day having all sizes set to given status."""
    return {
        f'{year:04d}-{month:02d}-{day:02d}': {6: status, 7: status, 8: status}
        for day in range(1, last_day + 1)
    }


class TestLastDayOfMonth(unittest.TestCase):
    """Test last day of month computation."""

    def test_standard_months(self):
        """Standard months should have correct day counts."""
        cases = [
            (1, 31), (3, 31), (4, 30), (5, 31), (6, 30),
            (7, 31), (8, 31), (9, 30), (10, 31), (11, 30), (12, 31),
        ]
        for month, expected in cases:
            with self.subTest(month=month):
                self.assertEqual(_last_day_of_month(2026, month), expected,
                                 f'month {month} should have {expected} days')

    def test_february_non_leap(self):
        """February in a non-leap year should have 28 days."""
        self.assertEqual(_last_day_of_month(2025, 2), 28, 'non-leap Feb')

    def test_february_leap(self):
        """February in a leap year should have 29 days."""
        self.assertEqual(_last_day_of_month(2024, 2), 29, 'leap Feb')


class TestGetMonthCrown(unittest.TestCase):
    """Test month crown determination logic."""

    def test_all_gold(self):
        """Every day all-gold should return GOLD."""
        ms = _full_month(2026, 1, 31, G)
        self.assertEqual(get_month_crown(ms, 2026, 1, 31), G, 'all gold month')

    def test_all_silver(self):
        """Every day all-silver should return SILVER."""
        ms = _full_month(2026, 1, 31, S)
        self.assertEqual(get_month_crown(ms, 2026, 1, 31), S, 'all silver month')

    def test_mixed_gold_silver(self):
        """Mix of gold and silver days should return SILVER."""
        ms = _full_month(2026, 1, 31, G)
        ms['2026-01-15'] = {6: S, 7: G, 8: G}
        self.assertEqual(get_month_crown(ms, 2026, 1, 31), S, 'mixed should be silver')

    def test_one_size_silver_rest_gold(self):
        """A single silver size on one day should make the whole month SILVER."""
        ms = _full_month(2026, 3, 31, G)
        ms['2026-03-01'] = {6: G, 7: S, 8: G}
        self.assertEqual(get_month_crown(ms, 2026, 3, 31), S,
                         'one silver size downgrades to silver')

    def test_incomplete_day_returns_none(self):
        """A day with a None status should return None."""
        ms = _full_month(2026, 1, 31, G)
        ms['2026-01-10'] = {6: G, 7: None, 8: G}
        self.assertIsNone(get_month_crown(ms, 2026, 1, 31), 'incomplete day')

    def test_missing_day_returns_none(self):
        """A missing day in the month should return None."""
        ms = _full_month(2026, 1, 31, G)
        del ms['2026-01-20']
        self.assertIsNone(get_month_crown(ms, 2026, 1, 31), 'missing day')

    def test_empty_month_returns_none(self):
        """No data at all should return None."""
        self.assertIsNone(get_month_crown({}, 2026, 1, 31), 'empty month')

    def test_single_day_month(self):
        """A one-day month with all gold should return GOLD."""
        ms = {'2026-02-01': {6: G, 7: G, 8: G}}
        self.assertEqual(get_month_crown(ms, 2026, 2, 1), G, 'single day gold')

    def test_february_leap_year(self):
        """A full leap February (29 days) all gold should return GOLD."""
        ms = _full_month(2024, 2, 29, G)
        self.assertEqual(get_month_crown(ms, 2024, 2, 29), G, 'leap Feb all gold')

    def test_february_leap_year_missing_29th(self):
        """Leap February missing the 29th should return None."""
        ms = _full_month(2024, 2, 29, G)
        del ms['2024-02-29']
        self.assertIsNone(get_month_crown(ms, 2024, 2, 29), 'missing 29th')


class TestFormatStreakText(unittest.TestCase):
    """Test streak display text formatting."""

    def test_zero_streak(self):
        """Zero streak should show encouragement message."""
        self.assertEqual(format_streak_text(0, 0),
                         'Start a streak by playing today!', 'zero streak')

    def test_negative_streak(self):
        """Negative streak should show encouragement message."""
        self.assertEqual(format_streak_text(-1, 0),
                         'Start a streak by playing today!', 'negative streak')

    def test_single_day(self):
        """Streak of 1 should use singular 'day'."""
        self.assertEqual(format_streak_text(1, 0),
                         'Current streak: 1 day', 'singular day')

    def test_plural_days(self):
        """Streak > 1 should use plural 'days'."""
        self.assertEqual(format_streak_text(5, 0),
                         'Current streak: 5 days', 'plural days')

    def test_protection_hidden_under_10(self):
        """Protection info should not show when streak < 10."""
        result = format_streak_text(9, 2)
        self.assertNotIn('protection', result, 'should hide protection under 10')

    def test_protection_hidden_when_zero(self):
        """Protection info should not show when protections = 0."""
        result = format_streak_text(10, 0)
        self.assertNotIn('protection', result, 'should hide zero protections')

    def test_protection_singular_at_10(self):
        """One protection at streak 10 should show singular."""
        result = format_streak_text(10, 1)
        self.assertIn('10 days', result, 'should show 10 days')
        self.assertIn('1 protection', result, 'should show singular protection')
        self.assertNotIn('protections', result, 'should not pluralize')

    def test_protection_plural(self):
        """Multiple protections should use plural."""
        result = format_streak_text(30, 2)
        self.assertIn('2 protections', result, 'should pluralize protections')


class TestCalendarStateNavigation(unittest.TestCase):
    """Test CalendarState year/month tracking and navigation."""

    def _make_state(self, today=FIXED_TODAY):
        """Helper to create a CalendarState with a fixed today."""
        with patch('calendar_logic.date') as mock_date:
            mock_date.today.return_value = today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            return CalendarState()

    def test_initial_state(self):
        """Should initialize to current year and month."""
        st = self._make_state()
        self.assertEqual(st.year, 2026, 'initial year')
        self.assertEqual(st.month, 6, 'initial month')

    def test_prev_month(self):
        """Should decrement month."""
        st = self._make_state()
        st.prev_month()
        self.assertEqual((st.year, st.month), (2026, 5), 'prev from June')

    def test_prev_month_wraps_year(self):
        """January should wrap to December of previous year."""
        st = self._make_state()
        st.year, st.month = 2026, 1
        st.prev_month()
        self.assertEqual((st.year, st.month), (2025, 12), 'Jan wraps to Dec')

    @patch('calendar_logic.date')
    def test_next_month(self, mock_date):
        """Should increment month when not at current."""
        mock_date.today.return_value = FIXED_TODAY
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        st = CalendarState()
        st.year, st.month = 2026, 3
        self.assertTrue(st.next_month(), 'should advance')
        self.assertEqual((st.year, st.month), (2026, 4), 'next from March')

    @patch('calendar_logic.date')
    def test_next_month_blocked_at_current(self, mock_date):
        """Should return False and not advance when at current month."""
        mock_date.today.return_value = FIXED_TODAY
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        st = CalendarState()
        self.assertFalse(st.next_month(), 'should block at current')
        self.assertEqual((st.year, st.month), (2026, 6), 'should stay at June')

    @patch('calendar_logic.date')
    def test_next_month_wraps_year(self, mock_date):
        """December should wrap to January of next year."""
        mock_date.today.return_value = date(2027, 2, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        st = CalendarState()
        st.year, st.month = 2026, 12
        self.assertTrue(st.next_month(), 'should advance')
        self.assertEqual((st.year, st.month), (2027, 1), 'Dec wraps to Jan')

    @patch('calendar_logic.date')
    def test_is_past_month_true(self, mock_date):
        """Months before current should be past."""
        mock_date.today.return_value = FIXED_TODAY
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        st = CalendarState()
        st.year, st.month = 2026, 3
        self.assertTrue(st.is_past_month(), 'March should be past in June')

    @patch('calendar_logic.date')
    def test_is_past_month_false_current(self, mock_date):
        """Current month should not be past."""
        mock_date.today.return_value = FIXED_TODAY
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        st = CalendarState()
        self.assertFalse(st.is_past_month(), 'current month is not past')

    @patch('calendar_logic.date')
    def test_is_past_month_previous_year(self, mock_date):
        """Any month in a previous year should be past."""
        mock_date.today.return_value = FIXED_TODAY
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        st = CalendarState()
        st.year, st.month = 2025, 12
        self.assertTrue(st.is_past_month(), 'previous year is past')

    def test_multiple_prev_navigations(self):
        """Multiple prev_month calls should work correctly."""
        st = self._make_state()
        for _ in range(8):
            st.prev_month()
        self.assertEqual((st.year, st.month), (2025, 10),
                         '8 months back from June 2026')


if __name__ == "__main__":
    unittest.main()
