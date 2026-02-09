"""Shared UI widgets for Yaque."""

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput
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
    BUTTON_HEIGHT, BUTTON_HEIGHT_SM, RADIUS_MD, LINK_HEIGHT,
)

BUTTON_RADIUS = dp(RADIUS_MD)


class RoundedButton(ButtonBehavior, Label):
    """A button with rounded corners. Use in ButtonRow or containers.

    Args:
        bg_color: Background color tuple (r, g, b, a). Defaults to salad green.
        bg_color_down: Pressed background color. Defaults to darker shade.
    """
    def __init__(self, bg_color=None, bg_color_down=None, **kwargs):
        kwargs.setdefault('font_name', FONT_NAME)
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

    def _update_text_size(self, *args):
        self.text_size = self.size

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*self.bg_color_down)
            else:
                Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[BUTTON_RADIUS])


def GrayRoundedButton(**kwargs):
    """Factory for gray rounded buttons in containers."""
    kwargs.setdefault('color', TEXT_DARK)
    return RoundedButton(
        bg_color=GRAY_BUTTON_COLOR,
        bg_color_down=GRAY_BUTTON_COLOR_DOWN,
        **kwargs
    )


def FixedRoundedButton(**kwargs):
    """Factory for standalone buttons with fixed height."""
    kwargs.setdefault('size_hint_y', None)
    return RoundedButton(**kwargs)


def FixedGrayRoundedButton(**kwargs):
    """Factory for standalone gray buttons with fixed height."""
    kwargs.setdefault('size_hint_y', None)
    return GrayRoundedButton(**kwargs)


# -----------------------------------------------------------------------------
# Label Factory (CSS-like: styles defined in ui_constants.LABEL_STYLES)
# -----------------------------------------------------------------------------

def styled_label(style='default', text='', **overrides):
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
def StyledLabel(**kwargs):
    """Base styled label with app font."""
    return styled_label('default', **kwargs)


def TitleLgLabel(text, **kwargs):
    """Large title label for screen headers (24sp)."""
    return styled_label('title_lg', text, **kwargs)


def TitleMdLabel(text, **kwargs):
    """Medium title label for section headers (20sp)."""
    return styled_label('title_md', text, **kwargs)


def TitleLabel(text, **kwargs):
    """Title label for popups and screen headers (18sp)."""
    return styled_label('title', text, **kwargs)


def TitleSmLabel(text, **kwargs):
    """Small title label for game screen headers (16sp)."""
    return styled_label('title_sm', text, **kwargs)


def SubtitleLabel(text, **kwargs):
    """Subtitle label for descriptions (14sp)."""
    return styled_label('subtitle', text, **kwargs)


def CaptionLabel(text, **kwargs):
    """Caption label for small text and metadata (12sp)."""
    return styled_label('caption', text, **kwargs)


def MonthLabel(text, **kwargs):
    """Month/year display label for calendar (22sp)."""
    return styled_label('month', text, **kwargs)


def DayLabel(text, **kwargs):
    """Day name/number label for calendar (14sp)."""
    return styled_label('day', text, **kwargs)


def TableHeaderLabel(text, **kwargs):
    """Table column header label (11sp)."""
    return styled_label('table_header', text, **kwargs)


def TableCellLabel(text, **kwargs):
    """Table cell data label (13sp)."""
    return styled_label('table_cell', text, **kwargs)


def ClockLabel(text='00:00', **kwargs):
    """Large clock/timer display label (36sp)."""
    return styled_label('clock', text, **kwargs)


def IconLabel(text, **kwargs):
    """Tiny label for icon button captions (9sp)."""
    return styled_label('icon_label', text, **kwargs)


def AboutTitleLabel(text, **kwargs):
    """Large title for About popup (28sp)."""
    return styled_label('about_title', text, **kwargs)


def AboutSubtitleLabel(text, **kwargs):
    """Subtitle for About popup (16sp)."""
    return styled_label('about_subtitle', text, **kwargs)


# -----------------------------------------------------------------------------
# Layout Factories
# -----------------------------------------------------------------------------

def PopupContent(**kwargs):
    """Vertical BoxLayout with popup padding/spacing defaults."""
    kwargs.setdefault('orientation', 'vertical')
    kwargs.setdefault('padding', [dp(PADDING_POPUP[0]), dp(PADDING_POPUP[1])])
    kwargs.setdefault('spacing', dp(SPACING_LG))
    return BoxLayout(**kwargs)


def styled_layout(style='button_row', **overrides):
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


def ButtonRow(**kwargs):
    """Horizontal BoxLayout for button rows with standard height/spacing."""
    return styled_layout('button_row', **kwargs)


def SizeButtonRow(**kwargs):
    """Horizontal BoxLayout for size selection buttons (taller)."""
    return styled_layout('size_button_row', **kwargs)


def Popup(content, height, width_hint=POPUP_WIDTH, auto_dismiss=True):
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

def UrlInput(text, **kwargs):
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


def CodeInput(**kwargs):
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


def LinkButton(text, **kwargs):
    """Transparent button styled as a link."""
    kwargs.setdefault('font_name', FONT_NAME)
    kwargs.setdefault('font_size', '12sp')
    kwargs.setdefault('size_hint_y', None)
    kwargs.setdefault('height', dp(LINK_HEIGHT))
    kwargs.setdefault('background_color', (0, 0, 0, 0))
    kwargs.setdefault('color', LINK_COLOR)
    return Button(text=text, **kwargs)


def SmallRoundedButton(**kwargs):
    """Smaller rounded button for compact UI elements."""
    kwargs.setdefault('font_size', '14sp')
    return RoundedButton(**kwargs)


def BackButton(**kwargs):
    """Standard back button with fixed height."""
    kwargs.setdefault('text', 'Back')
    kwargs.setdefault('font_size', '18sp')
    return FixedGrayRoundedButton(**kwargs)


def StatusLabel(text, **kwargs):
    """Centered status label for loading popups."""
    kwargs.setdefault('font_size', '16sp')
    kwargs.setdefault('halign', 'center')
    kwargs.setdefault('valign', 'middle')
    label = styled_label('title_sm', text, height=45, **kwargs)
    label.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
    return label
