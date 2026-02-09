import io
import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.modalview import ModalView
from kivy.core.image import Image as CoreImage
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Rectangle, PushMatrix, PopMatrix, Rotate, Line
from kivy.metrics import dp

from game import Game
from ui_constants import (
    FONT_NAME,
    TEXT_DARK, TEXT_MEDIUM, TEXT_LIGHT, TEXT_HEADER, TEXT_WHITE, COLOR_WHITE,
    POPUP_BACKGROUND, INPUT_BACKGROUND, INPUT_HINT_COLOR,
    STATUS_SUCCESS, STATUS_ERROR, SPINNER_BORDER,
    DEFAULT_BUTTON_COLOR_DOWN, BUTTON_UNSELECTED
)
from widgets import RoundedButton, GrayRoundedButton

ICONS_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'icons')


def show_share_popup(share_url, code):
    """Show popup with QR code and copy buttons for sharing a puzzle."""
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
    content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))

    # Title
    content.add_widget(Label(
        text='Share Puzzle',
        font_name=FONT_NAME,
        font_size='18sp',
        color=TEXT_DARK,
        size_hint_y=None,
        height=dp(35)
    ))

    # QR code image
    qr_widget = Image(texture=core_img.texture, size_hint_y=None, height=dp(180))
    content.add_widget(qr_widget)

    # URL label (selectable via TextInput)
    url_input = TextInput(
        text=share_url,
        font_name=FONT_NAME,
        font_size='11sp',
        size_hint_y=None,
        height=dp(40),
        padding=[dp(8), dp(10)],
        readonly=True,
        multiline=False,
        background_color=INPUT_BACKGROUND,
        foreground_color=TEXT_DARK
    )
    content.add_widget(url_input)

    # Status label for copy feedback
    status_label = Label(
        text='',
        font_name=FONT_NAME,
        font_size='13sp',
        color=STATUS_SUCCESS,
        size_hint_y=None,
        height=dp(22)
    )
    content.add_widget(status_label)

    def copy_url(btn):
        Clipboard.copy(share_url)
        status_label.text = 'URL copied!'
        Clock.schedule_once(lambda dt: setattr(status_label, 'text', ''), 2)

    def copy_code(btn):
        Clipboard.copy(code)
        status_label.text = 'Code copied!'
        Clock.schedule_once(lambda dt: setattr(status_label, 'text', ''), 2)

    # Copy buttons row
    buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))

    copy_url_btn = RoundedButton(
        text='Copy URL',
        font_size='15sp',
        color=TEXT_WHITE
    )
    copy_url_btn.bind(on_press=copy_url)
    buttons.add_widget(copy_url_btn)

    copy_code_btn = RoundedButton(
        text='Copy Code',
        font_size='15sp',
        color=TEXT_WHITE
    )
    copy_code_btn.bind(on_press=copy_code)
    buttons.add_widget(copy_code_btn)

    content.add_widget(buttons)

    # Close button
    close_btn = GrayRoundedButton(
        text='Close',
        font_size='16sp',
        color=TEXT_DARK,
        size_hint_y=None,
        height=dp(44)
    )
    content.add_widget(close_btn)

    popup = ModalView(
        size_hint=(0.85, None),
        height=dp(450),
        auto_dismiss=True,
        background_color=POPUP_BACKGROUND
    )
    popup.add_widget(content)
    close_btn.bind(on_press=popup.dismiss)
    popup.open()


