"""Layout widgets for Yaque."""

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
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget

from ui_constants import (
    DEFAULT_BUTTON_COLOR,
    DEFAULT_BUTTON_COLOR_DOWN,
    PADDING_CELL,
    PANEL_BACKGROUND,
    POPUP_BACKGROUND,
    POPUP_WIDTH,
    QUEEN_GOLD,
    QUEEN_GRAY,
    QUEEN_SILVER,
    RADIUS_SM,
    ROW_BACKGROUND,
    ROW_PRESSED,
    SPACING_MIN,
    STAT_ROW_HEIGHT,
    STYLES,
    TEXT_LIGHT,
    TEXT_MEDIUM,
    TEXT_WHITE,
)
from widgets.labels import (
    CaptionLabel,
    DayLabel,
    RatingLabel,
    TableCellLabel,
    styled,
)

# Path to icons directory
ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')


# -----------------------------------------------------------------------------
# Layout Factories
# -----------------------------------------------------------------------------

def PopupContent(**kwargs: Any) -> BoxLayout:
    """Vertical BoxLayout with popup padding/spacing defaults."""
    return styled(BoxLayout, 'popup_content', **kwargs)


def styled_layout(style: str = 'button_row', **overrides: Any) -> BoxLayout:
    """Create a BoxLayout with the specified style.

    Styles are defined in ui_constants.STYLES.
    """
    return styled(BoxLayout, style, **overrides)


def ButtonRow(**kwargs: Any) -> BoxLayout:
    """Horizontal BoxLayout for button rows with standard height/spacing."""
    return styled_layout('button_row', **kwargs)


def SizeButtonRow(**kwargs: Any) -> BoxLayout:
    """Horizontal BoxLayout for size selection buttons."""
    return styled_layout('button_row', **kwargs)


class PanelLayout(BoxLayout):
    """BoxLayout with a dark rounded background panel."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._update_panel_bg()
        self.bind(pos=self._update_panel_bg, size=self._update_panel_bg)

    def _update_panel_bg(self, *args: Any) -> None:
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*PANEL_BACKGROUND)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(RADIUS_SM)])


class DateSeparator(BoxLayout):
    """A date separator row."""

    def __init__(self, date_str: str, **kwargs: Any) -> None:
        style_props = STYLES.get('date_separator', {})
        for key in ('size_hint_y', 'height', 'padding'):
            if key in style_props:
                kwargs.setdefault(key, style_props[key])
        super().__init__(**kwargs)
        self.add_widget(CaptionLabel(date_str, color=TEXT_WHITE, halign='left', valign='middle'))


class StatRow(BoxLayout):
    """A row with light rounded background for stats display."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(STAT_ROW_HEIGHT))
        super().__init__(**kwargs)
        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args: Any) -> None:
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*ROW_BACKGROUND)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(RADIUS_SM)])


class DayCell(ButtonBehavior, BoxLayout):
    """Calendar day cell with day number and 3 queen status icons."""

    def __init__(self, day: int, completion_status: dict[int, str | None] | None = None, **kwargs: Any) -> None:
        super().__init__(orientation='vertical', **kwargs)
        self.day = day
        self.background_color = DEFAULT_BUTTON_COLOR
        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)

        # Day number
        self.day_label = DayLabel(str(day), color=TEXT_WHITE, size_hint_y=0.5)
        self.add_widget(self.day_label)

        # Queen icons row
        icons_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.5,
            spacing=dp(SPACING_MIN),
            padding=[dp(PADDING_CELL[0]), 0, dp(PADDING_CELL[0]), dp(PADDING_CELL[1])]
        )

        self.queen_icons: list[Image] = []
        for size in [6, 7, 8]:
            status = completion_status.get(size) if completion_status else None
            if status == 'gold':
                color = QUEEN_GOLD
            elif status == 'silver':
                color = QUEEN_SILVER
            else:
                color = QUEEN_GRAY
            icon = Image(
                source=os.path.join(ICONS_DIR, 'queen-small.png'),
                color=color,
                fit_mode='contain'
            )
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

        # Parse data
        started_at = play_data['started_at']
        duration_ms = play_data['duration_ms']
        completed = play_data['completed']
        daily_date = play_data['daily_date']
        completed_at = play_data['completed_at']
        size = play_data['size']
        fun_rating = play_data.get('fun_rating')

        # Format time only (date shown in separator)
        try:
            dt = datetime.fromisoformat(started_at)
            time_str = dt.strftime('%H:%M')
        except (ValueError, TypeError):
            time_str = '?'

        # Format duration
        if duration_ms:
            secs = duration_ms // 1000
            mins = secs // 60
            secs = secs % 60
            duration_str = f'{mins}:{secs:02d}'
        else:
            duration_str = '-'

        # Format rating
        rating_str = '[font=Stars]' + '★' * fun_rating + '[/font]' if fun_rating else '-'

        # Determine crown color
        crown_color = QUEEN_GRAY  # Gray/faded for random or incomplete
        if completed and daily_date:
            if completed_at:
                completed_date = completed_at[:10]
                if completed_date == daily_date:
                    crown_color = QUEEN_GOLD
                else:
                    crown_color = QUEEN_SILVER
            else:
                crown_color = QUEEN_SILVER  # Old data without completed_at

        # Type icon (calendar for daily, dice for random)
        self.add_widget(TypeIcon(daily_date, size_hint_y=0.7))

        # Size column
        self.add_widget(TableCellLabel(f'{size}x{size}', color=TEXT_LIGHT))

        # Duration column
        self.add_widget(TableCellLabel(duration_str))

        # Rating column
        self.add_widget(RatingLabel(rating_str))

        # Time column
        self.add_widget(TableCellLabel(time_str))

        # Crown icon
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


# -----------------------------------------------------------------------------
# Icon Factories
# -----------------------------------------------------------------------------

def TypeIcon(daily_date: str | None, **kwargs: Any) -> Image:
    """Calendar/dice icon indicating daily vs random puzzle."""
    icon_name = 'calendar' if daily_date else 'dice'
    kwargs.setdefault('color', TEXT_MEDIUM)
    kwargs.setdefault('fit_mode', 'contain')
    return Image(source=os.path.join(ICONS_DIR, f'{icon_name}.png'), **kwargs)


def CrownIcon(color: tuple[float, ...], **kwargs: Any) -> Image:
    """Small queen/crown status icon."""
    kwargs.setdefault('fit_mode', 'contain')
    return Image(source=os.path.join(ICONS_DIR, 'queen-small.png'), color=color, **kwargs)


def Popup(content: Widget, height: float, width_hint: float = POPUP_WIDTH, auto_dismiss: bool = True) -> ModalView:
    """Create a styled ModalView popup.

    Args:
        content: Widget to add as popup content
        height: Popup height in dp units (raw number)
        width_hint: size_hint_x value (default POPUP_WIDTH)
        auto_dismiss: Whether tapping outside closes popup
    """
    popup = ModalView(
        size_hint=(width_hint, None),
        height=dp(height),
        auto_dismiss=auto_dismiss,
        background_color=POPUP_BACKGROUND
    )
    popup.add_widget(content)
    return popup
