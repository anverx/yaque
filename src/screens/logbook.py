import os
from datetime import datetime

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

import database
from base_screens import BackgroundedScreen, ROW_BACKGROUND, ROW_PRESSED, QUEEN_GRAY, QUEEN_GOLD, QUEEN_SILVER
from game import Game
from widgets import (
    RoundedButton, FixedGrayRoundedButton,
    TitleLgLabel, CaptionLabel, SubtitleLabel,
    TableHeaderLabel, TableCellLabel,
)
from ui_constants import (
    TEXT_LIGHT, ROW_HEIGHT, BUTTON_HEIGHT_SM,
    PADDING_ROW, SPACING_XS, SPACING_MD, RADIUS_SM,
    DATE_SEPARATOR_HEIGHT, TABLE_HEADER_HEIGHT,
)

# Path to icons
ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')

PAGE_SIZE = 20


class LogbookRow(ButtonBehavior, BoxLayout):
    """A tappable row in the logbook."""

    def __init__(self, play_data, on_select, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self.play_data = play_data
        self.on_select = on_select
        self.size_hint_y = None
        self.height = dp(ROW_HEIGHT)
        self.padding = [dp(PADDING_ROW[0]), dp(PADDING_ROW[1])]
        self.spacing = dp(SPACING_MD)

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

        # Format time only (date shown in separator)
        try:
            dt = datetime.fromisoformat(started_at)
            time_str = dt.strftime('%H:%M')
        except:
            time_str = '?'

        # Format duration
        if duration_ms:
            secs = duration_ms // 1000
            mins = secs // 60
            secs = secs % 60
            duration_str = f'{mins}:{secs:02d}'
        else:
            duration_str = '-'

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

        # Time column
        self.add_widget(TableCellLabel(time_str, size_hint_x=0.25, halign='left', valign='middle'))

        # Size column
        self.add_widget(TableCellLabel(f'{size}x{size}', color=TEXT_LIGHT, size_hint_x=0.25, halign='center'))

        # Duration column
        self.add_widget(TableCellLabel(duration_str, size_hint_x=0.25, halign='center'))

        # Crown icon
        crown = Image(
            source=os.path.join(ICONS_DIR, 'queen-small.png'),
            color=crown_color,
            size_hint_x=0.25,
            fit_mode='contain'
        )
        self.add_widget(crown)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*ROW_PRESSED)
            else:
                Color(*self._bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(RADIUS_SM)])

    def on_press(self):
        if self.on_select:
            self.on_select(self.play_data)


class DateSeparator(BoxLayout):
    """A date separator row."""

    def __init__(self, date_str, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(DATE_SEPARATOR_HEIGHT)
        self.padding = [dp(PADDING_ROW[0]), dp(PADDING_ROW[1])]

        self.add_widget(CaptionLabel(date_str, halign='left', valign='middle'))


class LogbookScreen(BackgroundedScreen):
    def get_padding(self):
        return 15

    def build_content(self):
        self.current_offset = 0
        self.has_more = False
        layout = self.content_layout

        # Title
        layout.add_widget(TitleLgLabel('Logbook'))

        # Header row
        header = BoxLayout(
            size_hint_y=None,
            height=dp(TABLE_HEADER_HEIGHT),
            padding=[dp(PADDING_ROW[0]), 0],
            spacing=dp(SPACING_MD)
        )
        header.add_widget(TableHeaderLabel('Time', size_hint_x=0.25, halign='left'))
        header.add_widget(TableHeaderLabel('Size', size_hint_x=0.25, halign='center'))
        header.add_widget(TableHeaderLabel('Duration', size_hint_x=0.25, halign='center'))
        header.add_widget(Label(text='', size_hint_x=0.25))
        layout.add_widget(header)

        # Scrollable list
        scroll = ScrollView(size_hint=(1, 1))
        self.list_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(SPACING_XS),
            padding=[0, dp(PADDING_ROW[1])]
        )
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        scroll.add_widget(self.list_layout)
        layout.add_widget(scroll)

        # Back button
        self.add_back_button()

    def _format_date(self, date_str):
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
        except:
            return date_str[:10] if date_str else '?'

    def _get_date_key(self, started_at):
        """Extract date part from started_at timestamp."""
        return started_at[:10] if started_at else ''

    def _on_game_selected(self, play_data):
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
                except:
                    pass

            self.app._on_game_ready(game, daily_date=parsed_date, from_logbook=True)
        except Exception as e:
            print(f"Error loading game: {e}")

    def _load_more(self, instance):
        """Load next page of games."""
        self._load_plays(append=True)

    def _load_plays(self, append=False):
        """Load plays from database."""
        if not append:
            self.list_layout.clear_widgets()
            self.current_offset = 0

        plays = database.get_all_plays(limit=PAGE_SIZE, offset=self.current_offset)
        total = database.get_plays_count()

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
            if isinstance(last, RoundedButton) or isinstance(last, GrayRoundedButton):
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

    def on_enter(self):
        """Refresh list when screen is shown."""
        self._load_plays(append=False)