def show_load_popup(on_game_loaded):
    """Show popup for loading a shared puzzle code.

    Args:
        on_game_loaded: Callback function that receives the loaded Game object
    """
    content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))

    # Title
    content.add_widget(Label(
        text='Load Shared Puzzle',
        font_name=FONT_NAME,
        font_size='18sp',
        color=TEXT_DARK,
        size_hint_y=None,
        height=dp(35)
    ))

    # Instructions
    content.add_widget(Label(
        text='Paste puzzle code or URL:',
        font_name=FONT_NAME,
        font_size='14sp',
        color=TEXT_LIGHT,
        size_hint_y=None,
        height=dp(25)
    ))

    # Text input
    text_input = TextInput(
        multiline=False,
        font_name=FONT_NAME,
        font_size='16sp',
        size_hint_y=None,
        height=dp(48),
        padding=[dp(10), dp(12)],
        background_color=INPUT_BACKGROUND,
        foreground_color=TEXT_HEADER,
        cursor_color=TEXT_DARK,
        hint_text='Enter code here...',
        hint_text_color=INPUT_HINT_COLOR
    )
    content.add_widget(text_input)

    # Error label
    error_label = Label(
        text='',
        font_name=FONT_NAME,
        font_size='13sp',
        color=STATUS_ERROR,
        size_hint_y=None,
        height=dp(22)
    )
    content.add_widget(error_label)

    popup = None  # Will be set after popup creation

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
            on_game_loaded(game)
        except Exception as e:
            error_label.text = 'Invalid puzzle code'

    def paste_clipboard(btn):
        text_input.text = Clipboard.paste() or ''

    # Button row
    buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))

    paste_btn = GrayRoundedButton(
        text='Paste',
        font_size='16sp',
        color=TEXT_DARK
    )
    paste_btn.bind(on_press=paste_clipboard)
    buttons.add_widget(paste_btn)

    load_btn = RoundedButton(
        text='Load',
        font_size='16sp',
        color=TEXT_WHITE
    )
    load_btn.bind(on_press=load_puzzle)
    buttons.add_widget(load_btn)

    content.add_widget(buttons)

    # Cancel button
    cancel_btn = GrayRoundedButton(
        text='Cancel',
        font_size='16sp',
        color=TEXT_DARK,
        size_hint_y=None,
        height=dp(44)
    )
    content.add_widget(cancel_btn)

    popup = ModalView(
        size_hint=(0.85, None),
        height=dp(300),
        auto_dismiss=False,
        background_color=POPUP_BACKGROUND
    )
    popup.add_widget(content)
    cancel_btn.bind(on_press=popup.dismiss)
    popup.open()


