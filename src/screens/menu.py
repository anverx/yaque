"""yaque main menu — supplies a MenuConfig to the shared kivyshell MenuScreen.

The menu structure (daily row, Calendar+streak, actions, Exit) lives in the
shell; yaque provides the variants, callbacks, streak text and completion state.
"""

from __future__ import annotations

from datetime import date

import calendar_logic
import database
from kivyshell.shell.adapter import Variant
from kivyshell.shell.screens.menu import MenuConfig, MenuScreen


class MainMenuScreen(MenuScreen):
    def menu_config(self) -> MenuConfig:
        return MenuConfig(
            daily_title="Today's Puzzles",
            daily_variants=[Variant("6", "6x6"), Variant("7", "7x7"), Variant("8", "8x8")],
            on_daily=lambda v: self.app.start_daily_game(int(v.id)),
            calendar_label="Calendar",
            on_calendar=self.app.show_calendar,
            streak_text=self._streak_text,
            actions=[
                ("Random Game", self.app.start_random_game),
                ("Load Shared Puzzle", self.app.show_load_popup),
                ("Logbook", self.app.show_logbook),
                ("About", self.app.show_about),
            ],
            exit_label="Exit",
            on_exit=self.app.exit_app,
            daily_completion=self._daily_completion,
        )

    def _streak_text(self) -> str:
        streak = calendar_logic.get_current_streak()
        if streak > 0:
            return f"Streak: {streak} day{'s' if streak != 1 else ''}"
        return "Start a streak!"

    def _daily_completion(self) -> dict[str, bool]:
        status = database.get_daily_completion_status(date.today().isoformat())
        return {str(size): bool(status.get(size)) for size in (6, 7, 8)}
