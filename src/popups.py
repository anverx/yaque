import io
import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.modalview import ModalView
from kivy.core.image import Image as CoreImage
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Rectangle, PushMatrix, PopMatrix, Rotate, Line
from kivy.metrics import dp

from game import Game
from ui_constants import (
    COLOR_WHITE,
    POPUP_BACKGROUND, SPINNER_BORDER,
    STATUS_SUCCESS, STATUS_ERROR,
    DEFAULT_BUTTON_COLOR_DOWN, BUTTON_UNSELECTED,
    POPUP_WIDTH_NARROW, SPACING_XL, SPACING_XXL,
    BUTTON_HEIGHT_SM,
    QR_IMAGE_HEIGHT, CAPTION_HEIGHT, CAPTION_HEIGHT_SM,
    SMALL_BUTTON_WIDTH, SPINNER_LINE_WIDTH, SPACER_SM,
)
from widgets import (
    RoundedButton, GrayRoundedButton, FixedGrayRoundedButton, SmallRoundedButton,
    TitleLabel, SubtitleLabel, CaptionLabel, StatusLabel,
    PopupContent, ButtonRow, SizeButtonRow, Popup,
    UrlInput, CodeInput,
)

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
    content = PopupContent()
    content.add_widget(TitleLabel('Share Puzzle'))

    # QR code image
    qr_widget = Image(texture=core_img.texture, size_hint_y=None, height=dp(QR_IMAGE_HEIGHT))
    content.add_widget(qr_widget)

    # URL label (selectable via TextInput)
    url_input = UrlInput(share_url)
    content.add_widget(url_input)

    # Status label for copy feedback
    status_label = CaptionLabel('', color=STATUS_SUCCESS, size_hint_y=None, height=dp(CAPTION_HEIGHT))
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
    buttons = ButtonRow()
    copy_url_btn = RoundedButton(text='Copy URL')
    copy_url_btn.bind(on_press=copy_url)
    buttons.add_widget(copy_url_btn)

    copy_code_btn = RoundedButton(text='Copy Code')
    copy_code_btn.bind(on_press=copy_code)
    buttons.add_widget(copy_code_btn)
    content.add_widget(buttons)

    # Close button
    close_btn = FixedGrayRoundedButton(text='Close')
    content.add_widget(close_btn)

    popup = Popup(content, height=450)
    close_btn.bind(on_press=popup.dismiss)
    popup.open()


def show_load_popup(on_game_loaded):
    """Show popup for loading a shared puzzle code.

    Args:
        on_game_loaded: Callback function that receives the loaded Game object
    """
    content = PopupContent()
    content.add_widget(TitleLabel('Load Shared Puzzle'))
    content.add_widget(SubtitleLabel('Paste puzzle code or URL:'))

    # Text input
    text_input = CodeInput()
    content.add_widget(text_input)

    # Error label
    error_label = CaptionLabel('', color=STATUS_ERROR, size_hint_y=None, height=dp(CAPTION_HEIGHT))
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
    buttons = ButtonRow()
    paste_btn = GrayRoundedButton(text='Paste')
    paste_btn.bind(on_press=paste_clipboard)
    buttons.add_widget(paste_btn)

    load_btn = RoundedButton(text='Load')
    load_btn.bind(on_press=load_puzzle)
    buttons.add_widget(load_btn)
    content.add_widget(buttons)

    # Cancel button
    cancel_btn = FixedGrayRoundedButton(text='Cancel')
    content.add_widget(cancel_btn)

    popup = Popup(content, height=300, auto_dismiss=False)
    cancel_btn.bind(on_press=popup.dismiss)
    popup.open()


class LoadingPopup(ModalView):
    """A loading popup with spinning queen animation."""

    def __init__(self, on_cancel=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (POPUP_WIDTH_NARROW, 0.45)
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
        layout = PopupContent(padding=[dp(SPACING_XXL), dp(SPACING_XL)])

        # Status label (title at top)
        self.status_label = StatusLabel('Generating puzzle...')
        layout.add_widget(self.status_label)

        # Spinner widget (custom drawing)
        self.spinner_widget = Widget(size_hint=(1, 1))
        self.spinner_widget.bind(pos=self._update_spinner, size=self._update_spinner)
        layout.add_widget(self.spinner_widget)

        # Stopwatch label (small, subtle)
        self.timer_label = CaptionLabel('0:00', size_hint_y=None, height=dp(CAPTION_HEIGHT_SM))
        layout.add_widget(self.timer_label)

        # Cancel button
        cancel_btn = GrayRoundedButton(
            text='Cancel',
            size_hint=(None, None),
            size=(dp(SMALL_BUTTON_WIDTH), dp(BUTTON_HEIGHT_SM)),
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
                         circle_radius * 2, circle_radius * 2), width=dp(SPINNER_LINE_WIDTH))

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
    content = PopupContent()
    content.add_widget(TitleLabel(title, height=40))

    popup = None  # Will be set after creation

    def make_callback(size):
        def callback(btn):
            popup.dismiss()
            on_size_selected(size)
        return callback

    # Create button rows
    for row_sizes in sizes:
        row = SizeButtonRow()
        for size in row_sizes:
            btn = RoundedButton(text=f'{size}x{size}')
            btn.bind(on_press=make_callback(size))
            row.add_widget(btn)
        content.add_widget(row)

    # Spacer
    content.add_widget(Widget(size_hint_y=None, height=dp(SPACER_SM)))

    # Cancel button
    cancel_btn = FixedGrayRoundedButton(text='Cancel')
    content.add_widget(cancel_btn)

    popup = Popup(content, height=popup_height, width_hint=0.8)
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
    content = PopupContent()
    content.add_widget(TitleLabel('Select Puzzle Size'))

    popup = None
    selected_strategy = ['mixed']  # Use list to allow modification in nested function

    def make_size_callback(size):
        def callback(btn):
            popup.dismiss()
            on_size_and_strategy_selected(size, selected_strategy[0])
        return callback

    # Size buttons (2x2 grid)
    row1 = SizeButtonRow()
    row2 = SizeButtonRow()

    for size, row in [(6, row1), (7, row1), (8, row2), (9, row2)]:
        btn = RoundedButton(text=f'{size}x{size}')
        btn.bind(on_press=make_size_callback(size))
        row.add_widget(btn)

    content.add_widget(row1)
    content.add_widget(row2)

    # Strategy label
    content.add_widget(SubtitleLabel('Kingdom Style'))

    # Strategy buttons (radio-style)
    strategy_row = ButtonRow(height=dp(BUTTON_HEIGHT_SM), spacing=dp(SPACING_MD))
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
        btn = SmallRoundedButton(
            text=label,
            bg_color=BUTTON_UNSELECTED if strategy != 'mixed' else DEFAULT_BUTTON_COLOR_DOWN
        )
        btn.bind(on_press=select_strategy(strategy))
        strategy_buttons[strategy] = btn
        strategy_row.add_widget(btn)

    content.add_widget(strategy_row)

    # Spacer
    content.add_widget(Widget(size_hint_y=None, height=dp(SPACER_SM)))

    # Cancel button
    cancel_btn = FixedGrayRoundedButton(text='Cancel')
    content.add_widget(cancel_btn)

    popup = Popup(content, height=340)
    cancel_btn.bind(on_press=popup.dismiss)
    popup.open()
