from __future__ import annotations

import threading
import os
from datetime import date
from typing import Any

__version__ = "1.0.1"
__author__ = "Yaque Contributors"

from kivy.app import App
import database
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.utils import platform

# Register DM Sans font
FONTS_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'fonts')
LabelBase.register(
    name='DMSans',
    fn_regular=os.path.join(FONTS_DIR, 'DMSans-Regular.ttf'),
    fn_bold=os.path.join(FONTS_DIR, 'DMSans-Bold.ttf')
)
LabelBase.register(
    name='DMSansBlack',
    fn_regular=os.path.join(FONTS_DIR, 'DMSans-Black.ttf')
)

from game import Game, get_daily_game
from screens import (
    SplashScreen,
    MainMenuScreen,
    CalendarScreen,
    GameScreen,
    LogbookScreen,
)
from popups import show_share_popup, show_load_popup, show_game_size_popup, LoadingPopup
from widgets import (
    GrayRoundedButton, TitleLabel, SubtitleLabel, CaptionLabel,
    AboutTitleLabel, AboutSubtitleLabel, LinkButton,
    PopupContent, Popup,
)
from ui_constants import (
    BUTTON_HEIGHT_SM, POPUP_BACKGROUND,
    PADDING_POPUP_LARGE, CAPTION_HEIGHT_XS, SMALL_BUTTON_WIDTH,
    WINDOW_SIZE, WINDOW_CLEARCOLOR,
)

# Android intent handling
if platform == 'android':
    from android import activity
    from jnius import autoclass
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')

# Set window mode before app starts
if platform in ('android', 'ios'):
    Window.fullscreen = 'auto'
else:
    Window.size = WINDOW_SIZE

Window.clearcolor = WINDOW_CLEARCOLOR


