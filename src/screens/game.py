import io

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage

from board_widget import BoardWidget


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

        # Center area - will hold the board and QR overlay
        self.board_container = AnchorLayout(anchor_x='center', anchor_y='center')
        self.board_container.bind(size=self._resize_board)
        layout.add_widget(self.board_container)

        # QR code overlay (shown when paused)
        self.qr_image = Image(size_hint=(None, None), opacity=0)
        self.board_container.add_widget(self.qr_image)

        # Bottom area with game buttons
        bottom_bar = BoxLayout(size_hint_y=None, height=50, spacing=5)

        # Play/Pause button
        self.play_btn = Button(text='Play')
        self.play_btn.bind(on_press=self.toggle_play_pause)
        bottom_bar.add_widget(self.play_btn)

        undo_btn = Button(text='Undo')
        undo_btn.bind(on_press=lambda x: self.board.undo() if self.board and not self.board.hidden else None)
        bottom_bar.add_widget(undo_btn)

        redo_btn = Button(text='Redo')
        redo_btn.bind(on_press=lambda x: self.board.redo() if self.board and not self.board.hidden else None)
        bottom_bar.add_widget(redo_btn)

        reset_btn = Button(text='Reset')
        reset_btn.bind(on_press=self.reset_game)
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
        self.is_playing = False

    def set_game(self, game):
        self.game = game

        # Remove old board if exists
        if self.board:
            self.board_container.remove_widget(self.board)

        # Create new board (starts hidden)
        self.board = BoardWidget(
            kingdoms=game.kingdoms,
            queens=game.queens,
            on_cell_click=self.on_cell_click,
            on_solved=self.on_puzzle_solved,
            size_hint=(None, None)
        )
        # Insert board behind QR overlay
        self.board_container.add_widget(self.board, index=1)
        self._resize_board(self.board_container, self.board_container.size)

        # Generate QR code for sharing
        self._generate_qr_code()

        # Reset timer but don't start yet
        self.elapsed_time = 0
        self._update_clock_display()
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

        # Start in paused state (no QR until first pause)
        self.is_playing = False
        self.board.hidden = True
        self.play_btn.text = 'Play'
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
            self.play_btn.text = 'Play'
            self.qr_image.opacity = 1
            if self.timer_event:
                self.timer_event.cancel()
                self.timer_event = None
        else:
            # Play
            self.is_playing = True
            self.board.hidden = False
            self.play_btn.text = 'Pause'
            self.qr_image.opacity = 0
            if not self.board.solved:
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
        # Keep board visible when solved
        self.is_playing = False
        self.play_btn.text = 'Solved!'
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

    def go_to_menu(self, instance):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        self.is_playing = False
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

        # Return to initial paused state
        self.is_playing = False
        self.board.hidden = True
        self.board.solved = False
        self.play_btn.text = 'Play'
        self.play_btn.disabled = False
        self.qr_image.opacity = 0
        self.board.draw_board()

    def on_cell_click(self, row, col):
        pass  # Can add debug logging here if needed
