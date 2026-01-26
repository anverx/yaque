import io

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.image import Image as CoreImage
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock

from game import Game


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
