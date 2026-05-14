from __future__ import annotations

import os
import threading
import time
from datetime import date
from typing import Any

__version__ = "1.3.0"
__author__ = "Anatoli V. and Claude C."

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.uix.screenmanager import FadeTransition, ScreenManager
from kivy.utils import platform

import database

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
LabelBase.register(
    name='Stars',
    fn_regular=os.path.join(FONTS_DIR, 'NotoSans-Stars.ttf')
)

from game import Game, GenerationCancelled, get_daily_game
from popups import LoadingPopup, show_game_size_popup, show_load_popup, show_share_popup
from screens import (
    CalendarScreen,
    GameScreen,
    LogbookScreen,
    MainMenuScreen,
    SplashScreen,
)
from ui_constants import (
    BUTTON_HEIGHT_SM,
    CAPTION_HEIGHT_XS,
    PADDING_POPUP_LARGE,
    POPUP_BACKGROUND,
    SMALL_BUTTON_WIDTH,
    WINDOW_CLEARCOLOR,
    WINDOW_SIZE,
)
from widgets import (
    AboutSubtitleLabel,
    AboutTitleLabel,
    CaptionLabel,
    GrayRoundedButton,
    LinkButton,
    PopupContent,
    SubtitleLabel,
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

    def _show_loading_popup(self, status_text: str, subtitle: str = '') -> None:
        """Show the loading popup with spinning queen."""
        self._generation_cancelled = False
        # Increment generation ID to invalidate any previous generation
        self._generation_id = getattr(self, '_generation_id', 0) + 1
        self.loading_popup = LoadingPopup(on_cancel=self.cancel_generation)
        self.loading_popup.set_status(status_text, subtitle)
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
        self._show_loading_popup(f'Computing {size}x{size} puzzle...')
        gen_id = self._generation_id  # Capture current generation ID

        def cancel_check() -> bool:
            return self._generation_cancelled or gen_id != self._generation_id

        def generate() -> None:
            try:
                start_time = time.time()
                game = get_daily_game(puzzle_date, size, max_solutions=1, cancel_check=cancel_check)
                game.generation_time_ms = int((time.time() - start_time) * 1000)
                # Check both cancelled flag and generation ID
                if not cancel_check():
                    Clock.schedule_once(lambda dt: self._on_game_ready(
                        game, daily_date=puzzle_date, from_calendar=from_calendar
                    ))
            except GenerationCancelled:
                pass  # Silently ignore cancelled generation

        threading.Thread(target=generate, daemon=True).start()

    def start_random_game(self, instance: Any) -> None:
        """Show options popup, then generate random game."""
        show_game_size_popup(self._start_random_game_with_options)

    @staticmethod
    def _format_gen_time_hint(size: int, unique: bool) -> str:
        """Format generation time hint from DB averages."""
        avg_ms = database.get_avg_generation_time(size, unique)
        if avg_ms is not None:
            secs = avg_ms / 1000
            if secs < 1:
                return 'avg. <1s'
            elif secs < 60:
                return f'avg. ~{int(secs)}s'
            else:
                return f'avg. ~{int(secs // 60)}m{int(secs % 60):02d}s'
        if size >= 8:
            return 'could take some time'
        return ''

    def _start_random_game_with_options(self, size: int, strategy: str, max_solutions: int,
                                          queen_placement: str = 'backtrack') -> None:
        """Generate a random game with the selected options."""
        hint = self._format_gen_time_hint(size, max_solutions == 1)
        self._show_loading_popup(f'Computing {size}x{size} puzzle...', hint)
        gen_id = self._generation_id  # Capture current generation ID

        # Store the user's requested max_solutions for retry logic
        self._requested_max_solutions = max_solutions

        def cancel_check() -> bool:
            return self._generation_cancelled or gen_id != self._generation_id

        def generate() -> None:
            try:
                start_time = time.time()
                game = Game(size, max_solutions=max_solutions, kingdom_strategy=strategy,
                           cancel_check=cancel_check, queen_placement=queen_placement)
                game.generation_time_ms = int((time.time() - start_time) * 1000)
                if not cancel_check():
                    Clock.schedule_once(lambda dt: self._on_game_ready(game, strategy=strategy))
            except GenerationCancelled:
                pass  # Silently ignore cancelled generation
            except ValueError:
                # Failed to generate - try again with more solutions allowed
                if not cancel_check():
                    Clock.schedule_once(lambda dt: self._on_generation_failed(size, strategy, max_solutions))

        threading.Thread(target=generate, daemon=True).start()

    def _on_generation_failed(self, size: int, strategy: str, max_solutions: int) -> None:
        """Handle failed puzzle generation by retrying with relaxed constraints."""
        # Retry tiers based on what user requested
        if max_solutions < 4:
            next_max = 4
        elif max_solutions < 10:
            next_max = 10
        else:
            next_max = None

        if next_max is None:
            # Completely failed
            self._dismiss_loading_popup()
            from kivy.uix.label import Label
            from kivy.uix.popup import Popup
            popup = Popup(
                title='Generation Failed',
                content=Label(text='Could not generate puzzle.\nPlease try again.'),
                size_hint=(0.8, 0.3)
            )
            popup.open()
            return

        # Update status without dismissing — keeps timer running smoothly
        if self.loading_popup:
            self.loading_popup.set_status(f'Relaxing to {next_max} solutions...', '')
        gen_id = self._generation_id

        def cancel_check() -> bool:
            return self._generation_cancelled or gen_id != self._generation_id

        def retry() -> None:
            try:
                start_time = time.time()
                game = Game(size, max_solutions=next_max, kingdom_strategy=strategy, cancel_check=cancel_check)
                game.generation_time_ms = int((time.time() - start_time) * 1000)
                if not cancel_check():
                    Clock.schedule_once(lambda dt: self._on_game_ready(game, strategy=strategy))
            except GenerationCancelled:
                pass  # Silently ignore cancelled generation
            except ValueError:
                if not cancel_check():
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
        from kivy.metrics import dp
        from kivy.uix.behaviors import ButtonBehavior
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.modalview import ModalView

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

        # Tappable version label for hidden dev menu
        class TappableLabel(ButtonBehavior, Label):
            pass

        tap_state = {'count': 0, 'last_tap': 0.0}

        def on_version_tap(instance: Any) -> None:
            current_time = time.time()
            # Reset if more than 2 seconds since last tap
            if current_time - tap_state['last_tap'] > 2.0:
                tap_state['count'] = 0
            tap_state['count'] += 1
            tap_state['last_tap'] = current_time
            if tap_state['count'] >= 5:
                tap_state['count'] = 0
                popup.dismiss()
                self._show_dev_menu()

        version_label = TappableLabel(
            text=f'Version {__version__}',
            font_name='DMSans',
            font_size='12sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=dp(CAPTION_HEIGHT_XS)
        )
        version_label.bind(on_press=on_version_tap)
        content.add_widget(version_label)

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

    def _show_dev_menu(self) -> None:
        """Show the hidden developer menu."""
        import json
        import shutil

        from kivy.metrics import dp
        from kivy.uix.label import Label
        from kivy.uix.modalview import ModalView

        # Dev menu styling constants
        DEV_BUTTON_WIDTH = 150
        DEV_BUTTON_HEIGHT = 32

        content = PopupContent(padding=[dp(PADDING_POPUP_LARGE[0]), dp(PADDING_POPUP_LARGE[1])])
        title = Label(
            text='Developer Menu',
            font_name='DMSans',
            font_size='14sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=dp(24)
        )
        content.add_widget(title)

        status_label = Label(
            text='',
            font_name='DMSans',
            font_size='10sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=dp(60),
            halign='center',
            valign='top'
        )
        status_label.bind(width=lambda *x: setattr(status_label, 'text_size', (status_label.width, None)))
        content.add_widget(status_label)

        popup = None

        # Android: plyer save_file is not implemented, use ACTION_CREATE_DOCUMENT
        def _android_save_file(content_bytes: bytes, mime_type: str, filename: str) -> None:
            from android import activity as android_activity, mActivity

            request_code = 9001

            def on_result(req_code: int, result_code: int, intent_data: Any) -> None:
                android_activity.unbind(on_activity_result=on_result)
                if req_code != request_code:
                    return
                if result_code != -1 or intent_data is None:
                    status_label.text = 'Export cancelled'
                    return
                try:
                    uri = intent_data.getData()
                    resolver = mActivity.getContentResolver()
                    stream = resolver.openOutputStream(uri)
                    stream.write(content_bytes)
                    stream.flush()
                    stream.close()
                    status_label.text = f'Exported {filename}'
                except Exception as e:
                    status_label.text = f'Error saving: {e}'

            android_activity.bind(on_activity_result=on_result)
            save_intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
            save_intent.addCategory(Intent.CATEGORY_OPENABLE)
            save_intent.setType(mime_type)
            save_intent.putExtra(Intent.EXTRA_TITLE, filename)
            mActivity.startActivityForResult(save_intent, request_code)

        def export_json(btn: Any) -> None:
            try:
                data = database.export_to_json()
                json_content = json.dumps(data, indent=2)
            except Exception as e:
                status_label.text = f'Error: {e}'
                return

            timestamp = date.today().isoformat()
            filename = f'yaque_export_{timestamp}.json'

            if platform == 'android':
                _android_save_file(json_content.encode('utf-8'), 'application/json', filename)
            else:
                from plyer import filechooser

                def handle_selection(selection: list) -> None:
                    if not selection:
                        status_label.text = 'Export cancelled'
                        return
                    try:
                        export_path = selection[0]
                        with open(export_path, 'w') as f:
                            f.write(json_content)
                        status_label.text = f'Exported to {os.path.basename(export_path)}'
                    except Exception as e:
                        status_label.text = f'Error: {e}'

                try:
                    filechooser.save_file(
                        on_selection=handle_selection,
                        filters=[('JSON files', '*.json')],
                        path=filename
                    )
                except Exception as e:
                    status_label.text = f'Error: {e}'

        def export_sqlite(btn: Any) -> None:
            db_path = database.get_db_path()
            if not db_path:
                status_label.text = 'Database not initialized'
                return

            timestamp = date.today().isoformat()
            filename = f'yaque_{timestamp}.db'

            if platform == 'android':
                try:
                    with open(db_path, 'rb') as f:
                        db_bytes = f.read()
                    _android_save_file(db_bytes, 'application/x-sqlite3', filename)
                except Exception as e:
                    status_label.text = f'Error: {e}'
            else:
                from plyer import filechooser

                def handle_selection(selection: list) -> None:
                    if not selection:
                        status_label.text = 'Export cancelled'
                        return
                    try:
                        export_path = selection[0]
                        shutil.copy2(db_path, export_path)
                        status_label.text = f'Exported to {os.path.basename(export_path)}'
                    except Exception as e:
                        status_label.text = f'Error: {e}'

                try:
                    filechooser.save_file(
                        on_selection=handle_selection,
                        filters=[('SQLite files', '*.db')],
                        path=filename
                    )
                except Exception as e:
                    status_label.text = f'Error: {e}'

        def show_stats(btn: Any) -> None:
            try:
                stats = database.get_generation_stats()
                overall = stats['overall']
                if overall['total'] == 0:
                    status_label.text = 'No generation data yet'
                    return

                avg_ms = int(overall['avg_time']) if overall['avg_time'] else 0
                avg_att = int(overall['avg_attempts']) if overall['avg_attempts'] else 0
                avg_diff = int(overall['avg_difficulty']) if overall['avg_difficulty'] else 0
                lines = [f"Total: {overall['total']} | Avg: {avg_ms}ms | Att: {avg_att} | Diff: {avg_diff}"]

                for size_stats in stats['by_size']:
                    avg = int(size_stats['avg_time']) if size_stats['avg_time'] else 0
                    att = int(size_stats['avg_attempts']) if size_stats['avg_attempts'] else 0
                    diff = int(size_stats['avg_difficulty']) if size_stats['avg_difficulty'] else 0
                    lines.append(f"{size_stats['size']}x{size_stats['size']}: {size_stats['count']} | {avg}ms | att:{att} | diff:{diff}")

                status_label.text = '\n'.join(lines)
            except Exception as e:
                status_label.text = f'Error: {e}'

        def import_json(btn: Any) -> None:
            from plyer import filechooser

            def handle_selection(selection: list) -> None:
                if not selection:
                    status_label.text = 'No file selected'
                    return
                try:
                    import_path = selection[0]
                    with open(import_path) as f:
                        data = json.load(f)
                    result = database.import_from_json(data)
                    status_label.text = f"Imported {result['puzzles']} puzzles, {result['plays']} plays"
                except Exception as e:
                    status_label.text = f'Error: {e}'

            try:
                filechooser.open_file(
                    on_selection=handle_selection,
                    filters=[('JSON files', '*.json')],
                    title='Select Yaque export file'
                )
            except Exception as e:
                status_label.text = f'Error opening picker: {e}'

        # Export JSON button
        json_btn = GrayRoundedButton(
            text='Export JSON',
            font_size='12sp',
            size_hint=(None, None),
            size=(dp(DEV_BUTTON_WIDTH), dp(DEV_BUTTON_HEIGHT)),
            pos_hint={'center_x': 0.5}
        )
        json_btn.bind(on_press=export_json)
        content.add_widget(json_btn)

        # Export SQLite button
        sqlite_btn = GrayRoundedButton(
            text='Export SQLite',
            font_size='12sp',
            size_hint=(None, None),
            size=(dp(DEV_BUTTON_WIDTH), dp(DEV_BUTTON_HEIGHT)),
            pos_hint={'center_x': 0.5}
        )
        sqlite_btn.bind(on_press=export_sqlite)
        content.add_widget(sqlite_btn)

        # Import JSON button
        import_btn = GrayRoundedButton(
            text='Import JSON',
            font_size='12sp',
            size_hint=(None, None),
            size=(dp(DEV_BUTTON_WIDTH), dp(DEV_BUTTON_HEIGHT)),
            pos_hint={'center_x': 0.5}
        )
        import_btn.bind(on_press=import_json)
        content.add_widget(import_btn)

        # Show Stats button
        stats_btn = GrayRoundedButton(
            text='Gen Stats',
            font_size='12sp',
            size_hint=(None, None),
            size=(dp(DEV_BUTTON_WIDTH), dp(DEV_BUTTON_HEIGHT)),
            pos_hint={'center_x': 0.5}
        )
        stats_btn.bind(on_press=show_stats)
        content.add_widget(stats_btn)

        # Cython solver toggle
        import game as game_module

        def _cython_label() -> str:
            return f'Cython: {"ON" if game_module._cy_solver is not None else "OFF"}'

        def toggle_cython(btn: Any) -> None:
            if game_module._cy_solver is not None:
                game_module._cy_solver_saved = game_module._cy_solver
                game_module._cy_solver = None
            else:
                game_module._cy_solver = getattr(game_module, '_cy_solver_saved', None)
                if game_module._cy_solver is None:
                    try:
                        import solver as cy_solver
                        game_module._cy_solver = cy_solver
                    except ImportError:
                        status_label.text = 'Cython module not built'
                        return
            btn.text = _cython_label()
            status_label.text = ''

        cython_btn = GrayRoundedButton(
            text=_cython_label(),
            font_size='12sp',
            size_hint=(None, None),
            size=(dp(DEV_BUTTON_WIDTH), dp(DEV_BUTTON_HEIGHT)),
            pos_hint={'center_x': 0.5}
        )
        cython_btn.bind(on_press=toggle_cython)
        content.add_widget(cython_btn)

        # Close button
        close_btn = GrayRoundedButton(
            text='Close',
            font_size='12sp',
            size_hint=(None, None),
            size=(dp(DEV_BUTTON_WIDTH), dp(DEV_BUTTON_HEIGHT)),
            pos_hint={'center_x': 0.5}
        )
        content.add_widget(close_btn)

        popup = ModalView(
            size_hint=(0.85, 0.62),
            auto_dismiss=True,
            background_color=POPUP_BACKGROUND
        )
        popup.add_widget(content)
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    # -------------------------------------------------------------------------
    # App lifecycle
    # -------------------------------------------------------------------------

    def exit_app(self, instance: Any) -> None:
        App.get_running_app().stop()

    def on_stop(self) -> None:
        database.close_db()


if __name__ == "__main__":
    YaqueApp().run()
