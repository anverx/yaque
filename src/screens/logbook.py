"""yaque logbook — supplies tabs (Games / Stats / Activity) to kivyshell's LogbookScreen.

The tab chrome (switcher, panel, controls slot, back) lives in the shell; all the
DB queries, the games list + pagination, the stats table (by board size), and the
activity charts stay here.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import database
from game import Game
from ui_constants import (
    BUTTON_HEIGHT_SM,
    ROW_HEIGHT,
    SPACING_SM,
    STYLES,
    TEXT_LIGHT,
    TEXT_WHITE,
)
from widgets import (
    BarChart,
    CaptionLabel,
    DateSeparator,
    FixedGrayRoundedButton,
    GrayRoundedButton,
    LogbookRow,
    RoundedButton,
    SelectableButton,
    SelectableButtonGroup,
    StatRow,
    SubtitleLabel,
    TableCellLabel,
    TableHeaderLabel,
    styled,
)
from kivyshell.shell.screens.logbook import LogbookConfig, LogbookScreen as _LogbookScreen, LogbookTab

PAGE_SIZE = 20


class LogbookScreen(_LogbookScreen):
    def logbook_config(self) -> LogbookConfig:
        self.current_offset = 0
        self.has_more = False
        self.current_sort = 'time'

        # Games content: header + scrollable list
        self.games_content = BoxLayout(orientation='vertical')
        header = styled(BoxLayout, 'table_header_row')
        for col in ('Type', 'Size', 'Time', 'Rating', 'When', 'Daily'):
            header.add_widget(TableHeaderLabel(col))
        self.games_content.add_widget(header)
        scroll = ScrollView(size_hint=(1, 1))
        self.list_layout = styled(BoxLayout, 'list_layout')
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        scroll.add_widget(self.list_layout)
        self.games_content.add_widget(scroll)

        # Stats content
        self.stats_scroll = ScrollView(size_hint=(1, 1))
        self.stats_content = styled(BoxLayout, 'list_layout', spacing=dp(4))
        self.stats_content.bind(minimum_height=self.stats_content.setter('height'))
        self.stats_scroll.add_widget(self.stats_content)

        # Activity content
        self.activity_content = BoxLayout(orientation='vertical')

        # Sort selector row (shown only on the Games tab)
        self.sort_row = styled(BoxLayout, 'selection_row')
        self.sort_row.add_widget(CaptionLabel('Sort:', size_hint_x=None, width=dp(40)))
        self.sort_group = SelectableButtonGroup(on_select=self._on_sort_changed)
        for sort_key, label in [('time', 'When'), ('size', 'Size'), ('duration', 'Time'), ('rating', 'Rating')]:
            btn = SelectableButton(text=label, selected=(sort_key == 'time'), **STYLES['selection_btn'])
            self.sort_group.add(sort_key, btn)
            self.sort_row.add_widget(btn)
        self.sort_row.add_widget(Label(size_hint_x=1))

        return LogbookConfig(title='Logbook', tabs=[
            LogbookTab('games', 'Games', build=lambda: self.games_content,
                       refresh=lambda: self._load_plays(append=False), controls=self.sort_row),
            LogbookTab('stats', 'Stats', build=lambda: self.stats_scroll, refresh=self._refresh_stats),
            LogbookTab('activity', 'Activity', build=lambda: self.activity_content, refresh=self._refresh_activity),
        ])

    # --- helpers (ported verbatim) ---
    def _format_date(self, date_str: str) -> str:
        try:
            dt = datetime.fromisoformat(date_str)
            today = datetime.now().date()
            if dt.date() == today:
                return 'Today'
            if (today - dt.date()).days == 1:
                return 'Yesterday'
            return dt.strftime('%A, %b %d')
        except Exception:
            return date_str[:10] if date_str else '?'

    def _get_date_key(self, started_at: str) -> str:
        return started_at[:10] if started_at else ''

    def _on_game_selected(self, play_data: dict[str, Any]) -> None:
        code = play_data['code']
        daily_date = play_data['daily_date']
        try:
            game = Game.from_code(code)
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
        self._load_plays(append=True)

    def _load_plays(self, append: bool = False) -> None:
        if not append:
            self.list_layout.clear_widgets()
            self.current_offset = 0

        plays = database.get_all_plays(limit=PAGE_SIZE, offset=self.current_offset, sort_by=self.current_sort)
        total = database.get_plays_count(sort_by=self.current_sort)

        if not plays and not append:
            self.list_layout.add_widget(SubtitleLabel('No games played yet', size_hint_y=None, height=dp(ROW_HEIGHT)))
            return

        if append and self.list_layout.children:
            last = self.list_layout.children[0]
            if isinstance(last, (RoundedButton, GrayRoundedButton)):
                self.list_layout.remove_widget(last)

        last_date = None
        if append and self.list_layout.children:
            for child in reversed(self.list_layout.children):
                if isinstance(child, LogbookRow):
                    last_date = self._get_date_key(child.play_data['started_at'])
                    break

        current_date = last_date
        for play in plays:
            play_date = self._get_date_key(play['started_at'])
            if play_date != current_date:
                current_date = play_date
                self.list_layout.add_widget(DateSeparator(self._format_date(play['started_at'])))
            self.list_layout.add_widget(LogbookRow(play, self._on_game_selected))

        self.current_offset += len(plays)
        self.has_more = self.current_offset < total

        if self.has_more:
            remaining = total - self.current_offset
            load_more_btn = FixedGrayRoundedButton(text=f'Load More ({remaining} remaining)', height=dp(BUTTON_HEIGHT_SM))
            load_more_btn.bind(on_press=self._load_more)
            self.list_layout.add_widget(load_more_btn)

    def _format_duration(self, duration_ms: int | None) -> str:
        if not duration_ms:
            return '-'
        secs = duration_ms // 1000
        return f'{secs // 60}:{secs % 60:02d}'

    def _format_total_time(self, total_ms: int) -> str:
        total_secs = total_ms // 1000
        hours = total_secs // 3600
        mins = (total_secs % 3600) // 60
        return f'{hours}h {mins}m' if hours > 0 else f'{mins}m'

    def _refresh_stats(self) -> None:
        self.stats_content.clear_widgets()
        time_stats = database.get_time_stats_by_size()
        logbook_stats = database.get_logbook_stats()

        self.stats_content.add_widget(SubtitleLabel('Solve Times', color=TEXT_WHITE))
        header = StatRow()
        for col in ('Size', 'Best', 'Average', 'Games'):
            header.add_widget(TableHeaderLabel(col))
        self.stats_content.add_widget(header)

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

        self.stats_content.add_widget(BoxLayout(size_hint_y=None, height=dp(SPACING_SM)))

        self.stats_content.add_widget(SubtitleLabel('Summary', color=TEXT_WHITE))
        total = logbook_stats['total_completed']
        total_time = self._format_total_time(logbook_stats['total_time_ms'])
        for label, value in [('Completed', str(total)), ('Total Time', total_time)]:
            row = StatRow()
            row.add_widget(TableCellLabel(label, color=TEXT_LIGHT))
            row.add_widget(TableCellLabel(value))
            self.stats_content.add_widget(row)

    def _refresh_activity(self) -> None:
        self.activity_content.clear_widgets()

        self.activity_content.add_widget(SubtitleLabel('Games per Day (30 days)', color=TEXT_WHITE))
        games_data = database.get_games_per_day(30)
        total_games = sum(sum(v.values()) for _, v in games_data)
        self.activity_content.add_widget(BarChart(games_data))
        self.activity_content.add_widget(CaptionLabel(f'{total_games} games in the last 30 days', color=TEXT_LIGHT))

        self.activity_content.add_widget(BoxLayout(size_hint_y=None, height=dp(SPACING_SM)))

        self.activity_content.add_widget(SubtitleLabel('Minutes per Day (30 days)', color=TEXT_WHITE))
        minutes_data = database.get_minutes_per_day(30)
        total_minutes = sum(sum(v.values()) for _, v in minutes_data)
        self.activity_content.add_widget(BarChart(minutes_data))
        self.activity_content.add_widget(CaptionLabel(f'{total_minutes} minutes in the last 30 days', color=TEXT_LIGHT))

    def _on_sort_changed(self, sort_key: str) -> None:
        self.current_sort = sort_key
        self._load_plays(append=False)
