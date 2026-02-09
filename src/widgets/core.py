"""Core UI widgets for Yaque."""

from __future__ import annotations

from typing import Any, Callable

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

from ui_constants import (
    FONT_NAME, TEXT_WHITE, TEXT_DARK, TEXT_HEADER,
    DEFAULT_BUTTON_COLOR, DEFAULT_BUTTON_COLOR_DOWN,
    GRAY_BUTTON_COLOR, GRAY_BUTTON_COLOR_DOWN,
    INPUT_BACKGROUND, INPUT_HINT_COLOR, LINK_COLOR,
    LABEL_STYLES, LAYOUT_STYLES,
    POPUP_BACKGROUND, POPUP_WIDTH,
    PADDING_POPUP, SPACING_LG, SPACING_MD, SPACING_XL,
    BUTTON_HEIGHT, BUTTON_HEIGHT_SM, BUTTON_FONT_SIZE, RADIUS_MD, LINK_HEIGHT,
)

BUTTON_RADIUS = dp(RADIUS_MD)


# Type alias for color tuples
ColorTuple = tuple[float, float, float, float]


class RoundedButton(ButtonBehavior, Label):
    """A button with rounded corners. Use in ButtonRow or containers.

    Args:
        bg_color: Background color tuple (r, g, b, a). Defaults to salad green.
        bg_color_down: Pressed background color. Defaults to darker shade.
    """
    def __init__(self, bg_color: ColorTuple | None = None, bg_color_down: ColorTuple | None = None, **kwargs: Any) -> None:
        kwargs.setdefault('font_name', FONT_NAME)
        kwargs.setdefault('font_size', BUTTON_FONT_SIZE)
        kwargs.setdefault('color', TEXT_WHITE)
        kwargs.setdefault('markup', True)
        kwargs.setdefault('halign', 'center')
        kwargs.setdefault('valign', 'middle')
        kwargs.setdefault('height', dp(BUTTON_HEIGHT))
        super().__init__(**kwargs)
        self.bg_color = bg_color or DEFAULT_BUTTON_COLOR
        self.bg_color_down = bg_color_down or DEFAULT_BUTTON_COLOR_DOWN
        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)
        self.bind(size=self._update_text_size)

    def _update_text_size(self, *args: Any) -> None:
        self.text_size = self.size

    def _update_bg(self, *args: Any) -> None:
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*self.bg_color_down)
            else:
                Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[BUTTON_RADIUS])


def GrayRoundedButton(**kwargs: Any) -> RoundedButton:
    """Factory for gray rounded buttons in containers."""
    kwargs.setdefault('color', TEXT_DARK)
    return RoundedButton(
        bg_color=GRAY_BUTTON_COLOR,
        bg_color_down=GRAY_BUTTON_COLOR_DOWN,
        **kwargs
    )


def FixedRoundedButton(**kwargs: Any) -> RoundedButton:
    """Factory for standalone buttons with fixed height."""
    kwargs.setdefault('size_hint_y', None)
    return RoundedButton(**kwargs)


def FixedGrayRoundedButton(**kwargs: Any) -> RoundedButton:
    """Factory for standalone gray buttons with fixed height."""
    kwargs.setdefault('size_hint_y', None)
    return GrayRoundedButton(**kwargs)


# -----------------------------------------------------------------------------
# Label Factory (CSS-like: styles defined in ui_constants.LABEL_STYLES)
# -----------------------------------------------------------------------------

def styled_label(style: str = 'default', text: str = '', **overrides: Any) -> Label:
    """Create a label with the specified style.

    Styles are defined in ui_constants.LABEL_STYLES (CSS-like separation).
    Any kwargs override the style defaults.

    Args:
        style: Style name ('title', 'subtitle', 'caption', or 'default')
        text: Label text
        **overrides: Properties to override style defaults
    """
    # Get style properties (copy to avoid mutation)
    props = LABEL_STYLES.get(style, LABEL_STYLES['default']).copy()

    # Convert height to dp if present
    if 'height' in props:
        props['height'] = dp(props['height'])

    # Apply font_name default
    props.setdefault('font_name', FONT_NAME)

    # Apply overrides
    props.update(overrides)

    return Label(text=text, **props)


# Convenience wrappers (content-only calls)
def StyledLabel(**kwargs: Any) -> Label:
    """Base styled label with app font."""
    return styled_label('default', **kwargs)


def TitleLgLabel(text: str, **kwargs: Any) -> Label:
    """Large title label for screen headers (24sp)."""
    return styled_label('title_lg', text, **kwargs)


