import io
import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp, sp
from kivy.utils import platform

from board_widget import BoardWidget
import database
import game_encoding


# Path to icons directory
ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')


class IconButton(ButtonBehavior, BoxLayout):
    """A clickable image button with optional label."""
    def __init__(self, icon_name, size_dp=48, label=None, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.icon_name = icon_name
        self.size_hint = (None, None)

        # Icon
        self.icon = Image(
            source=os.path.join(ICONS_DIR, f'{icon_name}.png'),
            size_hint=(None, None),
            size=(dp(size_dp), dp(size_dp)),
            fit_mode='contain'
        )
        self.add_widget(self.icon)

        # Optional label
        if label:
            self.label = Label(
                text=label,
                font_name='DMSansBlack',
                font_size='9sp',
                color=(0.3, 0.3, 0.3, 1),
                size_hint=(None, None),
                size=(dp(size_dp), dp(12)),
                halign='center'
            )
            self.label.bind(size=self.label.setter('text_size'))
            self.add_widget(self.label)
            self.size = (dp(size_dp), dp(size_dp + 14))
        else:
            self.size = (dp(size_dp), dp(size_dp))

    def set_icon(self, icon_name, label=None):
        """Change the icon and optionally the label."""
        self.icon_name = icon_name
        self.icon.source = os.path.join(ICONS_DIR, f'{icon_name}.png')
        if label and hasattr(self, 'label'):
            self.label.text = label


class GameScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))

        # Game title (Daily puzzle: date / Random)
        self.title_label = Label(
            text='',
            font_name='DMSans',
            font_size='14sp',
            color=(0.4, 0.4, 0.4, 1),
            size_hint_y=None,
            height=dp(20)
        )
        layout.add_widget(self.title_label)

        # Clock
        top_bar = BoxLayout(size_hint_y=None, height=dp(50))
        self.clock_label = Label(
            text='00:00',
            font_name='DMSansBlack',
            font_size='36sp',
            color=(0, 0, 0, 1)
        )
        top_bar.add_widget(self.clock_label)
        layout.add_widget(top_bar)

        # Center area - will hold the board and QR overlay
        self.board_container = AnchorLayout(anchor_x='center', anchor_y='center')
        self.board_container.bind(size=self._resize_board)
        layout.add_widget(self.board_container)

        # QR code overlay (shown when paused)
        self.qr_image = Image(size_hint=(None, None), opacity=0)
        self.board_container.add_widget(self.qr_image)

        # Play/Pause button - large, centered, alone on its row
        self.play_btn = IconButton('play', size_dp=56, label='Play')
        self.play_btn.bind(on_press=self.toggle_play_pause)
        play_anchor = AnchorLayout(size_hint_y=None, height=dp(72), anchor_x='center')
        play_anchor.add_widget(self.play_btn)
        layout.add_widget(play_anchor)

        # Game control buttons (undo, redo, reset)
        control_bar = BoxLayout(size_hint=(None, None), height=dp(56), spacing=dp(16))
        control_bar.bind(minimum_width=control_bar.setter('width'))

        undo_btn = IconButton('undo', size_dp=40, label='Undo')
        undo_btn.bind(on_press=lambda x: self.board.undo() if self.board and not self.board.hidden else None)
        control_bar.add_widget(undo_btn)

        redo_btn = IconButton('redo', size_dp=40, label='Redo')
        redo_btn.bind(on_press=lambda x: self.board.redo() if self.board and not self.board.hidden else None)
        control_bar.add_widget(redo_btn)

        reset_btn = IconButton('reset', size_dp=40, label='Reset')
        reset_btn.bind(on_press=self.reset_game)
        control_bar.add_widget(reset_btn)

        # Auto-solve button (for testing celebration effect)
        auto_solve_btn = IconButton('queen', size_dp=40)
        auto_solve_btn.bind(on_press=self.auto_solve)
        control_bar.add_widget(auto_solve_btn)

        # Wrap in anchor layout to center
        control_anchor = AnchorLayout(size_hint_y=None, height=dp(56), anchor_x='center')
        control_anchor.add_widget(control_bar)
        layout.add_widget(control_anchor)

        # Navigation buttons (centered icons)
        nav_bar = BoxLayout(size_hint=(None, None), height=dp(56), spacing=dp(16))
        nav_bar.bind(minimum_width=nav_bar.setter('width'))

        menu_btn = IconButton('menu', size_dp=40, label='Menu')
        menu_btn.bind(on_press=self.go_back)
        nav_bar.add_widget(menu_btn)

        self.share_btn = IconButton('share', size_dp=40, label='Share')
        self.share_btn.bind(on_press=self.share_game)
        nav_bar.add_widget(self.share_btn)

        solution_btn = IconButton('solution', size_dp=40, label='Hint')
        solution_btn.bind(on_press=self.toggle_solution)
        nav_bar.add_widget(solution_btn)

        # Wrap in anchor layout to center
        nav_anchor = AnchorLayout(size_hint_y=None, height=dp(56), anchor_x='center')
        nav_anchor.add_widget(nav_bar)
        layout.add_widget(nav_anchor)

        self.add_widget(layout)

        # Game state
        self.game = None
        self.board = None
        self.elapsed_time = 0
        self.timer_event = None
        self.is_playing = False

        # Play tracking
        self.puzzle_id = None
        self.play_id = None
        self.daily_date = None  # Set if this is a daily puzzle

    def set_game(self, game, daily_date=None, from_calendar=False):
        self.game = game
        self.daily_date = daily_date
        self.from_calendar = from_calendar

        # Set title
        if daily_date:
            self.title_label.text = f"Daily puzzle: {daily_date.strftime('%B %d, %Y')}"
        else:
            self.title_label.text = "Random"

        # Save puzzle to database
        code = game.encode()
        daily_date_str = daily_date.isoformat() if daily_date else None
        self.puzzle_id = database.save_puzzle(
            code=code,
            size=game.size,
            daily_date=daily_date_str,
            seed=getattr(game, 'seed', None)
        )

        # Check for existing play to resume (only for daily puzzles)
        saved_play = None
        self.is_already_completed = False
        if daily_date:
            saved_play = database.get_latest_play(self.puzzle_id)

        if saved_play:
            self.play_id = saved_play['id']
            self.elapsed_time = saved_play.get('elapsed_seconds', 0) or 0
            self.is_already_completed = saved_play.get('completed', 0) == 1
            if self.is_already_completed:
                # Use duration_ms for completed puzzles
                duration_ms = saved_play.get('duration_ms', 0) or 0
                self.elapsed_time = duration_ms // 1000
        else:
            self.play_id = None
            self.elapsed_time = 0
            self.is_already_completed = False

        # Remove old board if exists
        if self.board:
            self.board_container.remove_widget(self.board)

        # Create new board (starts hidden)
        self.board = BoardWidget(
            kingdoms=game.kingdoms,
            queens=game.queens,
            on_cell_click=self.on_cell_click,
            on_solved=self.on_puzzle_solved,
            on_hidden_click=lambda: self.toggle_play_pause(None),
            size_hint=(None, None)
        )

        # Restore board state if resuming
        if saved_play and saved_play.get('board_state'):
            cell_marks = game_encoding.decode_board_state(saved_play['board_state'])
            self.board.cell_marks = cell_marks
            self.board.history = [cell_marks]
            self.board.history_index = 0
        elif self.is_already_completed:
            # For completed games without saved board state, show solution
            self.board.auto_solve()
            self.board.solved = True

        # Insert board behind QR overlay
        self.board_container.add_widget(self.board, index=1)
        self._resize_board(self.board_container, self.board_container.size)

        # Generate QR code for sharing
        self._generate_qr_code()

        # Update clock display
        self._update_clock_display()
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

        # Set initial state based on completion status
        if self.is_already_completed:
            # Show completed state - board visible, solved
            self.is_playing = False
            self.board.hidden = False
            self.board.solved = True
            self.play_btn.set_icon('queen', 'Solved!')
            self.play_btn.disabled = True
            self.qr_image.opacity = 0
        else:
            # Start in paused state (no QR until first pause)
            self.is_playing = False
            self.board.hidden = True
            self.play_btn.set_icon('play', 'Play')
            self.play_btn.disabled = False
            self.qr_image.opacity = 0
        self.board.draw_board()

    def _generate_qr_code(self):
        """Generate QR code for the current game."""
        import qrcode

        code = self.game.encode()
        share_url = f"yaque://start?game={code}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        qr.add_data(share_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert to Kivy texture
        buf = io.BytesIO()
        qr_img.save(buf, format='PNG')
        buf.seek(0)
        core_img = CoreImage(buf, ext='png')
        self.qr_image.texture = core_img.texture

    def toggle_play_pause(self, instance):
        if not self.board:
            return

        if self.is_playing:
            # Pause
            self.is_playing = False
            self.board.hidden = True
            self.play_btn.set_icon('play', 'Play')
            self.qr_image.opacity = 1
            if self.timer_event:
                self.timer_event.cancel()
                self.timer_event = None
            self._save_game_state()
        else:
            # Play
            self.is_playing = True
            self.board.hidden = False
            self.play_btn.set_icon('pause', 'Pause')
            self.qr_image.opacity = 0
            if not self.board.solved:
                # Start a new play session if not already started
                if self.play_id is None and self.puzzle_id is not None:
                    self.play_id = database.start_play(self.puzzle_id)
                self.timer_event = Clock.schedule_interval(self._tick, 1)

        self.board.draw_board()

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

        # Record completion in database
        if self.play_id is not None:
            # Save final board state before completing
            encoded_state = game_encoding.encode_board_state(self.board.cell_marks)
            database.save_game_state(self.play_id, self.elapsed_time, encoded_state)
            duration_ms = self.elapsed_time * 1000
            database.complete_play(self.play_id, duration_ms)

        # Keep board visible when solved
        self.is_playing = False
        self.play_btn.set_icon('queen', 'Solved!')  # Show queen icon when solved
        self.play_btn.disabled = True
        self.qr_image.opacity = 0

    def _resize_board(self, container, size):
        if not self.board:
            return
        # Use 90% of available space for bigger margins
        board_size = min(size[0], size[1]) * 0.9
        self.board.size = (board_size, board_size)
        # QR code is 85% of board size
        qr_size = board_size * 0.85
        self.qr_image.size = (qr_size, qr_size)

    def toggle_solution(self, instance):
        if not self.board:
            return
        self.board.show_solution = not self.board.show_solution
        self.board.draw_board()

    def _save_game_state(self):
        """Save current game state to database (for daily puzzles)."""
        if self.play_id is not None and self.board and not self.board.solved:
            encoded_state = game_encoding.encode_board_state(self.board.cell_marks)
            database.save_game_state(self.play_id, self.elapsed_time, encoded_state)

    def go_back(self, instance):
        """Go back to the previous screen (calendar or menu)."""
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        self._save_game_state()
        self.is_playing = False
        if self.from_calendar:
            self.app.sm.current = 'date_puzzles'
        else:
            self.app.sm.current = 'menu'

    def share_game(self, instance):
        if not self.game:
            return
        code = self.game.encode()
        share_url = f"yaque://start?game={code}"
        self.app.show_share_popup(share_url, code)

    def reset_game(self, instance):
        """Reset the game to initial state."""
        if not self.board:
            return

        # Reset board marks
        self.board.reset()

        # Stop timer and reset clock
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        self.elapsed_time = 0
        self._update_clock_display()

        # Reset play tracking (new play will start when user presses play)
        self.play_id = None

        # Return to initial paused state
        self.is_playing = False
        self.board.hidden = True
        self.board.solved = False
        self.play_btn.set_icon('play', 'Play')
        self.play_btn.disabled = False
        self.qr_image.opacity = 0
        self.board.draw_board()

    def auto_solve(self, instance):
        """Auto-solve the puzzle and play celebration (for testing)."""
        if not self.board:
            return

        # Make sure board is visible
        if self.board.hidden:
            self.is_playing = True
            self.board.hidden = False
            self.play_btn.set_icon('pause', 'Pause')
            self.qr_image.opacity = 0
            self.board.draw_board()

        # Stop timer
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

        # Auto-solve and celebrate
        self.board.auto_solve()
        self.play_btn.set_icon('queen', 'Solved!')
        self.play_btn.disabled = True

    def on_cell_click(self, row, col):
        pass  # Can add debug logging here if needed

    # Swipe from left edge to go back (Android)
    def on_touch_down(self, touch):
        if platform == 'android':
            # Detect touch starting near left edge (within 20dp)
            if touch.x < dp(20):
                touch.ud['swipe_from_edge'] = True
                touch.ud['start_x'] = touch.x
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if platform == 'android' and touch.ud.get('swipe_from_edge'):
            # Check if swiped right at least 100dp
            if touch.x - touch.ud.get('start_x', 0) > dp(100):
                self.go_back(None)
                return True
        return super().on_touch_up(touch)
