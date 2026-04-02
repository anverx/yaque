from __future__ import annotations

import calendar
import os
from datetime import date
from typing import Any

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, PopMatrix, PushMatrix, Rectangle, Rotate
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

import database
from popups import show_date_puzzles_popup
from screens.base import BackgroundedScreen
from ui_constants import (
    PADDING_CELL,
    QUEEN_GOLD,
    SPACING_MIN,
    STREAK_PROTECTED,
    STYLES,
    SWIPE_DISTANCE_THRESHOLD,
    TODAY_HIGHLIGHT,
    TOP_SPACER_HEIGHT,
)
from widgets import (
    DayCell,
    DayLabel,
    MonthLabel,
    PanelLayout,
    RoundedButton,
    TitleSmLabel,
    disable_widget,
    styled,
)


class CalendarScreen(BackgroundedScreen):
    def build_content(self) -> None:
        self.current_year = date.today().year
        self.current_month = date.today().month
        layout = self.content_layout

        # Extra spacer to push calendar below the banner
        layout.add_widget(BoxLayout(size_hint_y=None, height=dp(TOP_SPACER_HEIGHT)))

        # Header with month/year and navigation
        header = styled(BoxLayout, 'header_bar')

        prev_btn = RoundedButton(text='<', **STYLES['nav_btn'])
        prev_btn.bind(on_press=self.prev_month)
        header.add_widget(prev_btn)

        self.month_label = MonthLabel('')
        header.add_widget(self.month_label)

        next_btn = RoundedButton(text='>', **STYLES['nav_btn'])
        next_btn.bind(on_press=self.next_month)
        header.add_widget(next_btn)

        layout.add_widget(header)

        # Calendar panel with rounded background
        panel_pad_v = dp(PADDING_CELL[1] * 2)
        self.calendar_panel = PanelLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=[dp(PADDING_CELL[0] * 2), panel_pad_v],
            spacing=dp(SPACING_MIN),
        )

        # Day labels
        days_header = styled(GridLayout, 'days_header')
        for day_name in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']:
            days_header.add_widget(DayLabel(day_name))
        self.calendar_panel.add_widget(days_header)

        # Calendar grid
        self.calendar_grid = styled(GridLayout, 'calendar_grid')
        self.calendar_grid.bind(minimum_height=self.calendar_grid.setter('height'))
        self.calendar_panel.add_widget(self.calendar_grid)

        # Panel height = days_header + calendar_grid + padding + spacing
        def update_panel_height(*args: Any) -> None:
            self.calendar_panel.height = (
                days_header.height + self.calendar_grid.height
                + panel_pad_v * 2 + dp(SPACING_MIN)
            )
        self.calendar_grid.bind(height=update_panel_height)
        days_header.bind(height=update_panel_height)

        layout.add_widget(self.calendar_panel)

        # Streak display
        self.streak_label = TitleSmLabel('')
        layout.add_widget(self.streak_label)

        # Spacer
        layout.add_widget(BoxLayout())

        # Back button
        self.add_back_button()

        self.refresh_calendar()

    def prev_month(self, instance: Any) -> None:
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.refresh_calendar()

    def next_month(self, instance: Any) -> None:
        today = date.today()
        # Don't allow going past current month
        if self.current_year == today.year and self.current_month >= today.month:
            return
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.refresh_calendar()

    _crown_texture: Any = None

    def _draw_month_crown(self) -> None:
        """Draw a tilted gold crown on the month label."""
        if CalendarScreen._crown_texture is None:
            icons_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')
            CalendarScreen._crown_texture = CoreImage(
                os.path.join(icons_dir, 'queen-small.png')
            ).texture
        lbl = self.month_label
        icon_size = lbl.height * 0.45
        ix = lbl.right - icon_size - dp(4)
        iy = lbl.top - icon_size - dp(2)
        with lbl.canvas.after:
            Color(*QUEEN_GOLD)
            PushMatrix()
            Rotate(angle=-20, origin=(ix + icon_size / 2, iy + icon_size / 2))
            Rectangle(
                texture=CalendarScreen._crown_texture,
                pos=(ix, iy),
                size=(icon_size, icon_size),
            )
            PopMatrix()

    def _is_month_perfect(self, month_status: dict[str, dict], year: int, month: int) -> bool:
        """Check if every day in the month (up to today) has at least one win."""
        today = date.today()
        if year > today.year or (year == today.year and month > today.month):
            return False
        import calendar as cal_mod
        last_day = cal_mod.monthrange(year, month)[1]
        # For current month, only check up to today
        if year == today.year and month == today.month:
            last_day = today.day
        for day in range(1, last_day + 1):
            date_str = f'{year:04d}-{month:02d}-{day:02d}'
            day_status = month_status.get(date_str, {})
            if not any(v is not None for v in day_status.values()):
                return False
        return True

    def refresh_calendar(self) -> None:
        self.month_label.text = f'{calendar.month_name[self.current_month]} {self.current_year}'
        self.month_label.canvas.after.clear()
        self.calendar_grid.clear_widgets()

        # Update streak display with protection info
        info = database.get_streak_info()
        if info.streak > 0:
            streak_text = f'Current streak: {info.streak} day{"s" if info.streak != 1 else ""}'
            # Only reveal protection info once streak reaches 10 (easter egg)
            if info.streak >= 10 and info.protections_available > 0:
                shield = info.protections_available
                streak_text += f'  |  {shield} protection{"s" if shield > 1 else ""}'
            self.streak_label.text = streak_text
        else:
            self.streak_label.text = 'Start a streak by playing today!'

        protected_set = set(info.protected_dates)
        today = date.today()
        cal = calendar.Calendar(firstweekday=0)  # Monday first

        # Fetch completion status for entire month in one query
        month_status = database.get_month_completion_status(self.current_year, self.current_month)

        # Show crown if every day of the month has at least one win
        if self._is_month_perfect(month_status, self.current_year, self.current_month):
            self._draw_month_crown()

        for day in cal.itermonthdays(self.current_year, self.current_month):
            if day == 0:
                # Empty cell
                self.calendar_grid.add_widget(styled(Label, 'cell', text=''))
            else:
                day_date = date(self.current_year, self.current_month, day)
                date_str = day_date.isoformat()
                completion_status = month_status.get(date_str, {6: None, 7: None, 8: None})

                cell = DayCell(
                    day=day,
                    completion_status=completion_status,
                    **STYLES['cell']
                )

                # Disable future dates
                if day_date > today:
                    disable_widget(cell)
                else:
                    cell.bind(on_press=lambda x, d=day_date: self.select_date(d))
                    if day_date == today:
                        cell.background_color = TODAY_HIGHLIGHT
                    elif date_str in protected_set:
                        cell.background_color = STREAK_PROTECTED

                self.calendar_grid.add_widget(cell)

    def select_date(self, selected_date: date) -> None:
        def on_size_selected(size: int) -> None:
            self.app.start_daily_game(size, selected_date, from_calendar=True)
        show_date_puzzles_popup(selected_date, on_size_selected)

    def on_enter(self) -> None:
        """Refresh calendar when screen is shown to reflect completion changes."""
        self.refresh_calendar()

    # Swipe gestures for month navigation
    def on_touch_down(self, touch: Any) -> bool:
        touch.ud['start_x'] = touch.x
        touch.ud['start_y'] = touch.y
        return super().on_touch_down(touch)

    def on_touch_up(self, touch: Any) -> bool:
        start_x = touch.ud.get('start_x', touch.x)
        start_y = touch.ud.get('start_y', touch.y)
        dx = touch.x - start_x
        dy = abs(touch.y - start_y)

        # Only trigger if horizontal swipe (dx > dy) and sufficient distance
        if abs(dx) > dp(SWIPE_DISTANCE_THRESHOLD) and abs(dx) > dy:
            if dx < 0:
                # Swipe left → next month
                self.next_month(None)
                return True
            else:
                # Swipe right → previous month
                self.prev_month(None)
                return True
        return super().on_touch_up(touch)