class LoadingPopup(ModalView):
    """A loading popup with spinning queen animation."""

    def __init__(self, on_cancel=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.7, 0.45)
        self.auto_dismiss = False
        self.background_color = POPUP_BACKGROUND
        self.on_cancel_callback = on_cancel
        self.rotation_angle = 0
        self.elapsed_time = 0.0
        self._animation_event = None
        self._timer_event = None

        # Load queen texture once
        self.queen_texture = CoreImage(os.path.join(ICONS_DIR, 'queen.png')).texture

        # Main layout
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        # Status label (title at top)
        self.status_label = Label(
            text='Generating puzzle...',
            font_name=FONT_NAME,
            font_size='16sp',
            color=TEXT_DARK,
            size_hint_y=None,
            height=dp(45),
            halign='center',
            valign='middle',
            text_size=(None, None)
        )
        self.status_label.bind(width=lambda *x: setattr(self.status_label, 'text_size', (self.status_label.width, None)))
        layout.add_widget(self.status_label)

        # Spinner widget (custom drawing)
        self.spinner_widget = Widget(size_hint=(1, 1))
        self.spinner_widget.bind(pos=self._update_spinner, size=self._update_spinner)
        layout.add_widget(self.spinner_widget)

        # Stopwatch label (small, subtle)
        self.timer_label = Label(
            text='0:00',
            font_name=FONT_NAME,
            font_size='12sp',
            color=TEXT_MEDIUM,
            size_hint_y=None,
            height=dp(18)
        )
        layout.add_widget(self.timer_label)

        # Cancel button
        cancel_btn = GrayRoundedButton(
            text='Cancel',
            font_size='15sp',
            color=TEXT_DARK,
            size_hint=(None, None),
            size=(dp(100), dp(40)),
            pos_hint={'center_x': 0.5}
        )
        cancel_btn.bind(on_press=self._on_cancel)
        layout.add_widget(cancel_btn)

        self.add_widget(layout)

    def _update_spinner(self, *args):
        """Redraw the spinning queen."""
        self.spinner_widget.canvas.clear()

        w, h = self.spinner_widget.size
        x, y = self.spinner_widget.pos
        cx, cy = x + w / 2, y + h / 2

        circle_radius = min(w, h) / 2 * 0.7
        queen_size = circle_radius * 1.3

        with self.spinner_widget.canvas:
            # White circle background
            Color(*COLOR_WHITE)
            Ellipse(pos=(cx - circle_radius, cy - circle_radius),
                   size=(circle_radius * 2, circle_radius * 2))

            # Light gray border
            Color(*SPINNER_BORDER)
            Line(ellipse=(cx - circle_radius, cy - circle_radius,
                         circle_radius * 2, circle_radius * 2), width=dp(2))

            # Spinning queen
            PushMatrix()
            Rotate(angle=self.rotation_angle, origin=(cx, cy))
            Color(*COLOR_WHITE)
            Rectangle(
                pos=(cx - queen_size / 2, cy - queen_size / 2),
                size=(queen_size, queen_size),
                texture=self.queen_texture
            )
            PopMatrix()

    def _animate(self, dt):
        """Animation tick - rotate the queen."""
        self.rotation_angle = (self.rotation_angle + 3) % 360
        self._update_spinner()

    def _update_timer(self, dt):
        """Update the stopwatch display."""
        self.elapsed_time += dt
        minutes = int(self.elapsed_time) // 60
        seconds = int(self.elapsed_time) % 60
        self.timer_label.text = f'{minutes}:{seconds:02d}'

    def set_status(self, text):
        """Update the status text."""
        self.status_label.text = text

    def open(self, *args, **kwargs):
        """Start animation when popup opens."""
        super().open(*args, **kwargs)
        self.rotation_angle = 0
        self.elapsed_time = 0.0
        self.timer_label.text = '0:00'
        self._animation_event = Clock.schedule_interval(self._animate, 1/60)
        self._timer_event = Clock.schedule_interval(self._update_timer, 1)

    def dismiss(self, *args, **kwargs):
        """Stop animation when popup closes."""
        if self._animation_event:
            self._animation_event.cancel()
            self._animation_event = None
        if self._timer_event:
            self._timer_event.cancel()
            self._timer_event = None
        super().dismiss(*args, **kwargs)

    def _on_cancel(self, instance):
        """Handle cancel button press."""
        if self.on_cancel_callback:
            self.on_cancel_callback()
        self.dismiss()


def _show_size_selection_popup(title, sizes, on_size_selected, popup_height):
    """Generic size selection popup.

    Args:
        title: Popup title text
        sizes: List of sizes to show, grouped by row (e.g., [[6,7,8]] or [[6,7],[8,9]])
        on_size_selected: Callback receiving the selected size
        popup_height: Height of the popup in dp
    """
    content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))

    # Title
    content.add_widget(Label(
        text=title,
        font_name=FONT_NAME,
        font_size='18sp',
        color=TEXT_DARK,
        size_hint_y=None,
        height=dp(40)
    ))

    popup = None  # Will be set after creation

    def make_callback(size):
        def callback(btn):
            popup.dismiss()
            on_size_selected(size)
        return callback

    # Create button rows
    for row_sizes in sizes:
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        for size in row_sizes:
            btn = RoundedButton(
                text=f'{size}x{size}',
                font_size='18sp',
                color=TEXT_WHITE
            )
            btn.bind(on_press=make_callback(size))
            row.add_widget(btn)
        content.add_widget(row)

    # Spacer
    content.add_widget(Widget(size_hint_y=None, height=dp(5)))

    # Cancel button
    cancel_btn = GrayRoundedButton(
        text='Cancel',
        font_size='16sp',
        color=TEXT_DARK,
        size_hint_y=None,
        height=dp(44)
    )
    content.add_widget(cancel_btn)

    popup = ModalView(
        size_hint=(0.8, None),
        height=dp(popup_height),
        auto_dismiss=True,
        background_color=POPUP_BACKGROUND
    )
    popup.add_widget(content)
    cancel_btn.bind(on_press=popup.dismiss)
    popup.open()


