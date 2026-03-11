"""Tests for streak computation with protection points."""

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import compute_streak

# Fixed reference date for all tests
TODAY = date(2026, 3, 12)


def _dates(*specs: str) -> set[str]:
    """Build a set of played date strings from day offsets relative to TODAY.

    Each spec is either:
    - "N" — a single day offset (0=today, 1=yesterday, etc.)
    - "N-M" — a range of offsets (inclusive)
    """
    result = set()
    for spec in specs:
        if '-' in spec:
            parts = spec.split('-')
            lo, hi = int(parts[0]), int(parts[1])
            for i in range(lo, hi + 1):
                result.add((TODAY - timedelta(days=i)).isoformat())
        else:
            result.add((TODAY - timedelta(days=int(spec))).isoformat())
    return result


class TestBasicStreak:
    def test_no_plays(self):
        info = compute_streak(set(), TODAY)
        assert info.streak == 0

    def test_single_day_today(self):
        info = compute_streak(_dates('0'), TODAY)
        assert info.streak == 1
        assert info.protections_available == 0

    def test_consecutive_5_days(self):
        info = compute_streak(_dates('0-4'), TODAY)
        assert info.streak == 5
        assert info.protections_available == 0
        assert info.protections_used == 0

    def test_gap_breaks_streak(self):
        # 3 played, skip, 3 played (today)
        played = _dates('0-2', '4-6')
        info = compute_streak(played, TODAY)
        assert info.streak == 3


class TestGracePeriod:
    def test_played_yesterday_not_today(self):
        played = _dates('1-5')
        info = compute_streak(played, TODAY)
        assert info.streak == 5

    def test_last_play_two_days_ago(self):
        played = _dates('2-6')
        info = compute_streak(played, TODAY)
        assert info.streak == 0


class TestProtection:
    def test_9_consecutive_no_protection(self):
        # 9 played + gap → not protected
        played = _dates('0', '2-10')  # gap at day 1
        info = compute_streak(played, TODAY)
        assert info.streak == 1  # Only today

    def test_10_consecutive_protects_gap(self):
        # 10 played, gap, today
        played = _dates('0', '2-11')  # gap at day 1, 10 days before it
        info = compute_streak(played, TODAY)
        assert info.streak == 12
        assert info.protections_used == 1
        assert info.protections_available == 0

    def test_earn_point_after_gap(self):
        # 10 played, gap, 10 played ending today → banked=1
        played = _dates('0-9', '11-20')  # gap at day 10
        info = compute_streak(played, TODAY)
        assert info.streak == 21
        assert info.protections_used == 1
        assert info.protections_available == 1

    def test_two_gaps_each_protected(self):
        # 10 played, gap, 10 played, gap, 10 played ending today
        played = _dates('0-9', '11-20', '22-31')  # gaps at 10 and 21
        info = compute_streak(played, TODAY)
        assert info.streak == 32
        assert info.protections_used == 2
        assert info.protections_available == 1  # last 10 earns a new point

    def test_30_consecutive_protects_two_close_gaps(self):
        # 30 played, gap, gap, today
        played = _dates('0', '3-32')  # gaps at day 1 and 2
        info = compute_streak(played, TODAY)
        assert info.streak == 33
        assert info.protections_used == 2
        assert info.protections_available == 0

    def test_30_played_gap_5_played_gap(self):
        # 30 played, gap, 5 played, gap, today → both protected
        played = _dates('0', '2-6', '8-37')  # gaps at 1 and 7
        info = compute_streak(played, TODAY)
        assert info.streak == 38
        assert info.protections_used == 2
        assert info.protections_available == 0

    def test_re_earning_3_gaps(self):
        # 10 played, gap, 10 played, gap, 10 played, gap, today
        played = _dates('0', '2-11', '13-22', '24-33')  # gaps at 1, 12, 23
        info = compute_streak(played, TODAY)
        assert info.streak == 34
        assert info.protections_used == 3
        assert info.protections_available == 0

    def test_first_protected_second_breaks(self):
        # 10 played, gap, 9 played, gap → first ok, second breaks
        played = _dates('0-8', '10-19')  # gap at 9 (only 9 before it), gap at... wait
        # Let me redo: today=0, days 0-8 played (9 days), gap at 9, days 10-19 played (10 days)
        # Walking back: hit gap at 9, check 10 before (days 10-19) — all played → protected
        # Then continue through days 10-19, all played. Streak = 20. That's wrong for my test.
        #
        # I want: 10 played, gap, 9 played, gap, today
        # today=0, gap at 1, days 2-10 (9 played), gap at 11, days 12-21 (10 played)
        played = _dates('0', '2-10', '12-21')  # gap at 1, gap at 11
        info = compute_streak(played, TODAY)
        # gap at 1: check 10 before (days 2-11) → day 11 is gap → inner gap
        #   check 30 before day 11 (days 12-41) → only 10 played (12-21) → break!
        assert info.streak == 1  # Only today

    def test_30_consecutive_earns_2_banked(self):
        # 30 consecutive days ending today → 2 banked
        played = _dates('0-29')
        info = compute_streak(played, TODAY)
        assert info.streak == 30
        assert info.protections_available == 2
        assert info.protections_used == 0

    def test_10_consecutive_earns_1_banked(self):
        # 10 consecutive days ending today → 1 banked
        played = _dates('0-9')
        info = compute_streak(played, TODAY)
        assert info.streak == 10
        assert info.protections_available == 1
        assert info.protections_used == 0
