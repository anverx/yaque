from __future__ import annotations

import io
from collections.abc import Callable
from datetime import date
from typing import Any

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget

from game import Game
from ui_constants import (
    POPUP_BACKGROUND,
    POPUP_WIDTH_NARROW,
    SPACING_XL,
    SPACING_XXL,
    STATUS_ERROR,
    STATUS_SUCCESS,
    STYLES,
)
from widgets import (
    ButtonRow,
    CaptionLabel,
    CodeInput,
    FixedGrayRoundedButton,
    FixedRoundedButton,
    GrayRoundedButton,
    Popup,
    PopupContent,
    QueenSpinner,
    RoundedButton,
    SelectableButton,
    SelectableButtonGroup,
    SizeButtonRow,
    StatusLabel,
    SubtitleLabel,
    TitleLabel,
    UrlInput,
    styled,
)


def show_share_popup(share_url: str, code: str) -> None:
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
    qr_widget = styled(Image, 'qr_image', texture=core_img.texture)
    content.add_widget(qr_widget)

    # URL label (selectable via TextInput)
    url_input = UrlInput(share_url)
    content.add_widget(url_input)

    # Status label for copy feedback
    status_label = CaptionLabel('', color=STATUS_SUCCESS, **STYLES['status_area'])
    content.add_widget(status_label)

    def copy_url(btn: Any) -> None:
        Clipboard.copy(share_url)
        status_label.text = 'URL copied!'
        Clock.schedule_once(lambda dt: setattr(status_label, 'text', ''), 2)

    def copy_code(btn: Any) -> None:
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


