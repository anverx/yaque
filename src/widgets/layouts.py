"""Shim + game-specific layout components.

The pure layout primitives (PanelLayout, StatRow, DateSeparator, ButtonRow,
SizeButtonRow, PopupContent, Popup, TypeIcon, CrownIcon, styled_layout) now live
in ``kivyshell.uikit.layouts`` and are re-exported here.

DayCell and LogbookRow stay in yaque for now: they encode yaque's completion
model (calendar_logic.CompletionStatus, board sizes 6/7/8) and play-record schema.
They move to the kivyshell L2 shell screens in a later phase.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image

from calendar_logic import CompletionStatus
from ui_constants import (
    DEFAULT_BUTTON_COLOR,
    DEFAULT_BUTTON_COLOR_DOWN,
    PADDING_CELL,
    QUEEN_GOLD,
    QUEEN_GRAY,
    QUEEN_SILVER,
    RADIUS_SM,
    ROW_BACKGROUND,
    ROW_PRESSED,
    SPACING_MIN,
    STYLES,
    TEXT_LIGHT,
    TEXT_WHITE,
)
from kivyshell.uikit import DayLabel, RatingLabel, TableCellLabel

# Pure primitives (incl. TypeIcon, CrownIcon) come from the shared library.
from kivyshell.uikit.layouts import *  # noqa: F401,F403
from kivyshell.uikit.layouts import CrownIcon, TypeIcon  # used by LogbookRow below

ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')


class DayCell(ButtonBehavior, BoxLayout):
    """Calendar day cell with day number and 3 queen status icons."""

    def __init__(self, day: int, completion_status: dict[int, str | None] | None = None, **kwargs: Any) -> None:
        super().__init__(orientation='vertical', **kwargs)
        self.day = day
        self.background_color = DEFAULT_BUTTON_COLOR
        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)

        self.day_label = DayLabel(str(day), color=TEXT_WHITE, size_hint_y=0.5)
        self.add_widget(self.day_label)

        icons_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.5,
            spacing=dp(SPACING_MIN),
            padding=[dp(PADDING_CELL[0]), 0, dp(PADDING_CELL[0]), dp(PADDING_CELL[1])]
        )

        self.queen_icons: list[Image] = []
        for size in [6, 7, 8]:
            status = completion_status.get(size) if completion_status else None
            if status == CompletionStatus.GOLD:
                color = QUEEN_GOLD
            elif status == CompletionStatus.SILVER:
                color = QUEEN_SILVER
            else:
                color = QUEEN_GRAY
            icon = Image(source=os.path.join(ICONS_DIR, 'queen-small.png'), color=color, fit_mode='contain')
            self.queen_icons.append(icon)
            icons_row.add_widget(icon)

        self.add_widget(icons_row)

    def _update_bg(self, *args: Any) -> None:
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*DEFAULT_BUTTON_COLOR_DOWN)
            else:
                Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(RADIUS_SM)])


class LogbookRow(ButtonBehavior, BoxLayout):
    """A tappable row in the logbook."""

    def __init__(self, play_data: dict[str, Any], on_select: Callable[[dict[str, Any]], None], **kwargs: Any) -> None:
        style_props = STYLES.get('logbook_row', {})
        for key in ('size_hint_y', 'height', 'padding', 'spacing'):
            if key in style_props:
                kwargs.setdefault(key, style_props[key])
        super().__init__(orientation='horizontal', **kwargs)
        self.play_data = play_data
        self.on_select = on_select

        self._bg_color = ROW_BACKGROUND
        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)

        started_at = play_data['started_at']
        duration_ms = play_data['duration_ms']
        completed = play_data['completed']
        daily_date = play_data['daily_date']
        completed_at = play_data['completed_at']
        size = play_data['size']
        fun_rating = play_data.get('fun_rating')

        try:
            dt = datetime.fromisoformat(started_at)
            time_str = dt.strftime('%H:%M')
        except (ValueError, TypeError):
            time_str = '?'

        if duration_ms:
            secs = duration_ms // 1000
            mins = secs // 60
            secs = secs % 60
            duration_str = f'{mins}:{secs:02d}'
        else:
            duration_str = '-'

        rating_str = '[font=Stars]' + '★' * fun_rating + '[/font]' if fun_rating else '-'

        crown_color = QUEEN_GRAY
        if completed and daily_date:
            if completed_at:
                completed_date = completed_at[:10]
                crown_color = QUEEN_GOLD if completed_date == daily_date else QUEEN_SILVER
            else:
                crown_color = QUEEN_SILVER

        self.add_widget(TypeIcon(daily_date, size_hint_y=0.7))
        self.add_widget(TableCellLabel(f'{size}x{size}', color=TEXT_LIGHT))
        self.add_widget(TableCellLabel(duration_str))
        self.add_widget(RatingLabel(rating_str))
        self.add_widget(TableCellLabel(time_str))
        self.add_widget(CrownIcon(crown_color, size_hint_y=0.7))

    def _update_bg(self, *args: Any) -> None:
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*ROW_PRESSED)
            else:
                Color(*self._bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(RADIUS_SM)])

    def on_press(self) -> None:
        if self.on_select:
            self.on_select(self.play_data)
