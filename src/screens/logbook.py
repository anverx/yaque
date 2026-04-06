from __future__ import annotations

from datetime import datetime
from typing import Any

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import database
from game import Game
from screens.base import BackgroundedScreen
from ui_constants import (
    BUTTON_HEIGHT_SM,
    PADDING_CELL,
    ROW_HEIGHT,
    SPACING_SM,
    STYLES,
    TEXT_LIGHT,
    TEXT_WHITE,
    TOP_SPACER_HEIGHT,
)
from widgets import (
    BarChart,
    CaptionLabel,
    DateSeparator,
    FixedGrayRoundedButton,
    GrayRoundedButton,
    LogbookRow,
    PanelLayout,
    RoundedButton,
    SelectableButton,
    SelectableButtonGroup,
    StatRow,
    SubtitleLabel,
    TableCellLabel,
    TableHeaderLabel,
    TitleLgLabel,
    styled,
)

PAGE_SIZE = 20


class LogbookScreen(BackgroundedScreen):
    def build_content(self) -> None:
        self.current_offset = 0
        self.has_more = False
        self.current_sort = 'time'
        self.current_tab = 'games'
        layout = self.content_layout

        # Extra spacer to push content below the banner
        layout.add_widget(BoxLayout(size_hint_y=None, height=dp(TOP_SPACER_HEIGHT)))

        # Title
        layout.add_widget(TitleLgLabel('Logbook'))

        # Tab selector row
        tab_row = styled(BoxLayout, 'selection_row')
        self.tab_group = SelectableButtonGroup(on_select=self._on_tab_changed)
        for tab_key, label in [('games', 'Games'), ('stats', 'Stats'), ('activity', 'Activity')]:
            btn = SelectableButton(
                text=label,
                selected=(tab_key == 'games'),
                **STYLES['selection_btn']
            )
            self.tab_group.add(tab_key, btn)
            tab_row.add_widget(btn)
        tab_row.add_widget(Label(size_hint_x=1))
        layout.add_widget(tab_row)

        # Sort selector row (visible only on Games tab)
        self.sort_row = styled(BoxLayout, 'selection_row')
        sort_label = CaptionLabel('Sort:', size_hint_x=None, width=dp(40))
        self.sort_row.add_widget(sort_label)
        self.sort_group = SelectableButtonGroup(on_select=self._on_sort_changed)
        for sort_key, label in [('time', 'When'), ('size', 'Size'), ('duration', 'Time'), ('rating', 'Rating')]:
            btn = SelectableButton(
                text=label,
                selected=(sort_key == 'time'),
                **STYLES['selection_btn']
            )
            self.sort_group.add(sort_key, btn)
            self.sort_row.add_widget(btn)
        self.sort_row.add_widget(Label(size_hint_x=1))
        layout.add_widget(self.sort_row)

        # Shared panel with dark background
        self.panel = PanelLayout(
            orientation='vertical',
            padding=[dp(PADDING_CELL[0]), dp(PADDING_CELL[1])],
        )

        # Games content (header + scrollable list)
        self.games_content = BoxLayout(orientation='vertical')
        header = styled(BoxLayout, 'table_header_row')
        header.add_widget(TableHeaderLabel('Type'))
        header.add_widget(TableHeaderLabel('Size'))
        header.add_widget(TableHeaderLabel('Time'))
        header.add_widget(TableHeaderLabel('Rating'))
        header.add_widget(TableHeaderLabel('When'))
        header.add_widget(TableHeaderLabel('Daily'))
        self.games_content.add_widget(header)
        scroll = ScrollView(size_hint=(1, 1))
        self.list_layout = styled(BoxLayout, 'list_layout')
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        scroll.add_widget(self.list_layout)
        self.games_content.add_widget(scroll)

        # Stats content (scrollable, rebuilt on each refresh)
        self.stats_scroll = ScrollView(size_hint=(1, 1))
        self.stats_content = styled(BoxLayout, 'list_layout', spacing=dp(4))
        self.stats_content.bind(minimum_height=self.stats_content.setter('height'))
        self.stats_scroll.add_widget(self.stats_content)

        # Activity content (rebuilt on each refresh)
        self.activity_content = BoxLayout(orientation='vertical')

        # Start with games content
        self.panel.add_widget(self.games_content)
        layout.add_widget(self.panel)

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

    def _on_tab_changed(self, tab_key: str) -> None:
        """Switch between Games, Stats, and Activity tabs."""
        self.current_tab = tab_key
        self.panel.clear_widgets()
        if tab_key == 'games':
            self.sort_row.height = dp(BUTTON_HEIGHT_SM)
            self.sort_row.opacity = 1
            self.panel.add_widget(self.games_content)
            self._load_plays(append=False)
        elif tab_key == 'stats':
            self.sort_row.height = 0
            self.sort_row.opacity = 0
            self._refresh_stats()
            self.panel.add_widget(self.stats_scroll)
        elif tab_key == 'activity':
            self.sort_row.height = 0
            self.sort_row.opacity = 0
            self._refresh_activity()
            self.panel.add_widget(self.activity_content)

    def _format_duration(self, duration_ms: int | None) -> str:
        """Format milliseconds as M:SS."""
        if not duration_ms:
            return '-'
        secs = duration_ms // 1000
        return f'{secs // 60}:{secs % 60:02d}'

    def _format_total_time(self, total_ms: int) -> str:
        """Format total milliseconds as human-readable duration."""
        total_secs = total_ms // 1000
        hours = total_secs // 3600
        mins = (total_secs % 3600) // 60
        if hours > 0:
            return f'{hours}h {mins}m'
        return f'{mins}m'

    def _refresh_stats(self) -> None:
        """Refresh the stats panel with current data."""
        self.stats_content.clear_widgets()
        time_stats = database.get_time_stats_by_size()
        logbook_stats = database.get_logbook_stats()

        spacer_h = dp(SPACING_SM)

        # Times table header
        self.stats_content.add_widget(SubtitleLabel('Solve Times', color=TEXT_WHITE))
        header = StatRow()
        header.add_widget(TableHeaderLabel('Size'))
        header.add_widget(TableHeaderLabel('Best'))
        header.add_widget(TableHeaderLabel('Average'))
        header.add_widget(TableHeaderLabel('Games'))
        self.stats_content.add_widget(header)

        # Times table rows
        for size in [6, 7, 8, 9]:
            stats = time_stats.get(size)
            best = self._format_duration(stats['best_time']) if stats else '-'
            avg = self._format_duration(stats['avg_time']) if stats else '-'
            count = str(stats['play_count']) if stats else '0'
            row = StatRow()
            row.add_widget(TableCellLabel(f'{size}x{size}', color=TEXT_LIGHT))
            row.add_widget(TableCellLabel(best))
            row.add_widget(TableCellLabel(avg))
            row.add_widget(TableCellLabel(count))
            self.stats_content.add_widget(row)

        # Spacer
        self.stats_content.add_widget(BoxLayout(size_hint_y=None, height=spacer_h))

        # Summary section
        self.stats_content.add_widget(SubtitleLabel('Summary', color=TEXT_WHITE))
        total = logbook_stats['total_completed']
        total_time = self._format_total_time(logbook_stats['total_time_ms'])

        for label, value in [('Completed', str(total)), ('Total Time', total_time)]:
            row = StatRow()
            row.add_widget(TableCellLabel(label, color=TEXT_LIGHT))
            row.add_widget(TableCellLabel(value))
            self.stats_content.add_widget(row)

    def _refresh_activity(self) -> None:
        """Refresh the activity chart."""
        self.activity_content.clear_widgets()
        self.activity_content.add_widget(SubtitleLabel('Games per Day (30 days)', color=TEXT_WHITE))
        data = database.get_games_per_day(30)
        total = sum(sum(v.values()) for _, v in data)
        chart = BarChart(data)
        self.activity_content.add_widget(chart)
        self.activity_content.add_widget(
            CaptionLabel(f'{total} games in the last 30 days', color=TEXT_LIGHT)
        )

    def _on_sort_changed(self, sort_key: str) -> None:
        """Handle sort option change."""
        self.current_sort = sort_key
        self._load_plays(append=False)

    def on_enter(self) -> None:
        """Refresh current tab when screen is shown."""
        if self.current_tab == 'games':
            self._load_plays(append=False)
        elif self.current_tab == 'stats':
            self._refresh_stats()
        elif self.current_tab == 'activity':
            self._refresh_activity()