def show_load_popup(on_game_loaded: Callable[[Game], None]) -> None:
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
    error_label = CaptionLabel('', color=STATUS_ERROR, **STYLES['status_area'])
    content.add_widget(error_label)

    popup = None  # Will be set after popup creation

    def load_puzzle(btn: Any) -> None:
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
        except Exception:
            error_label.text = 'Invalid puzzle code'

    def paste_clipboard(btn: Any) -> None:
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

    def __init__(self, on_cancel: Callable[[], None] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.size_hint = (POPUP_WIDTH_NARROW, 0.45)
        self.auto_dismiss = False
        self.background_color = POPUP_BACKGROUND
        self.on_cancel_callback = on_cancel
        self.elapsed_time: float = 0.0
        self._animation_event: Any = None
        self._timer_event: Any = None

        # Main layout
        layout = PopupContent(padding=[dp(SPACING_XXL), dp(SPACING_XL)])

        # Status label (title at top)
        self.status_label = StatusLabel('Generating puzzle...')
        layout.add_widget(self.status_label)

        # Spinner widget
        self.spinner = QueenSpinner(size_hint=(1, 1))
        layout.add_widget(self.spinner)

        # Stopwatch label (small, subtle)
        self.timer_label = CaptionLabel('0:00', **STYLES['timer_area'])
        layout.add_widget(self.timer_label)

        # Cancel button
        cancel_btn = GrayRoundedButton(text='Cancel', **STYLES['small_centered_btn'])
        cancel_btn.bind(on_press=self._on_cancel)
        layout.add_widget(cancel_btn)

        self.add_widget(layout)

    def _animate(self, dt: float) -> None:
        """Animation tick - rotate the queen."""
        self.spinner.rotate()

    def _update_timer(self, dt: float) -> None:
        """Update the stopwatch display."""
        self.elapsed_time += dt
        minutes = int(self.elapsed_time) // 60
        seconds = int(self.elapsed_time) % 60
        self.timer_label.text = f'{minutes}:{seconds:02d}'

    def set_status(self, text: str) -> None:
        """Update the status text."""
        self.status_label.text = text

    def open(self, *args: Any, **kwargs: Any) -> None:
        """Start animation when popup opens."""
        super().open(*args, **kwargs)
        self.spinner.reset()
        self.elapsed_time = 0.0
        self.timer_label.text = '0:00'
        self._animation_event = Clock.schedule_interval(self._animate, 1/60)
        self._timer_event = Clock.schedule_interval(self._update_timer, 1)

    def dismiss(self, *args: Any, **kwargs: Any) -> None:
        """Stop animation when popup closes."""
        if self._animation_event:
            self._animation_event.cancel()
            self._animation_event = None
        if self._timer_event:
            self._timer_event.cancel()
            self._timer_event = None
        super().dismiss(*args, **kwargs)

    def _on_cancel(self, instance: Any) -> None:
        """Handle cancel button press."""
        if self.on_cancel_callback:
            self.on_cancel_callback()
        self.dismiss()


def _show_size_selection_popup(
    title: str,
    sizes: list[list[int]],
    on_size_selected: Callable[[int], None],
    popup_height: float
) -> None:
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

    def make_callback(size: int) -> Callable[[Any], None]:
        def callback(btn: Any) -> None:
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
    content.add_widget(styled(Widget, 'spacer_sm'))

    # Cancel button
    cancel_btn = FixedGrayRoundedButton(text='Cancel')
    content.add_widget(cancel_btn)

    popup = Popup(content, height=popup_height, width_hint=0.8)
    cancel_btn.bind(on_press=popup.dismiss)
    popup.open()


def show_date_puzzles_popup(selected_date: date, on_size_selected: Callable[[int], None]) -> None:
    """Show popup for selecting puzzle size for a specific date.

    Args:
        selected_date: The date for the puzzles
        on_size_selected: Callback function that receives the selected size (int)
    """
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


def show_game_size_popup(on_game_options_selected: Callable[[int, str, int], None]) -> None:
    """Show popup for selecting game size, kingdom strategy, and max solutions.

    Args:
        on_game_options_selected: Callback receiving (size: int, strategy: str, max_solutions: int)
    """
    content = PopupContent()
    content.add_widget(TitleLabel('Random Puzzle'))

    popup = None
    selected_size = [8]  # Default size
    selected_strategy = ['mixed']
    selected_max_solutions = [1]  # Default: unique

    # Size selection
    content.add_widget(SubtitleLabel('Size'))
    size_row = styled(BoxLayout, 'selection_row')
    size_group = SelectableButtonGroup(
        on_select=lambda value: selected_size.__setitem__(0, value)
    )

    for size in [6, 7, 8, 9]:
        btn = SelectableButton(
            text=f'{size}x{size}',
            selected=(size == 8),
            **STYLES['selection_btn']
        )
        size_group.add(size, btn)
        size_row.add_widget(btn)

    content.add_widget(size_row)

    # Strategy selection
    content.add_widget(SubtitleLabel('Kingdom Style'))
    strategy_row = styled(BoxLayout, 'selection_row')
    strategy_group = SelectableButtonGroup(
        on_select=lambda value: selected_strategy.__setitem__(0, value)
    )

    strategies = [
        ('classic', 'Classic'),
        ('mixed', 'Mixed'),
        ('jagged', 'Jagged'),
    ]

    for strategy, label in strategies:
        btn = SelectableButton(
            text=label,
            selected=(strategy == 'mixed'),
            **STYLES['selection_btn']
        )
        strategy_group.add(strategy, btn)
        strategy_row.add_widget(btn)

    content.add_widget(strategy_row)

    # Solution count selection
    content.add_widget(SubtitleLabel('Solutions'))
    solutions_row = styled(BoxLayout, 'selection_row')
    solutions_group = SelectableButtonGroup(
        on_select=lambda value: selected_max_solutions.__setitem__(0, value)
    )

    solution_options = [
        (1, 'Unique'),
        (4, '< 4'),
        (10, '< 10'),
    ]

    for max_sol, label in solution_options:
        btn = SelectableButton(
            text=label,
            selected=(max_sol == 1),
            **STYLES['selection_btn']
        )
        solutions_group.add(max_sol, btn)
        solutions_row.add_widget(btn)

    content.add_widget(solutions_row)

    # Spacer
    content.add_widget(styled(Widget, 'spacer_sm'))

    # Play button
    def on_play(btn: Any) -> None:
        popup.dismiss()
        on_game_options_selected(selected_size[0], selected_strategy[0], selected_max_solutions[0])

    play_btn = FixedRoundedButton(text='Play')
    play_btn.bind(on_press=on_play)
    content.add_widget(play_btn)

    # Cancel button
    cancel_btn = FixedGrayRoundedButton(text='Cancel')
    content.add_widget(cancel_btn)

    popup = Popup(content, height=420)
    cancel_btn.bind(on_press=popup.dismiss)
    popup.open()