def TitleMdLabel(text: str, **kwargs: Any) -> Label:
    """Medium title label for section headers (20sp)."""
    return styled_label('title_md', text, **kwargs)


def TitleLabel(text: str, **kwargs: Any) -> Label:
    """Title label for popups and screen headers (18sp)."""
    return styled_label('title', text, **kwargs)


def TitleSmLabel(text: str, **kwargs: Any) -> Label:
    """Small title label for game screen headers (16sp)."""
    return styled_label('title_sm', text, **kwargs)


def SubtitleLabel(text: str, **kwargs: Any) -> Label:
    """Subtitle label for descriptions (14sp)."""
    return styled_label('subtitle', text, **kwargs)


def CaptionLabel(text: str, **kwargs: Any) -> Label:
    """Caption label for small text and metadata (12sp)."""
    return styled_label('caption', text, **kwargs)


def MonthLabel(text: str, **kwargs: Any) -> Label:
    """Month/year display label for calendar (22sp)."""
    return styled_label('month', text, **kwargs)


def DayLabel(text: str, **kwargs: Any) -> Label:
    """Day name/number label for calendar (14sp)."""
    return styled_label('day', text, **kwargs)


def TableHeaderLabel(text: str, **kwargs: Any) -> Label:
    """Table column header label (11sp)."""
    return styled_label('table_header', text, **kwargs)


def TableCellLabel(text: str, **kwargs: Any) -> Label:
    """Table cell data label (13sp)."""
    return styled_label('table_cell', text, **kwargs)


def ClockLabel(text: str = '00:00', **kwargs: Any) -> Label:
    """Large clock/timer display label (36sp)."""
    return styled_label('clock', text, **kwargs)


def IconLabel(text: str, **kwargs: Any) -> Label:
    """Tiny label for icon button captions (9sp)."""
    return styled_label('icon_label', text, **kwargs)


def AboutTitleLabel(text: str, **kwargs: Any) -> Label:
    """Large title for About popup (28sp)."""
    return styled_label('about_title', text, **kwargs)


def AboutSubtitleLabel(text: str, **kwargs: Any) -> Label:
    """Subtitle for About popup (16sp)."""
    return styled_label('about_subtitle', text, **kwargs)


# -----------------------------------------------------------------------------
# Layout Factories
# -----------------------------------------------------------------------------

def PopupContent(**kwargs: Any) -> BoxLayout:
    """Vertical BoxLayout with popup padding/spacing defaults."""
    kwargs.setdefault('orientation', 'vertical')
    kwargs.setdefault('padding', [dp(PADDING_POPUP[0]), dp(PADDING_POPUP[1])])
    kwargs.setdefault('spacing', dp(SPACING_LG))
    return BoxLayout(**kwargs)


def styled_layout(style: str = 'button_row', **overrides: Any) -> BoxLayout:
    """Create a BoxLayout with the specified style.

    Styles are defined in ui_constants.LAYOUT_STYLES.
    """
    props = LAYOUT_STYLES.get(style, LAYOUT_STYLES['button_row']).copy()

    # Convert height and spacing to dp
    if 'height' in props:
        props['height'] = dp(props['height'])
    if 'spacing' in props:
        props['spacing'] = dp(props['spacing'])

    props.update(overrides)
    return BoxLayout(**props)


def ButtonRow(**kwargs: Any) -> BoxLayout:
    """Horizontal BoxLayout for button rows with standard height/spacing."""
    return styled_layout('button_row', **kwargs)


def SizeButtonRow(**kwargs: Any) -> BoxLayout:
    """Horizontal BoxLayout for size selection buttons (taller)."""
    return styled_layout('size_button_row', **kwargs)


def Popup(content: Widget, height: float, width_hint: float = POPUP_WIDTH, auto_dismiss: bool = True) -> ModalView:
    """Create a styled ModalView popup.

    Args:
        content: Widget to add as popup content
        height: Popup height in dp units (raw number)
        width_hint: size_hint_x value (default POPUP_WIDTH)
        auto_dismiss: Whether tapping outside closes popup
    """
    popup = ModalView(
        size_hint=(width_hint, None),
        height=dp(height),
        auto_dismiss=auto_dismiss,
        background_color=POPUP_BACKGROUND
    )
    popup.add_widget(content)
    return popup


# -----------------------------------------------------------------------------
# Input Factories
# -----------------------------------------------------------------------------

