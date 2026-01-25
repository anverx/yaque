import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform

from game import Game
from board_widget import BoardWidget

# Set window mode before app starts
if platform in ('android', 'ios'):
    Window.fullscreen = 'auto'
else:
    Window.size = (400, 700)  # Vertical phone-like aspect ratio

# Light background
Window.clearcolor = (0.95, 0.95, 0.95, 1)


class YaqueApp(App):
    def build(self):
        self.game = None
        self.board = None
        self.elapsed_time = 0
        self.timer_event = None

        # Main vertical layout
        self.root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Top area with clock
        top_bar = BoxLayout(size_hint_y=None, height=80)
        self.clock_label = Label(
            text='00:00',
            font_size='48sp',
            color=(0, 0, 0, 1)
        )
        top_bar.add_widget(self.clock_label)
        self.root.add_widget(top_bar)

        # Center area - will hold the board
        self.board_container = AnchorLayout(anchor_x='center', anchor_y='center')
        self.board_container.bind(size=self._resize_board)
        self.root.add_widget(self.board_container)

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

        self.root.add_widget(bottom_bar)

        # Bottom buttons
        debug_bar = BoxLayout(size_hint_y=None, height=50, spacing=5)

        new_game_btn = Button(text='New Game')
        new_game_btn.bind(on_press=self.new_game)
        debug_bar.add_widget(new_game_btn)

        show_solution_btn = Button(text='Show Solution')
        show_solution_btn.bind(on_press=self.toggle_solution)
        debug_bar.add_widget(show_solution_btn)

        self.root.add_widget(debug_bar)

        # Show loading and start generation
        self._show_loading()
        threading.Thread(target=self._generate_game, daemon=True).start()

        return self.root

    def _show_loading(self):
        self.loading = ModalView(size_hint=(0.8, 0.3), auto_dismiss=False)
        loading_content = BoxLayout(orientation='vertical', padding=20)
        loading_content.add_widget(Label(
            text='Finding the perfect puzzle...',
            font_size='20sp',
            color=(0, 0, 0, 1)
        ))
        self.loading.add_widget(loading_content)
        self.loading.open()

    def _generate_game(self):
        # Run in background thread
        self.game = Game(7, max_solutions=1)
        # Schedule UI update on main thread
        Clock.schedule_once(self._on_game_ready)

    def _on_game_ready(self, dt):
        self.loading.dismiss()

        # Create and add the board
        self.board = BoardWidget(
            kingdoms=self.game.kingdoms,
            queens=self.game.queens,
            on_cell_click=self.on_cell_click,
            on_solved=self.on_puzzle_solved,
            size_hint=(None, None)
        )
        self.board_container.add_widget(self.board)

        # Trigger resize
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
        # Stop the clock
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

    def new_game(self, instance):
        # Stop the clock
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        # Remove current board
        if self.board:
            self.board_container.remove_widget(self.board)
            self.board = None
        # Show loading and generate new game
        self._show_loading()
        threading.Thread(target=self._generate_game, daemon=True).start()

    def toggle_solution(self, instance):
        if not self.board:
            return
        self.board.show_solution = not self.board.show_solution
        self.board.draw_board()

    def _resize_board(self, container, size):
        if not self.board:
            return
        # Keep board square, using the smaller dimension with some margin
        board_size = min(size[0], size[1]) - 20
        self.board.size = (board_size, board_size)

    def on_cell_click(self, row, col):
        k = self.game.kingdoms[row][col]
        is_queen = (row, col) in self.board.queen_set
        print(f"Clicked: ({row}, {col}) - Kingdom {k}" + (" - QUEEN" if is_queen else ""))


if __name__ == "__main__":
    YaqueApp().run()
