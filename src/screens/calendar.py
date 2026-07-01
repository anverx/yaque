"""yaque calendar — supplies a CalendarConfig to the shared kivyshell CalendarScreen.

The month grid, navigation, streak and swipe live in the shell; yaque provides the
CalendarState data source, the DayCell factory (3 queen status icons), the date-tap
action (size popup -> start daily), and the month-crown color mapping.
"""

from __future__ import annotations

from datetime import date

from calendar_logic import CalendarState, CompletionStatus
from popups import show_date_puzzles_popup
from ui_constants import QUEEN_GOLD, QUEEN_SILVER, STYLES
from widgets.layouts import DayCell
from kivyshell.shell.screens.calendar import CalendarConfig
from kivyshell.shell.screens.calendar import CalendarScreen as _CalendarScreen


class CalendarScreen(_CalendarScreen):
    def calendar_config(self) -> CalendarConfig:
        return CalendarConfig(
            new_state=CalendarState,
            make_cell=lambda day, status: DayCell(day=day, completion_status=status, **STYLES["cell"]),
            on_day=self._select_date,
            month_badge_color=self._month_badge_color,
        )

    def _select_date(self, selected_date: date) -> None:
        show_date_puzzles_popup(
            selected_date,
            lambda size: self.app.start_daily_game(size, selected_date, from_calendar=True),
        )

    @staticmethod
    def _month_badge_color(crown: object) -> tuple | None:
        if crown == CompletionStatus.GOLD:
            return QUEEN_GOLD
        if crown == CompletionStatus.SILVER:
            return QUEEN_SILVER
        return None
