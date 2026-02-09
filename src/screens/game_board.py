from __future__ import annotations

import io
import os
from datetime import date
from typing import Any

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

from ui_constants import (
    INDICATOR_CURRENT, INDICATOR_OTHER,
    HEADER_HEIGHT, BUTTON_HEIGHT, SPACING_SM, SPACING_LG, SPACING_XL,
    ICON_BTN_SIZE, ICON_BTN_SIZE_LG, CONTROL_BAR_HEIGHT, PLAY_AREA_HEIGHT,
    INDICATOR_HEIGHT, INDICATOR_CIRCLE_SIZE, INDICATOR_SPACING,
    SUBTITLE_HEIGHT, SOLUTIONS_BTN_WIDTH, SOLUTIONS_BTN_HEIGHT,
    SOLUTIONS_BTN_AREA_HEIGHT, SWIPE_EDGE_THRESHOLD, SWIPE_DISTANCE_THRESHOLD,
    ICON_LABEL_HEIGHT, ICON_LABEL_TOTAL,
)
from widgets import (
    BoardWidget,
    GrayRoundedButton, FixedGrayRoundedButton, TitleSmLabel, CaptionLabel, ClockLabel, IconLabel,
)
import database
import game_encoding


# Path to icons directory
ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')


from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse


class SolutionIndicator(Widget):
    """Shows gray circles for each solution with a golden indicator for current."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.num_solutions = 0
        self.current_index = 0
        self.bind(pos=self._draw, size=self._draw)

    def set_solutions(self, num_solutions: int, current_index: int = 0) -> None:
        self.num_solutions = num_solutions
        self.current_index = current_index
        self._draw()

    def set_current(self, index: int) -> None:
        self.current_index = index
        self._draw()

    def _draw(self, *args: Any) -> None:
        self.canvas.clear()
        if self.num_solutions <= 1:
            return

        with self.canvas:
            # Calculate circle positions (centered)
            circle_size = dp(INDICATOR_CIRCLE_SIZE)
            spacing = dp(INDICATOR_SPACING)
            total_width = self.num_solutions * circle_size + (self.num_solutions - 1) * (spacing - circle_size)
            start_x = self.center_x - total_width / 2

            for i in range(self.num_solutions):
                cx = start_x + i * spacing
                cy = self.center_y - circle_size / 2

                if i == self.current_index:
                    Color(*INDICATOR_CURRENT)
                    Ellipse(pos=(cx, cy), size=(circle_size, circle_size))
                else:
                    Color(*INDICATOR_OTHER)
                    Ellipse(pos=(cx, cy), size=(circle_size, circle_size))


class IconButton(ButtonBehavior, BoxLayout):
    """A clickable image button with optional label."""
    def __init__(self, icon_name: str, size_dp: int = ICON_BTN_SIZE, label: str | None = None, **kwargs: Any) -> None:
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
            self.label = IconLabel(
                label,
                size_hint=(None, None),
                size=(dp(size_dp), dp(ICON_LABEL_HEIGHT)),
                halign='center'
            )
            self.label.bind(size=self.label.setter('text_size'))
            self.add_widget(self.label)
            self.size = (dp(size_dp), dp(size_dp + ICON_LABEL_TOTAL))
        else:
            self.size = (dp(size_dp), dp(size_dp))

    def set_icon(self, icon_name: str, label: str | None = None) -> None:
        """Change the icon and optionally the label."""
        self.icon_name = icon_name
        self.icon.source = os.path.join(ICONS_DIR, f'{icon_name}.png')
        if label and hasattr(self, 'label'):
            self.label.text = label


class GameScreen(Screen):
    def __init__(self, app: Any, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.app = app

        layout = BoxLayout(orientation='vertical', padding=dp(SPACING_LG), spacing=dp(SPACING_SM))

        # Game title (Daily puzzle: date / Random)
        self.title_label = TitleSmLabel('')
        layout.add_widget(self.title_label)

        # Subtitle - shows "Unique solution!" as label or "X solutions" as clickable button
        self.subtitle_label = CaptionLabel('', size_hint_y=None, height=dp(SUBTITLE_HEIGHT))
        layout.add_widget(self.subtitle_label)

        # Solutions button (replaces subtitle when multiple solutions)
        solutions_btn_anchor = AnchorLayout(size_hint_y=None, height=dp(SOLUTIONS_BTN_AREA_HEIGHT), anchor_x='center')
        self.solutions_text_btn = GrayRoundedButton(
            text='',
            size_hint=(None, None),
            size=(dp(SOLUTIONS_BTN_WIDTH), dp(SOLUTIONS_BTN_HEIGHT))
        )
        self.solutions_text_btn.bind(on_press=lambda x: self.toggle_solutions(x))
        self.solutions_text_btn.opacity = 0
        self.solutions_text_btn.disabled = True
        solutions_btn_anchor.add_widget(self.solutions_text_btn)
        layout.add_widget(solutions_btn_anchor)

        # Track solutions for cycling
        self.all_solutions = []
        self.current_solution_index = 0
        self.showing_solutions = False

        # Clock
        top_bar = BoxLayout(size_hint_y=None, height=dp(HEADER_HEIGHT))
        self.clock_label = ClockLabel()
        top_bar.add_widget(self.clock_label)
        layout.add_widget(top_bar)

        # Solution indicator (gray circles with golden indicator)
        self.solution_indicator = SolutionIndicator(size_hint_y=None, height=dp(INDICATOR_HEIGHT))
        self.solution_indicator.opacity = 0  # Hidden until solutions shown
        layout.add_widget(self.solution_indicator)

        # Center area - will hold the board, QR overlay, and play button
        self.board_container = AnchorLayout(anchor_x='center', anchor_y='center')
        self.board_container.bind(size=self._resize_board)
        layout.add_widget(self.board_container)

        # QR code overlay (shown when paused)
        self.qr_image = Image(size_hint=(None, None), opacity=0)
        self.board_container.add_widget(self.qr_image)

        # Play/Pause button - attached below the board
        self.play_btn = IconButton('play', size_dp=ICON_BTN_SIZE_LG, label='Play')
        self.play_btn.bind(on_press=self.toggle_play_pause)
        play_anchor = AnchorLayout(size_hint_y=None, height=dp(PLAY_AREA_HEIGHT), anchor_x='center')
        play_anchor.add_widget(self.play_btn)
        layout.add_widget(play_anchor)

        # Game control buttons (undo, redo, reset)
        control_bar = BoxLayout(size_hint=(None, None), height=dp(CONTROL_BAR_HEIGHT), spacing=dp(SPACING_XL))
        control_bar.bind(minimum_width=control_bar.setter('width'))

        undo_btn = IconButton('undo', label='Undo')
        undo_btn.bind(on_press=lambda x: self.board.undo() if self.board and not self.board.hidden else None)
        control_bar.add_widget(undo_btn)

        redo_btn = IconButton('redo', label='Redo')
        redo_btn.bind(on_press=lambda x: self.board.redo() if self.board and not self.board.hidden else None)
        control_bar.add_widget(redo_btn)

        reset_btn = IconButton('reset', label='Reset')
        reset_btn.bind(on_press=self.reset_game)
        control_bar.add_widget(reset_btn)

        self.share_btn = IconButton('share', label='Share')
        self.share_btn.bind(on_press=self.share_game)
        control_bar.add_widget(self.share_btn)

        # Wrap in anchor layout to center
        control_anchor = AnchorLayout(size_hint_y=None, height=dp(CONTROL_BAR_HEIGHT), anchor_x='center')
        control_anchor.add_widget(control_bar)
        layout.add_widget(control_anchor)

        # Back button
        back_btn = FixedGrayRoundedButton(text='Back')
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)

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

    def set_game(self, game: Any, daily_date: date | None = None, from_calendar: bool = False, from_logbook: bool = False, strategy: str | None = None) -> None:
        self.game = game
        self.daily_date = daily_date
        self.from_calendar = from_calendar
        self.from_logbook = from_logbook

        # Clear subtitle and solutions (will be set when solved)
        self.subtitle_label.text = ''
        self.subtitle_label.opacity = 0
        self.solutions_text_btn.text = ''
        self.solutions_text_btn.opacity = 0
        self.solutions_text_btn.disabled = True
        self.all_solutions = []
        self.current_solution_index = 0
        self.showing_solutions = False
        self.solution_indicator.opacity = 0

        # Set title
        if daily_date:
            self.title_label.text = f"Daily puzzle: {daily_date.strftime('%B %d, %Y')}"
        else:
            # Random game - show size and strategy
            strategy_names = {'classic': 'Classic', 'mixed': 'Mixed', 'jagged': 'Jagged'}
            strategy_label = strategy_names.get(strategy, '')
            if strategy_label:
                self.title_label.text = f"Random {game.size}x{game.size} ({strategy_label})"
            else:
                self.title_label.text = f"Random {game.size}x{game.size}"

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
            for row, col in game.queens:
                self.board.cell_marks[row][col] = 2  # MARK_QUEEN
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
            # Completed game - show crown, board hidden until tapped
            self.is_playing = False
            self.board.hidden = True
            self.board.solved = True
            self.play_btn.set_icon('queen', 'Solved!')
            self.play_btn.disabled = False  # Can tap to reveal
            self.qr_image.opacity = 0
            # Load solutions for completed puzzles
            self.all_solutions = self.game.find_all_solutions(max_count=100)
            self.current_solution_index = 0
            self.showing_solutions = False
            self.board.all_solutions = self.all_solutions
            self.board.current_solution_index = 0
            self.board.show_solution = False
            self._update_solution_subtitle()
        else:
            # Start in paused state (no QR until first pause)
            self.is_playing = False
            self.board.hidden = True
            self.play_btn.set_icon('play', 'Play')
            self.play_btn.disabled = False
            self.qr_image.opacity = 0
        self.board.draw_board()

    def _generate_qr_code(self) -> None:
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

    def toggle_play_pause(self, instance: Any) -> None:
        if not self.board:
            return

        # Special case: revealing a completed game
        if self.board.solved and self.board.hidden:
            self.board.hidden = False
            self.play_btn.disabled = True  # No more toggling after reveal
            self.qr_image.opacity = 0
            self.board.draw_board()
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

    def _tick(self, dt: float) -> None:
        self.elapsed_time += 1
        self._update_clock_display()

    def _update_clock_display(self) -> None:
        minutes = self.elapsed_time // 60
        seconds = self.elapsed_time % 60
        self.clock_label.text = f'{minutes:02d}:{seconds:02d}'

    def on_puzzle_solved(self) -> None:
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

        # Find all solutions and pass to board
        self.all_solutions = self.game.find_all_solutions(max_count=100)
        self.current_solution_index = 0
        self.showing_solutions = False
        self.board.all_solutions = self.all_solutions
        self.board.current_solution_index = 0
        self.board.show_solution = False  # Don't show solutions until button clicked

        # Update subtitle with solution count
        self._update_solution_subtitle()

    def _resize_board(self, container: Any, size: tuple[float, float]) -> None:
        if not self.board:
            return
        # Use 90% of available space for bigger margins
        board_size = min(size[0], size[1]) * 0.9
        self.board.size = (board_size, board_size)
        # QR code is 85% of board size
        qr_size = board_size * 0.85
        self.qr_image.size = (qr_size, qr_size)

    def _update_solution_subtitle(self) -> None:
        """Update the subtitle to show solution count."""
        num_solutions = len(self.all_solutions)
        if num_solutions == 1:
            self.subtitle_label.text = "Unique"
            self.subtitle_label.opacity = 1
            self.solutions_text_btn.opacity = 0
            self.solutions_text_btn.disabled = True
        else:
            self.subtitle_label.text = ''
            self.subtitle_label.opacity = 0
            self.solutions_text_btn.text = f"{num_solutions} solutions"
            self.solutions_text_btn.opacity = 1
            self.solutions_text_btn.disabled = False

    def toggle_solutions(self, instance: Any) -> None:
        """Toggle solution display or cycle to next solution."""
        if not self.board or not self.all_solutions:
            return

        if not self.showing_solutions:
            # First click - show solutions
            self.showing_solutions = True
            self.board.show_solution = True
            self.solution_indicator.opacity = 1
            self.solution_indicator.set_solutions(len(self.all_solutions), 0)
            self.board.draw_board()
        else:
            # Subsequent clicks - cycle through solutions
            self.current_solution_index = self.board.cycle_solution()
            self.solution_indicator.set_current(self.current_solution_index)

    def _save_game_state(self) -> None:
        """Save current game state to database (for daily puzzles)."""
        if self.play_id is not None and self.board and not self.board.solved:
            encoded_state = game_encoding.encode_board_state(self.board.cell_marks)
            database.save_game_state(self.play_id, self.elapsed_time, encoded_state)

    def go_back(self, instance: Any) -> None:
        """Go back to the previous screen (calendar, logbook, or menu)."""
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        self._save_game_state()
        self.is_playing = False
        if self.from_calendar:
            self.app.sm.current = 'calendar'
        elif self.from_logbook:
            self.app.sm.current = 'logbook'
        else:
            self.app.sm.current = 'menu'

    def share_game(self, instance: Any) -> None:
        if not self.game:
            return
        code = self.game.encode()
        share_url = f"yaque://start?game={code}"
        self.app.show_share_popup(share_url, code)

    def reset_game(self, instance: Any) -> None:
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

        # Hide solutions UI
        self.subtitle_label.text = ''
        self.subtitle_label.opacity = 0
        self.solutions_text_btn.opacity = 0
        self.solutions_text_btn.disabled = True
        self.solution_indicator.opacity = 0
        self.all_solutions = []
        self.showing_solutions = False
        self.board.draw_board()

    def on_cell_click(self, row: int, col: int) -> None:
        pass  # Can add debug logging here if needed

    # Swipe from left edge to go back (Android)
    def on_touch_down(self, touch: Any) -> bool:
        if platform == 'android':
            # Detect touch starting near left edge
            if touch.x < dp(SWIPE_EDGE_THRESHOLD):
                touch.ud['swipe_from_edge'] = True
                touch.ud['start_x'] = touch.x
        return super().on_touch_down(touch)

    def on_touch_up(self, touch: Any) -> bool:
        if platform == 'android' and touch.ud.get('swipe_from_edge'):
            # Check if swiped right sufficiently
            if touch.x - touch.ud.get('start_x', 0) > dp(SWIPE_DISTANCE_THRESHOLD):
                self.go_back(None)
                return True
        return super().on_touch_up(touch)
