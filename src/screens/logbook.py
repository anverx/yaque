from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import database
from game import Game
from screens.base import BackgroundedScreen
from ui_constants import (
    BUTTON_HEIGHT_SM,
    PADDING_CELL,
    QUEEN_GOLD,
    QUEEN_GRAY,
    QUEEN_SILVER,
    RADIUS_SM,
    ROW_BACKGROUND,
    ROW_HEIGHT,
    ROW_PRESSED,
    STYLES,
    TEXT_LIGHT,
    TEXT_WHITE,
    TOP_SPACER_HEIGHT,
)
from widgets import (
    CaptionLabel,
    CrownIcon,
    FixedGrayRoundedButton,
    GrayRoundedButton,
    PanelLayout,
    RatingLabel,
    RoundedButton,
    SelectableButton,
    SelectableButtonGroup,
    SubtitleLabel,
    TableCellLabel,
    TableHeaderLabel,
    TitleLgLabel,
    TypeIcon,
    styled,
)

PAGE_SIZE = 20


class LogbookRow(ButtonBehavior, BoxLayout):
    """A tappable row in the logbook."""

    def __init__(self, play_data: dict[str, Any], on_select: Callable[[dict[str, Any]], None], **kwargs: Any) -> None:
        # Apply pre-converted style properties (already in dp units)
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


class DateSeparator(BoxLayout):
    """A date separator row."""

    def __init__(self, date_str: str, **kwargs: Any) -> None:
        # Apply pre-converted style properties (already in dp units)
        style_props = STYLES.get('date_separator', {})
        for key in ('size_hint_y', 'height', 'padding'):
            if key in style_props:
                kwargs.setdefault(key, style_props[key])
        super().__init__(**kwargs)
        self.add_widget(CaptionLabel(date_str, color=TEXT_WHITE, halign='left', valign='middle'))


class LogbookScreen(BackgroundedScreen):
    def build_content(self) -> None:
        self.current_offset = 0
        self.has_more = False
        self.current_sort = 'time'
        layout = self.content_layout

        # Extra spacer to push content below the banner
        layout.add_widget(BoxLayout(size_hint_y=None, height=dp(TOP_SPACER_HEIGHT)))

        # Title
        layout.add_widget(TitleLgLabel('Logbook'))

        # Sort selector row
        sort_row = styled(BoxLayout, 'selection_row')

        sort_label = CaptionLabel('Sort:', size_hint_x=None, width=dp(40))
        sort_row.add_widget(sort_label)

        self.sort_group = SelectableButtonGroup(on_select=self._on_sort_changed)

        for sort_key, label in [('time', 'When'), ('size', 'Size'), ('duration', 'Time'), ('rating', 'Rating')]:
            btn = SelectableButton(
                text=label,
                selected=(sort_key == 'time'),
                **STYLES['selection_btn']
            )
            self.sort_group.add(sort_key, btn)
            sort_row.add_widget(btn)

        # Spacer to push buttons left
        sort_row.add_widget(Label(size_hint_x=1))
        layout.add_widget(sort_row)

        # Panel with dark background
        self.logbook_panel = PanelLayout(
            orientation='vertical',
            padding=[dp(PADDING_CELL[0]), dp(PADDING_CELL[1])],
        )

        # Header row
        header = styled(BoxLayout, 'table_header_row')
        header.add_widget(TableHeaderLabel('Type'))
        header.add_widget(TableHeaderLabel('Size'))
        header.add_widget(TableHeaderLabel('Time'))
        header.add_widget(TableHeaderLabel('Rating'))
        header.add_widget(TableHeaderLabel('When'))
        header.add_widget(TableHeaderLabel('Daily'))
        self.logbook_panel.add_widget(header)

        # Scrollable list
        scroll = ScrollView(size_hint=(1, 1))
        self.list_layout = styled(BoxLayout, 'list_layout')
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        scroll.add_widget(self.list_layout)
        self.logbook_panel.add_widget(scroll)

        layout.add_widget(self.logbook_panel)

        # Back button
        self.add_back_button()

    def _format_date(self, date_str: str) -> str:
        """Format date string for separator."""
        try:
            dt = datetime.fromisoformat(date_str)
            today = datetime.now().date()
            if dt.date() == today:
                return 'Today'
            elif (today - dt.date()).days == 1:
                return 'Yesterday'
            else:
                return dt.strftime('%A, %b %d')
        except Exception:
            return date_str[:10] if date_str else '?'

    def _get_date_key(self, started_at: str) -> str:
        """Extract date part from started_at timestamp."""
        return started_at[:10] if started_at else ''

    def _on_game_selected(self, play_data: dict[str, Any]) -> None:
        """Load and show the selected game."""
        code = play_data['code']
        daily_date = play_data['daily_date']

        try:
            game = Game.from_code(code)

            # Parse daily_date if present
            from datetime import date
            parsed_date = None
            if daily_date:
                try:
                    parts = daily_date.split('-')
                    parsed_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
                except Exception:
                    pass

            self.app._on_game_ready(game, daily_date=parsed_date, from_logbook=True)
        except Exception as e:
            print(f"Error loading game: {e}")

    def _load_more(self, instance: Any) -> None:
        """Load next page of games."""
        self._load_plays(append=True)

    def _load_plays(self, append: bool = False) -> None:
        """Load plays from database."""
        if not append:
            self.list_layout.clear_widgets()
            self.current_offset = 0

        plays = database.get_all_plays(limit=PAGE_SIZE, offset=self.current_offset, sort_by=self.current_sort)
        total = database.get_plays_count(sort_by=self.current_sort)

        if not plays and not append:
            self.list_layout.add_widget(SubtitleLabel(
                'No games played yet',
                size_hint_y=None,
                height=dp(ROW_HEIGHT)
            ))
            return

        # Remove old "Load More" button if appending
        if append and self.list_layout.children:
            last = self.list_layout.children[0]  # Children are in reverse order
            if isinstance(last, (RoundedButton, GrayRoundedButton)):
                self.list_layout.remove_widget(last)

        # Get last date shown (if appending)
        last_date = None
        if append and self.list_layout.children:
            for child in reversed(self.list_layout.children):
                if isinstance(child, LogbookRow):
                    last_date = self._get_date_key(child.play_data['started_at'])
                    break

        # Add plays with date separators
        current_date = last_date
        for play in plays:
            play_date = self._get_date_key(play['started_at'])

            # Add date separator if date changed
            if play_date != current_date:
                current_date = play_date
                separator = DateSeparator(self._format_date(play['started_at']))
                self.list_layout.add_widget(separator)

            row = LogbookRow(play, self._on_game_selected)
            self.list_layout.add_widget(row)

        self.current_offset += len(plays)
        self.has_more = self.current_offset < total

        # Add "Load More" button if there's more
        if self.has_more:
            remaining = total - self.current_offset
            load_more_btn = FixedGrayRoundedButton(
                text=f'Load More ({remaining} remaining)',
                height=dp(BUTTON_HEIGHT_SM)
            )
            load_more_btn.bind(on_press=self._load_more)
            self.list_layout.add_widget(load_more_btn)

    def _on_sort_changed(self, sort_key: str) -> None:
        """Handle sort option change."""
        self.current_sort = sort_key
        self._load_plays(append=False)

    def on_enter(self) -> None:
        """Refresh list when screen is shown."""
        self._load_plays(append=False)
