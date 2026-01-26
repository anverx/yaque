import threading
import calendar
import io
import tempfile
import os
from datetime import date, timedelta
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.utils import platform
from kivy.core.clipboard import Clipboard

from game import Game, get_daily_game
from board_widget import BoardWidget

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
    Window.size = (400, 700)  # Vertical phone-like aspect ratio

# Light background
Window.clearcolor = (0.95, 0.95, 0.95, 1)


class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Solid background
        with layout.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self._bg = Rectangle(pos=layout.pos, size=layout.size)
        layout.bind(pos=self._update_bg, size=self._update_bg)

        # Splash screen image
        splash = Image(
            source='assets/images/splashscreen.jpg',
            allow_stretch=True,
            keep_ratio=True
        )
        layout.add_widget(splash)

        # Loading text
        self.status_label = Label(
            text='Loading...',
            font_size='20sp',
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.status_label)

        self.add_widget(layout)

    def _update_bg(self, instance, value):
        self._bg.pos = instance.pos
        self._bg.size = instance.size

    def set_status(self, text):
        self.status_label.text = text


class MainMenuScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Title
        layout.add_widget(Label(
            text='Yaque',
            font_size='48sp',
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=100
        ))

        # Daily puzzles section
        layout.add_widget(Label(
            text="Today's Puzzles",
            font_size='24sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=50
        ))

        daily_buttons = BoxLayout(size_hint_y=None, height=60, spacing=10)
        for size in [6, 7, 8]:
            btn = Button(text=f'{size}x{size}', font_size='20sp')
            btn.bind(on_press=lambda x, s=size: self.app.start_daily_game(s))
            daily_buttons.add_widget(btn)
        layout.add_widget(daily_buttons)

        # Spacer
        layout.add_widget(BoxLayout(size_hint_y=0.3))

        # Calendar button
        calendar_btn = Button(
            text='Calendar',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        calendar_btn.bind(on_press=self.app.show_calendar)
        layout.add_widget(calendar_btn)

        # Random game button
        random_btn = Button(
            text='Random Game',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        random_btn.bind(on_press=self.app.start_random_game)
        layout.add_widget(random_btn)

        # Load shared puzzle button
        load_btn = Button(
            text='Load Shared Puzzle',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        load_btn.bind(on_press=self.app.show_load_popup)
        layout.add_widget(load_btn)

        # Spacer
        layout.add_widget(BoxLayout(size_hint_y=0.3))

        # Exit button
        exit_btn = Button(
            text='Exit',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        exit_btn.bind(on_press=self.app.exit_app)
        layout.add_widget(exit_btn)

        self.add_widget(layout)


class CalendarScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.current_year = date.today().year
        self.current_month = date.today().month

        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Header with month/year and navigation
        header = BoxLayout(size_hint_y=None, height=50, spacing=10)

        prev_btn = Button(text='<', font_size='24sp', size_hint_x=None, width=50)
        prev_btn.bind(on_press=self.prev_month)
        header.add_widget(prev_btn)

        self.month_label = Label(
            text='',
            font_size='24sp',
            color=(0, 0, 0, 1)
        )
        header.add_widget(self.month_label)

        next_btn = Button(text='>', font_size='24sp', size_hint_x=None, width=50)
        next_btn.bind(on_press=self.next_month)
        header.add_widget(next_btn)

        self.main_layout.add_widget(header)

        # Day labels
        days_header = GridLayout(cols=7, size_hint_y=None, height=30, spacing=2)
        for day_name in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']:
            days_header.add_widget(Label(
                text=day_name,
                font_size='14sp',
                color=(0.3, 0.3, 0.3, 1)
            ))
        self.main_layout.add_widget(days_header)

        # Calendar grid
        self.calendar_grid = GridLayout(cols=7, spacing=2, size_hint_y=None)
        self.calendar_grid.bind(minimum_height=self.calendar_grid.setter('height'))
        self.main_layout.add_widget(self.calendar_grid)

        # Spacer
        self.main_layout.add_widget(BoxLayout())

        # Back button
        back_btn = Button(
            text='Back to Menu',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        back_btn.bind(on_press=lambda x: setattr(self.app.sm, 'current', 'menu'))
        self.main_layout.add_widget(back_btn)

        self.add_widget(self.main_layout)
        self.refresh_calendar()

    def prev_month(self, instance):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.refresh_calendar()

    def next_month(self, instance):
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

    def refresh_calendar(self):
        self.month_label.text = f'{calendar.month_name[self.current_month]} {self.current_year}'
        self.calendar_grid.clear_widgets()

        today = date.today()
        cal = calendar.Calendar(firstweekday=0)  # Monday first

        for day in cal.itermonthdays(self.current_year, self.current_month):
            if day == 0:
                # Empty cell
                self.calendar_grid.add_widget(Label(text='', size_hint_y=None, height=50))
            else:
                day_date = date(self.current_year, self.current_month, day)
                btn = Button(
                    text=str(day),
                    font_size='18sp',
                    size_hint_y=None,
                    height=50
                )
                # Disable future dates
                if day_date > today:
                    btn.disabled = True
                    btn.opacity = 0.5
                else:
                    btn.bind(on_press=lambda x, d=day_date: self.select_date(d))
                    # Highlight today
                    if day_date == today:
                        btn.background_color = (0.6, 0.8, 1, 1)
                self.calendar_grid.add_widget(btn)

    def select_date(self, selected_date):
        self.app.show_date_puzzles(selected_date)


class DatePuzzlesScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.selected_date = None

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Date label
        self.date_label = Label(
            text='',
            font_size='24sp',
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.date_label)

        # Puzzle buttons
        layout.add_widget(Label(
            text='Select Puzzle Size',
            font_size='20sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=40
        ))

        self.puzzle_buttons = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=200,
            spacing=10
        )
        for size in [6, 7, 8]:
            btn = Button(text=f'{size}x{size}', font_size='24sp')
            btn.bind(on_press=lambda x, s=size: self.start_puzzle(s))
            self.puzzle_buttons.add_widget(btn)
        layout.add_widget(self.puzzle_buttons)

        # Spacer
        layout.add_widget(BoxLayout())

        # Back button
        back_btn = Button(
            text='Back to Calendar',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        back_btn.bind(on_press=lambda x: setattr(self.app.sm, 'current', 'calendar'))
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def set_date(self, selected_date):
        self.selected_date = selected_date
        if selected_date == date.today():
            self.date_label.text = "Today's Puzzles"
        else:
            self.date_label.text = selected_date.strftime('%B %d, %Y')

    def start_puzzle(self, size):
        if self.selected_date:
            self.app.start_daily_game(size, self.selected_date)


class GameScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Top area with clock
        top_bar = BoxLayout(size_hint_y=None, height=80)
        self.clock_label = Label(
            text='00:00',
            font_size='48sp',
            color=(0, 0, 0, 1)
        )
        top_bar.add_widget(self.clock_label)
        layout.add_widget(top_bar)

        # Center area - will hold the board
        self.board_container = AnchorLayout(anchor_x='center', anchor_y='center')
        self.board_container.bind(size=self._resize_board)
        layout.add_widget(self.board_container)

        # Bottom area with game buttons
        bottom_bar = BoxLayout(size_hint_y=None, height=50, spacing=5)

        undo_btn = Button(text='Undo')
        undo_btn.bind(on_press=lambda x: self.board.undo() if self.board else None)
        bottom_bar.add_widget(undo_btn)

        redo_btn = Button(text='Redo')
        redo_btn.bind(on_press=lambda x: self.board.redo() if self.board else None)
        bottom_bar.add_widget(redo_btn)

        reset_btn = Button(text='Reset')
        reset_btn.bind(on_press=lambda x: self.board.reset() if self.board else None)
        bottom_bar.add_widget(reset_btn)

        layout.add_widget(bottom_bar)

        # Bottom buttons
        nav_bar = BoxLayout(size_hint_y=None, height=50, spacing=5)

        menu_btn = Button(text='Menu')
        menu_btn.bind(on_press=self.go_to_menu)
        nav_bar.add_widget(menu_btn)

        self.share_btn = Button(text='Share')
        self.share_btn.bind(on_press=self.share_game)
        nav_bar.add_widget(self.share_btn)

        show_solution_btn = Button(text='Solution')
        show_solution_btn.bind(on_press=self.toggle_solution)
        nav_bar.add_widget(show_solution_btn)

        layout.add_widget(nav_bar)

        self.add_widget(layout)

        # Game state
        self.game = None
        self.board = None
        self.elapsed_time = 0
        self.timer_event = None

    def set_game(self, game):
        self.game = game

        # Remove old board if exists
        if self.board:
            self.board_container.remove_widget(self.board)

        # Create new board
        self.board = BoardWidget(
            kingdoms=game.kingdoms,
            queens=game.queens,
            on_cell_click=self.on_cell_click,
            on_solved=self.on_puzzle_solved,
            size_hint=(None, None)
        )
        self.board_container.add_widget(self.board)
        self._resize_board(self.board_container, self.board_container.size)

        # Start the clock
        self.elapsed_time = 0
        self._update_clock_display()
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self._tick, 1)

    def _tick(self, dt):
        self.elapsed_time += 1
        self._update_clock_display()

    def _update_clock_display(self):
        minutes = self.elapsed_time // 60
        seconds = self.elapsed_time % 60
        self.clock_label.text = f'{minutes:02d}:{seconds:02d}'

    def on_puzzle_solved(self):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

    def _resize_board(self, container, size):
        if not self.board:
            return
        board_size = min(size[0], size[1]) - 20
        self.board.size = (board_size, board_size)

    def toggle_solution(self, instance):
        if not self.board:
            return
        self.board.show_solution = not self.board.show_solution
        self.board.draw_board()

    def go_to_menu(self, instance):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        self.app.sm.current = 'menu'

    def share_game(self, instance):
        if not self.game:
            return
        code = self.game.encode()
        share_url = f"yaque://start?game={code}"
        self.app.show_share_popup(share_url, code)

    def on_cell_click(self, row, col):
        pass  # Can add debug logging here if needed


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

    def _go_to_menu(self, dt):
        self.sm.current = 'menu'

    def start_daily_game(self, size, puzzle_date=None):
        if puzzle_date is None:
            puzzle_date = date.today()
        self.splash_screen.set_status(f'Generating {size}x{size} puzzle...')
        self.sm.current = 'splash'

        def generate():
            game = get_daily_game(puzzle_date, size, max_solutions=4)
            Clock.schedule_once(lambda dt: self._on_game_ready(game))

        threading.Thread(target=generate, daemon=True).start()

    def start_random_game(self, instance):
        self.splash_screen.set_status('Finding the perfect puzzle...')
        self.sm.current = 'splash'

        def generate():
            game = Game(7, max_solutions=1)
            Clock.schedule_once(lambda dt: self._on_game_ready(game))

        threading.Thread(target=generate, daemon=True).start()

    def _on_game_ready(self, game):
        self.game_screen.set_game(game)
        self.sm.current = 'game'

    def show_calendar(self, instance):
        self.sm.current = 'calendar'

    def show_date_puzzles(self, selected_date):
        self.date_puzzles_screen.set_date(selected_date)
        self.sm.current = 'date_puzzles'

    def show_share_popup(self, share_url, code):
        import qrcode

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(share_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Save to bytes buffer and load as Kivy texture
        buf = io.BytesIO()
        qr_img.save(buf, format='PNG')
        buf.seek(0)
        core_img = CoreImage(buf, ext='png')

        # Build popup content
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # QR code image
        qr_widget = Image(texture=core_img.texture, size_hint_y=None, height=250)
        content.add_widget(qr_widget)

        # URL label (selectable via TextInput)
        url_input = TextInput(
            text=share_url,
            font_size='12sp',
            size_hint_y=None,
            height=50,
            readonly=True,
            multiline=False
        )
        content.add_widget(url_input)

        # Status label for copy feedback
        status_label = Label(
            text='',
            font_size='14sp',
            color=(0.2, 0.6, 0.2, 1),
            size_hint_y=None,
            height=25
        )
        content.add_widget(status_label)

        # Buttons
        buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)

        def copy_url(btn):
            Clipboard.copy(share_url)
            status_label.text = 'URL copied!'
            Clock.schedule_once(lambda dt: setattr(status_label, 'text', ''), 2)

        def copy_code(btn):
            Clipboard.copy(code)
            status_label.text = 'Code copied!'
            Clock.schedule_once(lambda dt: setattr(status_label, 'text', ''), 2)

        copy_url_btn = Button(text='Copy URL')
        copy_url_btn.bind(on_press=copy_url)
        buttons.add_widget(copy_url_btn)

        copy_code_btn = Button(text='Copy Code')
        copy_code_btn.bind(on_press=copy_code)
        buttons.add_widget(copy_code_btn)

        close_btn = Button(text='Close')
        buttons.add_widget(close_btn)

        content.add_widget(buttons)

        popup = Popup(
            title='Share Puzzle',
            content=content,
            size_hint=(0.9, 0.75),
            auto_dismiss=True
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_load_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Instructions
        content.add_widget(Label(
            text='Paste puzzle code:',
            font_size='16sp',
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=30
        ))

        # Text input
        text_input = TextInput(
            multiline=False,
            font_size='16sp',
            size_hint_y=None,
            height=50
        )
        content.add_widget(text_input)

        # Error label
        error_label = Label(
            text='',
            font_size='14sp',
            color=(0.8, 0.2, 0.2, 1),
            size_hint_y=None,
            height=30
        )
        content.add_widget(error_label)

        # Buttons
        buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)

        def load_puzzle(btn):
            text = text_input.text.strip()
            if not text:
                error_label.text = 'Please enter a code or URL'
                return
            # Extract code from URL if needed
            code = text
            if text.startswith('yaque://'):
                # Parse URL: yaque://start?game=CODE
                if '?game=' in text:
                    code = text.split('?game=')[-1]
                elif '?g=' in text:
                    code = text.split('?g=')[-1]
            try:
                game = Game.from_code(code)
                popup.dismiss()
                self._on_game_ready(game)
            except Exception as e:
                error_label.text = 'Invalid puzzle code'

        def paste_clipboard(btn):
            text_input.text = Clipboard.paste() or ''

        paste_btn = Button(text='Paste')
        paste_btn.bind(on_press=paste_clipboard)
        buttons.add_widget(paste_btn)

        load_btn = Button(text='Load')
        load_btn.bind(on_press=load_puzzle)
        buttons.add_widget(load_btn)

        cancel_btn = Button(text='Cancel')
        buttons.add_widget(cancel_btn)

        content.add_widget(buttons)

        popup = Popup(
            title='Load Shared Puzzle',
            content=content,
            size_hint=(0.9, 0.4),
            auto_dismiss=False
        )
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def exit_app(self, instance):
        App.get_running_app().stop()


if __name__ == "__main__":
    YaqueApp().run()