def show_date_puzzles_popup(selected_date, on_size_selected):
    """Show popup for selecting puzzle size for a specific date.

    Args:
        selected_date: The date for the puzzles
        on_size_selected: Callback function that receives the selected size (int)
    """
    from datetime import date

    if selected_date == date.today():
        title = "Today's Puzzles"
    else:
        title = selected_date.strftime('%B %d, %Y')

    _show_size_selection_popup(
        title=title,
        sizes=[[6, 7, 8]],
        on_size_selected=on_size_selected,
        popup_height=200
    )


def show_game_size_popup(on_size_and_strategy_selected):
    """Show popup for selecting game size and kingdom strategy.

    Args:
        on_size_and_strategy_selected: Callback receiving (size: int, strategy: str)
    """
    content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))

    # Title
    content.add_widget(Label(
        text='Select Puzzle Size',
        font_name=FONT_NAME,
        font_size='18sp',
        color=TEXT_DARK,
        size_hint_y=None,
        height=dp(35)
    ))

    popup = None
    selected_strategy = ['mixed']  # Use list to allow modification in nested function

    def make_size_callback(size):
        def callback(btn):
            popup.dismiss()
            on_size_and_strategy_selected(size, selected_strategy[0])
        return callback

    # Size buttons (2x2 grid)
    row1 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
    row2 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))

    for size, row in [(6, row1), (7, row1), (8, row2), (9, row2)]:
        btn = RoundedButton(
            text=f'{size}x{size}',
            font_size='18sp',
            color=TEXT_WHITE
        )
        btn.bind(on_press=make_size_callback(size))
        row.add_widget(btn)

    content.add_widget(row1)
    content.add_widget(row2)

    # Strategy label
    content.add_widget(Label(
        text='Kingdom Style',
        font_name=FONT_NAME,
        font_size='14sp',
        color=TEXT_LIGHT,
        size_hint_y=None,
        height=dp(25)
    ))

    # Strategy buttons (radio-style)
    strategy_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
    strategy_buttons = {}

    strategies = [
        ('classic', 'Classic'),
        ('mixed', 'Mixed'),
        ('jagged', 'Jagged'),
    ]

    def select_strategy(strategy):
        def callback(btn):
            selected_strategy[0] = strategy
            # Update button colors to show selection
            for s, b in strategy_buttons.items():
                if s == strategy:
                    b.bg_color = DEFAULT_BUTTON_COLOR_DOWN  # Darker = selected
                else:
                    b.bg_color = BUTTON_UNSELECTED  # Gray = unselected
                b._update_bg()
        return callback

    for strategy, label in strategies:
        btn = RoundedButton(
            text=label,
            font_size='14sp',
            color=TEXT_WHITE,
            bg_color=BUTTON_UNSELECTED if strategy != 'mixed' else DEFAULT_BUTTON_COLOR_DOWN
        )
        btn.bind(on_press=select_strategy(strategy))
        strategy_buttons[strategy] = btn
        strategy_row.add_widget(btn)

    content.add_widget(strategy_row)

    # Spacer
    content.add_widget(Widget(size_hint_y=None, height=dp(5)))

    # Cancel button
    cancel_btn = GrayRoundedButton(
        text='Cancel',
        font_size='16sp',
        color=TEXT_DARK,
        size_hint_y=None,
        height=dp(44)
    )
    content.add_widget(cancel_btn)

    popup = ModalView(
        size_hint=(0.85, None),
        height=dp(340),
        auto_dismiss=True,
        background_color=POPUP_BACKGROUND
    )
    popup.add_widget(content)
    cancel_btn.bind(on_press=popup.dismiss)
    popup.open()