class YaqueApp(App):
    def build(self) -> ScreenManager:
        # Initialize database
        database.init_db(self.user_data_dir)

        self.sm = ScreenManager(transition=FadeTransition())

        # Create screens
        self.splash_screen = SplashScreen(name='splash')
        self.menu_screen = MainMenuScreen(self, name='menu')
        self.calendar_screen = CalendarScreen(self, name='calendar')
        self.game_screen = GameScreen(self, name='game')
        self.logbook_screen = LogbookScreen(self, name='logbook')

        self.sm.add_widget(self.splash_screen)
        self.sm.add_widget(self.menu_screen)
        self.sm.add_widget(self.calendar_screen)
        self.sm.add_widget(self.game_screen)
        self.sm.add_widget(self.logbook_screen)

        # Loading popup (reusable)
        self.loading_popup = None
        self._generation_cancelled = False

        # Start with splash screen
        self.sm.current = 'splash'

        # Transition to menu after brief delay
        Clock.schedule_once(self._go_to_menu, 1.5)

        # Handle incoming intent on Android
        if platform == 'android':
            activity.bind(on_new_intent=self._on_new_intent)
            # Check initial intent
            Clock.schedule_once(lambda dt: self._check_initial_intent(), 2)

        return self.sm

    # -------------------------------------------------------------------------
    # Android intent handling
    # -------------------------------------------------------------------------

    def _check_initial_intent(self) -> None:
        """Check if app was launched via custom URL scheme."""
        if platform != 'android':
            return
        try:
            from android import mActivity
            intent = mActivity.getIntent()
            self._handle_intent(intent)
        except Exception as e:
            print(f"Error checking initial intent: {e}")

    def _on_new_intent(self, intent: Any) -> None:
        """Handle new intent when app is already running."""
        self._handle_intent(intent)

    def _handle_intent(self, intent: Any) -> None:
        """Parse and handle yaque:// URL from intent."""
        if platform != 'android':
            return
        try:
            action = intent.getAction()
            if action == Intent.ACTION_VIEW:
                uri = intent.getData()
                if uri:
                    scheme = uri.getScheme()
                    if scheme == 'yaque':
                        game_code = uri.getQueryParameter('game') or uri.getQueryParameter('g')
                        if game_code:
                            self._load_shared_game(game_code)
        except Exception as e:
            print(f"Error handling intent: {e}")

    def _load_shared_game(self, code: str) -> None:
        """Load a game from shared code."""
        try:
            game = Game.from_code(code)
            self._on_game_ready(game)
        except Exception as e:
            print(f"Error loading shared game: {e}")

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------

    def _go_to_menu(self, dt: float) -> None:
        self.sm.current = 'menu'

    def show_calendar(self, instance: Any) -> None:
        self.sm.current = 'calendar'

    # -------------------------------------------------------------------------
    # Game generation
    # -------------------------------------------------------------------------

    def _show_loading_popup(self, status_text: str) -> None:
        """Show the loading popup with spinning queen."""
        self._generation_cancelled = False
        self.loading_popup = LoadingPopup(on_cancel=self.cancel_generation)
        self.loading_popup.set_status(status_text)
        self.loading_popup.open()

    def _dismiss_loading_popup(self) -> None:
        """Dismiss the loading popup if open."""
        if self.loading_popup:
            self.loading_popup.dismiss()
            self.loading_popup = None

    def start_daily_game(self, size: int, puzzle_date: date | None = None, from_calendar: bool = False) -> None:
        if puzzle_date is None:
            puzzle_date = date.today()

        # Check if puzzle already exists in database
        existing = database.get_daily_puzzle(puzzle_date.isoformat(), size)
        if existing:
            # Load from database - no need to generate
            game = Game.from_code(existing['code'])
            game.seed = existing.get('seed')
            self._on_game_ready(game, daily_date=puzzle_date, from_calendar=from_calendar)
            return

        # Generate new puzzle
        self._show_loading_popup(f'Generating {size}x{size} puzzle...')

        def generate() -> None:
            game = get_daily_game(puzzle_date, size, max_solutions=4)
            if not self._generation_cancelled:
                Clock.schedule_once(lambda dt: self._on_game_ready(
                    game, daily_date=puzzle_date, from_calendar=from_calendar
                ))

        threading.Thread(target=generate, daemon=True).start()

    def start_random_game(self, instance: Any) -> None:
        """Show size selection popup, then generate random game."""
        show_game_size_popup(self._start_random_game_with_size_and_strategy)

    def _start_random_game_with_size_and_strategy(self, size: int, strategy: str) -> None:
        """Generate a random game with the selected size and kingdom strategy."""
        # Expected generation times based on board size
        expected_times = {6: '<1s', 7: '~1s', 8: '~10s', 9: '~50s'}
        time_hint = expected_times.get(size, '')
        time_str = f' (avg. {time_hint})' if time_hint else ''
        self._show_loading_popup(f'Finding the perfect {size}x{size} puzzle...{time_str}')

        def generate() -> None:
            try:
                game = Game(size, max_solutions=1, kingdom_strategy=strategy)
                if not self._generation_cancelled:
                    Clock.schedule_once(lambda dt: self._on_game_ready(game, strategy=strategy))
            except ValueError:
                # Failed to generate - try again with more solutions allowed
                if not self._generation_cancelled:
                    Clock.schedule_once(lambda dt: self._on_generation_failed(size, strategy, 1))

        threading.Thread(target=generate, daemon=True).start()

    def _on_generation_failed(self, size: int, strategy: str, max_solutions: int) -> None:
        """Handle failed puzzle generation by retrying with relaxed constraints."""
        # Retry tiers: 1 -> 4 -> 10 -> give up
        next_max = {1: 4, 4: 10}.get(max_solutions)

        if next_max is None:
            # Completely failed
            self._dismiss_loading_popup()
            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            popup = Popup(
                title='Generation Failed',
                content=Label(text='Could not generate puzzle.\nPlease try again.'),
                size_hint=(0.8, 0.3)
            )
            popup.open()
            return

        self._dismiss_loading_popup()
        expected_times = {6: '<1s', 7: '~1s', 8: '~10s', 9: '~50s'}
        time_hint = expected_times.get(size, '')
        time_str = f' (avg. {time_hint})' if time_hint else ''
        self._show_loading_popup(f'Retrying {size}x{size} puzzle...{time_str}')

        def retry() -> None:
            try:
                game = Game(size, max_solutions=next_max, kingdom_strategy=strategy)
                if not self._generation_cancelled:
                    Clock.schedule_once(lambda dt: self._on_game_ready(game, strategy=strategy))
            except ValueError:
                if not self._generation_cancelled:
                    Clock.schedule_once(lambda dt: self._on_generation_failed(size, strategy, next_max))

        threading.Thread(target=retry, daemon=True).start()

    def _on_game_ready(self, game: Game, daily_date: date | None = None, from_calendar: bool = False, from_logbook: bool = False, strategy: str | None = None) -> None:
        if not self._generation_cancelled:
            self._dismiss_loading_popup()
            self.game_screen.set_game(game, daily_date=daily_date, from_calendar=from_calendar, from_logbook=from_logbook, strategy=strategy)
            self.sm.current = 'game'

    def cancel_generation(self) -> None:
        """Cancel ongoing game generation."""
        self._generation_cancelled = True

    # -------------------------------------------------------------------------
    # Popups
    # -------------------------------------------------------------------------

    def show_share_popup(self, share_url: str, code: str) -> None:
        show_share_popup(share_url, code)

    def show_load_popup(self, instance: Any) -> None:
        show_load_popup(self._on_game_ready)

    def show_logbook(self, instance: Any) -> None:
        """Show the logbook/statistics screen."""
        self.sm.current = 'logbook'

    def show_about(self, instance: Any) -> None:
        """Show the about popup."""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.modalview import ModalView
        from kivy.metrics import dp

        content = PopupContent(padding=[dp(PADDING_POPUP_LARGE[0]), dp(PADDING_POPUP_LARGE[1])])

        # Title
        content.add_widget(AboutTitleLabel('Yaque'))

        # Subtitle
        content.add_widget(AboutSubtitleLabel('A Queens Puzzle Game'))

        # Description
        desc = SubtitleLabel(
            'Place one queen in each colored kingdom.\nQueens cannot attack each other\n(no shared rows, columns, or adjacent cells).',
            height=70,
            halign='center',
            valign='middle'
        )
        desc.bind(width=lambda *x: setattr(desc, 'text_size', (desc.width, None)))
        content.add_widget(desc)

        # Spacer
        content.add_widget(BoxLayout(size_hint_y=0.3))

        # License
        content.add_widget(CaptionLabel('License: CC BY-NC-SA 4.0', size_hint_y=None, height=dp(CAPTION_HEIGHT_XS)))

        # Version
        content.add_widget(CaptionLabel(f'Version {__version__}', size_hint_y=None, height=dp(CAPTION_HEIGHT_XS)))

        # GitHub link
        github_btn = LinkButton('github.com/anverx/yaque')
        github_btn.bind(on_press=lambda x: self._open_url('https://github.com/anverx/yaque'))
        content.add_widget(github_btn)

        # Close button
        close_btn = GrayRoundedButton(
            text='Close',
            size_hint=(None, None),
            size=(dp(SMALL_BUTTON_WIDTH), dp(BUTTON_HEIGHT_SM)),
            pos_hint={'center_x': 0.5}
        )
        content.add_widget(close_btn)

        popup = ModalView(
            size_hint=(0.85, 0.55),
            auto_dismiss=True,
            background_color=POPUP_BACKGROUND
        )
        popup.add_widget(content)
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _open_url(self, url: str) -> None:
        """Open URL in browser."""
        import webbrowser
        webbrowser.open(url)

    # -------------------------------------------------------------------------
    # App lifecycle
    # -------------------------------------------------------------------------

    def exit_app(self, instance: Any) -> None:
        App.get_running_app().stop()

    def on_stop(self) -> None:
        database.close_db()


if __name__ == "__main__":
    YaqueApp().run()
