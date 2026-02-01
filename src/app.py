import threading
import os
from datetime import date

from kivy.app import App
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
    DatePuzzlesScreen,
    GameScreen,
)
from popups import show_share_popup, show_load_popup, LoadingPopup

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
    # Simulate phone resolution for testing (e.g., 1080x1920 at ~3x density)
    Window.size = (360, 640)  # Logical phone resolution

# Light background
Window.clearcolor = (0.95, 0.95, 0.95, 1)


class YaqueApp(App):
    def build(self):
        self.sm = ScreenManager(transition=FadeTransition())

        # Create screens
        self.splash_screen = SplashScreen(name='splash')
        self.menu_screen = MainMenuScreen(self, name='menu')
        self.calendar_screen = CalendarScreen(self, name='calendar')
        self.date_puzzles_screen = DatePuzzlesScreen(self, name='date_puzzles')
        self.game_screen = GameScreen(self, name='game')

        self.sm.add_widget(self.splash_screen)
        self.sm.add_widget(self.menu_screen)
        self.sm.add_widget(self.calendar_screen)
        self.sm.add_widget(self.date_puzzles_screen)
        self.sm.add_widget(self.game_screen)

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

    def _check_initial_intent(self):
        """Check if app was launched via custom URL scheme."""
        if platform != 'android':
            return
        try:
            from android import mActivity
            intent = mActivity.getIntent()
            self._handle_intent(intent)
        except Exception as e:
            print(f"Error checking initial intent: {e}")

    def _on_new_intent(self, intent):
        """Handle new intent when app is already running."""
        self._handle_intent(intent)

    def _handle_intent(self, intent):
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

    def _load_shared_game(self, code):
        """Load a game from shared code."""
        try:
            game = Game.from_code(code)
            self._on_game_ready(game)
        except Exception as e:
            print(f"Error loading shared game: {e}")

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------

    def _go_to_menu(self, dt):
        self.sm.current = 'menu'

    def show_calendar(self, instance):
        self.sm.current = 'calendar'

    def show_date_puzzles(self, selected_date):
        self.date_puzzles_screen.set_date(selected_date)
        self.sm.current = 'date_puzzles'

    # -------------------------------------------------------------------------
    # Game generation
    # -------------------------------------------------------------------------

    def _show_loading_popup(self, status_text):
        """Show the loading popup with spinning queen."""
        self._generation_cancelled = False
        self.loading_popup = LoadingPopup(on_cancel=self.cancel_generation)
        self.loading_popup.set_status(status_text)
        self.loading_popup.open()

    def _dismiss_loading_popup(self):
        """Dismiss the loading popup if open."""
        if self.loading_popup:
            self.loading_popup.dismiss()
            self.loading_popup = None

    def start_daily_game(self, size, puzzle_date=None):
        if puzzle_date is None:
            puzzle_date = date.today()
        self._show_loading_popup(f'Generating {size}x{size} puzzle...')

        def generate():
            game = get_daily_game(puzzle_date, size, max_solutions=4)
            if not self._generation_cancelled:
                Clock.schedule_once(lambda dt: self._on_game_ready(game))

        threading.Thread(target=generate, daemon=True).start()

    def start_random_game(self, instance):
        self._show_loading_popup('Finding the perfect puzzle...')

        def generate():
            game = Game(7, max_solutions=1)
            if not self._generation_cancelled:
                Clock.schedule_once(lambda dt: self._on_game_ready(game))

        threading.Thread(target=generate, daemon=True).start()

    def _on_game_ready(self, game):
        if not self._generation_cancelled:
            self._dismiss_loading_popup()
            self.game_screen.set_game(game)
            self.sm.current = 'game'

    def cancel_generation(self):
        """Cancel ongoing game generation."""
        self._generation_cancelled = True

    # -------------------------------------------------------------------------
    # Popups
    # -------------------------------------------------------------------------

    def show_share_popup(self, share_url, code):
        show_share_popup(share_url, code)

    def show_load_popup(self, instance):
        show_load_popup(self._on_game_ready)

    # -------------------------------------------------------------------------
    # App lifecycle
    # -------------------------------------------------------------------------

    def exit_app(self, instance):
        App.get_running_app().stop()


if __name__ == "__main__":
    YaqueApp().run()
