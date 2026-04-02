from __future__ import annotations

import io
from datetime import date
from typing import Any

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.utils import platform

import database
import game_encoding
from ui_constants import (
    CLOCK_BEHIND,
    CLOCK_FAST,
    CLOCK_NORMAL,
    CLOCK_SLOW,
    GRAY_BUTTON_COLOR,
    GRAY_BUTTON_COLOR_DOWN,
    ICON_BTN_SIZE_LG,
    STYLES,
    SWIPE_DISTANCE_THRESHOLD,
    SWIPE_EDGE_THRESHOLD,
)
from widgets import (
    BackButton,
    BoardWidget,
    CaptionLabel,
    ClockLabel,
    GrayRoundedButton,
    IconButton,
    SolutionIndicator,
    TitleSmLabel,
    styled,
)


class GameScreen(Screen):
    def __init__(self, app: Any, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.app = app

        layout = styled(BoxLayout, 'game_layout')

        # Game title (Daily puzzle: date / Random)
        self.title_label = TitleSmLabel('')
        layout.add_widget(self.title_label)

        # Subtitle - shows "Unique solution!" as label or "X solutions" as clickable button
        self.subtitle_label = CaptionLabel('', **STYLES['subtitle_area'])
        layout.add_widget(self.subtitle_label)

        # Solutions button (replaces subtitle when multiple solutions)
        solutions_btn_anchor = styled(AnchorLayout, 'solutions_btn_area')
        self.solutions_text_btn = GrayRoundedButton(text='', **STYLES['solutions_btn'])
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
        top_bar = styled(BoxLayout, 'header_bar')
        self.clock_label = ClockLabel()
        top_bar.add_widget(self.clock_label)
        layout.add_widget(top_bar)

        # Best/average time stats (shown when 10+ completed games for this size)
        self.time_stats_label = CaptionLabel('', **STYLES['subtitle_area'])
        self.time_stats_label.opacity = 0
        layout.add_widget(self.time_stats_label)

        # Solution indicator (gray circles with golden indicator)
        self.solution_indicator = SolutionIndicator(**STYLES['indicator_area'])
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
        play_anchor = styled(AnchorLayout, 'play_area')
        play_anchor.add_widget(self.play_btn)
        layout.add_widget(play_anchor)

        # Game control buttons (undo, redo, reset)
        control_bar = styled(BoxLayout, 'control_bar')
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

        self.rate_btn = IconButton('star', label='Rate')
        self.rate_btn.bind(on_press=self.show_rating)
        self.rate_btn.opacity = 0
        self.rate_btn.disabled = True
        control_bar.add_widget(self.rate_btn)

        # Wrap in anchor layout to center
        control_anchor = styled(AnchorLayout, 'control_anchor')
        control_anchor.add_widget(control_bar)
        layout.add_widget(control_anchor)

        # Back button
        back_btn = BackButton()
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
        self._hit_me_mode = False

        # Wake lock to prevent screen sleep during gameplay
        self._screen_on = False

    def _keep_screen_on(self, on: bool) -> None:
        """Keep screen on (prevent sleep) while playing."""
        if self._screen_on == on:
            return
        self._screen_on = on

        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
                activity = PythonActivity.mActivity

                def set_flag() -> None:
                    window = activity.getWindow()
                    if on:
                        window.addFlags(LayoutParams.FLAG_KEEP_SCREEN_ON)
                    else:
                        window.clearFlags(LayoutParams.FLAG_KEEP_SCREEN_ON)

                # Must run on UI thread
                activity.runOnUiThread(autoclass('java.lang.Runnable')(set_flag))
            except Exception as e:
                print(f"Failed to set screen wake lock: {e}")
        else:
            # Desktop fallback (no-op, but could use platform-specific APIs)
            pass

    def set_game(self, game: Any, daily_date: date | None = None, from_calendar: bool = False, from_logbook: bool = False, strategy: str | None = None) -> None:
        self.game = game
        self.daily_date = daily_date
        self.from_calendar = from_calendar
        self.from_logbook = from_logbook

        # Clear state from previous game
        self._hit_me_mode = False
        self.subtitle_label.text = ''
        self.subtitle_label.opacity = 0
        self.solutions_text_btn.text = ''
        self.solutions_text_btn.opacity = 0
        self.solutions_text_btn.disabled = True
        self.all_solutions = []
        self.current_solution_index = 0
        self.showing_solutions = False
        self.solution_indicator.opacity = 0

        # Show best/average time stats if 10+ completed games for this size
        self._update_time_stats(game.size)

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

        # Calculate difficulty score if not already set
        difficulty_score = getattr(game, 'difficulty_score', None)
        if difficulty_score is None and hasattr(game, 'calculate_difficulty'):
            difficulty_score = game.calculate_difficulty()

        self.puzzle_id = database.save_puzzle(
            code=code,
            size=game.size,
            daily_date=daily_date_str,
            seed=getattr(game, 'seed', None),
            generation_time_ms=getattr(game, 'generation_time_ms', None),
            num_solutions=getattr(game, 'num_solutions', None),
            kingdom_strategy=strategy,
            generation_attempts=getattr(game, 'attempts', None),
            difficulty_score=difficulty_score
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

        # Update clock display and reset color
        self._update_clock_display()
        self.clock_label.color = CLOCK_NORMAL
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

        # "Hit Me" — generate a new random game with same params
        if self._hit_me_mode:
            from popups import _last_random_options
            self._hit_me_mode = False
            self.app._start_random_game_with_options(
                size=_last_random_options['size'],
                strategy=_last_random_options['strategy'],
                max_solutions=_last_random_options['max_solutions'],
                queen_placement=_last_random_options['queen_placement'],
            )
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
            self._keep_screen_on(False)
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
                self._keep_screen_on(True)

        self.board.draw_board()

    def _tick(self, dt: float) -> None:
        self.elapsed_time += 1
        self._update_clock_display()
        self._update_clock_color()

    def _update_clock_display(self) -> None:
        minutes = self.elapsed_time // 60
        seconds = self.elapsed_time % 60
        self.clock_label.text = f'{minutes:02d}:{seconds:02d}'

    def _update_clock_color(self) -> None:
        """Update clock color based on elapsed time vs best/average."""
        if self._best_secs is None:
            return
        if self.elapsed_time <= self._best_secs:
            self.clock_label.color = CLOCK_FAST
        elif self.elapsed_time <= self._avg_secs:
            self.clock_label.color = CLOCK_SLOW
        else:
            self.clock_label.color = CLOCK_BEHIND

    def _update_time_stats(self, size: int) -> None:
        """Show best/average times if 10+ completed games for this size."""
        stats = database.get_time_stats_by_size().get(size)
        if not stats or stats['play_count'] < 10:
            self.time_stats_label.text = ''
            self.time_stats_label.opacity = 0
            self._best_secs = None
            self._avg_secs = None
            return
        self._best_secs = stats['best_time'] // 1000
        self._avg_secs = stats['avg_time'] // 1000
        best = self._format_duration(stats['best_time'])
        avg = self._format_duration(stats['avg_time'])
        self.time_stats_label.text = f'Best {best}  ·  Avg {avg}'
        self.time_stats_label.opacity = 1

    @staticmethod
    def _format_duration(ms: int | None) -> str:
        if not ms:
            return '-'
        secs = ms // 1000
        return f'{secs // 60}:{secs % 60:02d}'

    def on_puzzle_solved(self) -> None:
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

        # Release wake lock when solved
        self._keep_screen_on(False)

        # Record completion in database
        if self.play_id is not None:
            # Save final board state before completing
            encoded_state = game_encoding.encode_board_state(self.board.cell_marks)
            database.save_game_state(self.play_id, self.elapsed_time, encoded_state)
            duration_ms = self.elapsed_time * 1000
            database.complete_play(self.play_id, duration_ms)

        # Keep board visible when solved
        self.is_playing = False
        self.qr_image.opacity = 0

        if self.daily_date:
            self.play_btn.set_icon('queen', 'Solved!')
            self.play_btn.disabled = True
            self._hit_me_mode = False
        else:
            self.play_btn.set_icon('dice', 'Hit Me!')
            self.play_btn.disabled = False
            self._hit_me_mode = True

        # Show rate button
        self.rate_btn.opacity = 1
        self.rate_btn.disabled = False

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
        self._keep_screen_on(False)
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
        self.clock_label.color = CLOCK_NORMAL

        # Reset play tracking (new play will start when user presses play)
        self.play_id = None

        # Return to initial paused state
        self._keep_screen_on(False)
        self._hit_me_mode = False
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

        # Hide rate button
        self.rate_btn.opacity = 0
        self.rate_btn.disabled = True

        self.board.draw_board()

    def on_cell_click(self, row: int, col: int) -> None:
        pass  # Can add debug logging here if needed

    def show_rating(self, instance: Any) -> None:
        """Show a simple rating popup."""
        from widgets import ButtonRow, Popup, PopupContent, SmallRoundedButton, TitleLabel

        content = PopupContent()
        content.add_widget(TitleLabel('Rate this puzzle'))

        stars_row = ButtonRow()

        def make_rate_callback(rating: int) -> Any:
            def callback(btn: Any) -> None:
                if self.play_id:
                    database.rate_play(self.play_id, rating)
                popup.dismiss()
            return callback

        for i in range(1, 6):
            star_btn = SmallRoundedButton(
                text='[font=Stars]' + '★' * i + '[/font]',
                bg_color=GRAY_BUTTON_COLOR,
                bg_color_down=GRAY_BUTTON_COLOR_DOWN,
                color=STYLES['rating_cell']['color'],
            )
            star_btn.bind(on_press=make_rate_callback(i))
            stars_row.add_widget(star_btn)

        content.add_widget(stars_row)
        popup = Popup(content, height=140)
        popup.open()

    # Swipe from left edge to go back (Android)
    def on_touch_down(self, touch: Any) -> bool:
        if platform == 'android' and touch.x < dp(SWIPE_EDGE_THRESHOLD):
            # Detect touch starting near left edge
            touch.ud['swipe_from_edge'] = True
            touch.ud['start_x'] = touch.x
        return super().on_touch_down(touch)

    def on_touch_up(self, touch: Any) -> bool:
        if platform == 'android' and touch.ud.get('swipe_from_edge') and touch.x - touch.ud.get('start_x', 0) > dp(SWIPE_DISTANCE_THRESHOLD):
            # Swiped right from left edge - go back
            self.go_back(None)
            return True
        return super().on_touch_up(touch)
