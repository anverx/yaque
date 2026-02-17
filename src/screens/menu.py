from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout

import database
from screens.base import BackgroundedScreen
from ui_constants import STYLES
from widgets import BackButton, ButtonRow, FixedRoundedButton, RoundedButton, TallRoundedButton, TitleMdLabel


class MainMenuScreen(BackgroundedScreen):
    def build_content(self) -> None:
        layout = self.content_layout

        # Extra spacer for menu layout
        layout.add_widget(BoxLayout(size_hint_y=0.2))

        # Daily puzzles section
        layout.add_widget(TitleMdLabel("Today's Puzzles"))

        daily_buttons = ButtonRow()
        self.daily_buttons = {}
        for size in [6, 7, 8]:
            btn = RoundedButton(text=f'{size}x{size}')
            btn.bind(on_press=lambda x, s=size: self.app.start_daily_game(s))
            self.daily_buttons[size] = btn
            daily_buttons.add_widget(btn)
        layout.add_widget(daily_buttons)

        # Spacer before middle buttons
        layout.add_widget(BoxLayout(size_hint_y=0.25))

        # Calendar button with streak display
        self.calendar_btn = TallRoundedButton(text='Calendar')
        self.calendar_btn.bind(on_press=self.app.show_calendar)
        layout.add_widget(self.calendar_btn)

        # Random game button
        random_btn = FixedRoundedButton(text='Random Game')
        random_btn.bind(on_press=self.app.start_random_game)
        layout.add_widget(random_btn)

        # Load shared puzzle button
        load_btn = FixedRoundedButton(text='Load Shared Puzzle')
        load_btn.bind(on_press=self.app.show_load_popup)
        layout.add_widget(load_btn)

        # Logbook button
        logbook_btn = FixedRoundedButton(text='Logbook')
        logbook_btn.bind(on_press=self.app.show_logbook)
        layout.add_widget(logbook_btn)

        # About button
        about_btn = FixedRoundedButton(text='About')
        about_btn.bind(on_press=self.app.show_about)
        layout.add_widget(about_btn)

        # Spacer
        layout.add_widget(BoxLayout(size_hint_y=0.1))

        # Exit button
        exit_btn = BackButton(text='Exit')
        exit_btn.bind(on_press=self.app.exit_app)
        layout.add_widget(exit_btn)

    def on_enter(self) -> None:
        """Called when screen is entered - refresh streak display."""
        streak = database.get_current_streak()
        if streak > 0:
            streak_text = f"Streak: {streak} day{'s' if streak != 1 else ''}"
        else:
            streak_text = "Start a streak!"
        caption_size = STYLES['caption']['font_size']
        self.calendar_btn.text = f"Calendar\n[size={caption_size}]{streak_text}[/size]"
