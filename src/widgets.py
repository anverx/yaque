"""Shared UI widgets for Yaque."""

from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

from ui_constants import (
    FONT_NAME, TEXT_WHITE, TEXT_DARK,
    DEFAULT_BUTTON_COLOR, DEFAULT_BUTTON_COLOR_DOWN,
    GRAY_BUTTON_COLOR, GRAY_BUTTON_COLOR_DOWN,
    LABEL_STYLES
)

BUTTON_RADIUS = dp(12)


class RoundedButton(ButtonBehavior, Label):
    """A button with rounded corners.

    Args:
        bg_color: Background color tuple (r, g, b, a). Defaults to salad green.
        bg_color_down: Pressed background color. Defaults to darker shade.
    """
    def __init__(self, bg_color=None, bg_color_down=None, **kwargs):
        kwargs.setdefault('font_name', FONT_NAME)
        kwargs.setdefault('color', TEXT_WHITE)
        super().__init__(**kwargs)
        self.bg_color = bg_color or DEFAULT_BUTTON_COLOR
        self.bg_color_down = bg_color_down or DEFAULT_BUTTON_COLOR_DOWN
        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*self.bg_color_down)
            else:
                Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[BUTTON_RADIUS])


def GrayRoundedButton(**kwargs):
    """Factory for gray rounded buttons (cancel buttons)."""
    kwargs.setdefault('color', TEXT_DARK)
    return RoundedButton(
        bg_color=GRAY_BUTTON_COLOR,
        bg_color_down=GRAY_BUTTON_COLOR_DOWN,
        **kwargs
    )


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


def TitleLabel(text, **kwargs):
    """Title label for popups and screen headers."""
    return styled_label('title', text, **kwargs)


def SubtitleLabel(text, **kwargs):
    """Subtitle label for descriptions."""
    return styled_label('subtitle', text, **kwargs)


def CaptionLabel(text, **kwargs):
    """Caption label for small text and metadata."""
    return styled_label('caption', text, **kwargs)