def UrlInput(text: str, **kwargs: Any) -> TextInput:
    """Readonly text input for displaying URLs (small font, selectable)."""
    kwargs.setdefault('font_name', FONT_NAME)
    kwargs.setdefault('font_size', '11sp')
    kwargs.setdefault('size_hint_y', None)
    kwargs.setdefault('height', dp(BUTTON_HEIGHT_SM))
    kwargs.setdefault('padding', [dp(SPACING_MD), dp(SPACING_LG)])
    kwargs.setdefault('readonly', True)
    kwargs.setdefault('multiline', False)
    kwargs.setdefault('background_color', INPUT_BACKGROUND)
    kwargs.setdefault('foreground_color', TEXT_DARK)
    return TextInput(text=text, **kwargs)


def CodeInput(**kwargs: Any) -> TextInput:
    """Text input for entering puzzle codes."""
    kwargs.setdefault('multiline', False)
    kwargs.setdefault('font_name', FONT_NAME)
    kwargs.setdefault('font_size', '16sp')
    kwargs.setdefault('size_hint_y', None)
    kwargs.setdefault('height', dp(BUTTON_HEIGHT))
    kwargs.setdefault('padding', [dp(SPACING_LG), dp(SPACING_XL)])
    kwargs.setdefault('background_color', INPUT_BACKGROUND)
    kwargs.setdefault('foreground_color', TEXT_HEADER)
    kwargs.setdefault('cursor_color', TEXT_DARK)
    kwargs.setdefault('hint_text', 'Enter code here...')
    kwargs.setdefault('hint_text_color', INPUT_HINT_COLOR)
    return TextInput(**kwargs)


def LinkButton(text: str, **kwargs: Any) -> Button:
    """Transparent button styled as a link."""
    kwargs.setdefault('font_name', FONT_NAME)
    kwargs.setdefault('font_size', '12sp')
    kwargs.setdefault('size_hint_y', None)
    kwargs.setdefault('height', dp(LINK_HEIGHT))
    kwargs.setdefault('background_color', (0, 0, 0, 0))
    kwargs.setdefault('color', LINK_COLOR)
    return Button(text=text, **kwargs)


def SmallRoundedButton(**kwargs: Any) -> RoundedButton:
    """Smaller rounded button for compact UI elements."""
    kwargs.setdefault('font_size', '14sp')
    return RoundedButton(**kwargs)


class SelectableButton(RoundedButton):
    """A button that can be selected/deselected with visual feedback.

    Use with SelectableButtonGroup for radio-style selection.
    """

    def __init__(self, selected: bool = False, **kwargs: Any) -> None:
        from ui_constants import BUTTON_UNSELECTED
        # Set initial colors based on selected state
        if not selected:
            kwargs.setdefault('bg_color', BUTTON_UNSELECTED)
        super().__init__(**kwargs)
        self._selected = selected

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool) -> None:
        from ui_constants import BUTTON_UNSELECTED
        self._selected = value
        if value:
            self.bg_color = DEFAULT_BUTTON_COLOR_DOWN
        else:
            self.bg_color = BUTTON_UNSELECTED
        self._update_bg()


class SelectableButtonGroup:
    """Manages a group of SelectableButtons for radio-style selection."""

    def __init__(self, on_select: Callable[[Any], None] | None = None) -> None:
        self.buttons: dict[Any, SelectableButton] = {}
        self.selected_value: Any = None
        self.on_select = on_select

    def add(self, value: Any, button: SelectableButton) -> None:
        """Add a button to the group with associated value."""
        self.buttons[value] = button
        button.bind(on_press=lambda btn: self.select(value))
        if button.selected:
            self.selected_value = value

    def select(self, value: Any) -> None:
        """Select a button by its value."""
        self.selected_value = value
        for v, btn in self.buttons.items():
            btn.selected = (v == value)
        if self.on_select:
            self.on_select(value)


def BackButton(**kwargs: Any) -> RoundedButton:
    """Standard back button with fixed height."""
    kwargs.setdefault('text', 'Back')
    kwargs.setdefault('font_size', '18sp')
    return FixedGrayRoundedButton(**kwargs)


def StatusLabel(text: str, **kwargs: Any) -> Label:
    """Centered status label for loading popups."""
    kwargs.setdefault('font_size', '16sp')
    kwargs.setdefault('halign', 'center')
    kwargs.setdefault('valign', 'middle')
    label = styled_label('title_sm', text, height=45, **kwargs)
    label.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
    return label
