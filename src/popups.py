import io
import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.modalview import ModalView
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.image import Image as CoreImage
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Rectangle, PushMatrix, PopMatrix, Rotate, Line
from kivy.metrics import dp

from game import Game

ICONS_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'icons')

# Salad green button colors (matching menu.py)
BUTTON_COLOR = (0.55, 0.78, 0.4, 1)
BUTTON_COLOR_DOWN = (0.45, 0.68, 0.3, 1)
BUTTON_RADIUS = dp(12)


class RoundedButton(ButtonBehavior, Label):
    """A button with rounded corners - green style matching main menu."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = BUTTON_COLOR
        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*BUTTON_COLOR_DOWN)
            else:
                Color(*self.background_color)
            from kivy.graphics import RoundedRectangle
            RoundedRectangle(pos=self.pos, size=self.size, radius=[BUTTON_RADIUS])


class GrayRoundedButton(ButtonBehavior, Label):
    """A button with rounded corners - gray style for cancel buttons."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0.75, 0.75, 0.75, 1)
        self.background_color_down = (0.6, 0.6, 0.6, 1)
        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*self.background_color_down)
            else:
                Color(*self.background_color)
            from kivy.graphics import RoundedRectangle
            RoundedRectangle(pos=self.pos, size=self.size, radius=[BUTTON_RADIUS])


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


def show_load_popup(on_game_loaded):
    """Show popup for loading a shared puzzle code.

    Args:
        on_game_loaded: Callback function that receives the loaded Game object
    """
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


class LoadingPopup(ModalView):
    """A loading popup with spinning queen animation."""

    def __init__(self, on_cancel=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.7, 0.4)
        self.auto_dismiss = False
        self.background_color = (1, 1, 1, 0.95)
        self.on_cancel_callback = on_cancel
        self.rotation_angle = 0
        self._animation_event = None

        # Load queen texture once
        self.queen_texture = CoreImage(os.path.join(ICONS_DIR, 'queen.png')).texture

        # Main layout
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

        # Spinner widget (custom drawing)
        self.spinner_widget = Widget(size_hint=(1, 1))
        self.spinner_widget.bind(pos=self._update_spinner, size=self._update_spinner)
        layout.add_widget(self.spinner_widget)

        # Status label
        self.status_label = Label(
            text='Generating puzzle...',
            font_name='DMSans',
            font_size='14sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=dp(30)
        )
        layout.add_widget(self.status_label)

        # Cancel button
        cancel_btn = Button(
            text='Cancel',
            font_name='DMSans',
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
            Color(1, 1, 1, 1)
            Ellipse(pos=(cx - circle_radius, cy - circle_radius),
                   size=(circle_radius * 2, circle_radius * 2))

            # Light gray border
            Color(0.8, 0.8, 0.8, 1)
            Line(ellipse=(cx - circle_radius, cy - circle_radius,
                         circle_radius * 2, circle_radius * 2), width=dp(2))

            # Spinning queen
            PushMatrix()
            Rotate(angle=self.rotation_angle, origin=(cx, cy))
            Color(1, 1, 1, 1)
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

    def set_status(self, text):
        """Update the status text."""
        self.status_label.text = text

    def open(self, *args, **kwargs):
        """Start animation when popup opens."""
        super().open(*args, **kwargs)
        self.rotation_angle = 0
        self._animation_event = Clock.schedule_interval(self._animate, 1/60)

    def dismiss(self, *args, **kwargs):
        """Stop animation when popup closes."""
        if self._animation_event:
            self._animation_event.cancel()
            self._animation_event = None
        super().dismiss(*args, **kwargs)

    def _on_cancel(self, instance):
        """Handle cancel button press."""
        if self.on_cancel_callback:
            self.on_cancel_callback()
        self.dismiss()


def show_game_size_popup(on_size_selected):
    """Show popup for selecting game size.

    Args:
        on_size_selected: Callback function that receives the selected size (int)
    """
    content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))

    # Title
    content.add_widget(Label(
        text='Select Puzzle Size',
        font_name='DMSansBlack',
        font_size='18sp',
        color=(0.3, 0.3, 0.3, 1),
        size_hint_y=None,
        height=dp(40)
    ))

    popup = None  # Will be set after creation

    def make_callback(size):
        def callback(btn):
            popup.dismiss()
            on_size_selected(size)
        return callback

    # Size buttons in a grid (2x2)
    row1 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
    row2 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))

    for size, row in [(6, row1), (7, row1), (8, row2), (9, row2)]:
        btn = RoundedButton(
            text=f'{size}x{size}',
            font_name='DMSans',
            font_size='18sp',
            color=(1, 1, 1, 1)
        )
        btn.bind(on_press=make_callback(size))
        row.add_widget(btn)

    content.add_widget(row1)
    content.add_widget(row2)

    # Spacer
    content.add_widget(Widget(size_hint_y=None, height=dp(5)))

    # Cancel button (gray)
    cancel_btn = GrayRoundedButton(
        text='Cancel',
        font_name='DMSans',
        font_size='16sp',
        color=(0.3, 0.3, 0.3, 1),
        size_hint_y=None,
        height=dp(44)
    )
    content.add_widget(cancel_btn)

    popup = ModalView(
        size_hint=(0.8, None),
        height=dp(280),
        auto_dismiss=True,
        background_color=(1, 1, 1, 0.95)
    )
    popup.add_widget(content)
    cancel_btn.bind(on_press=popup.dismiss)
    popup.open()
