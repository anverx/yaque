"""Shared UI widgets for Yaque."""

from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

from ui_constants import (
    FONT_NAME, TEXT_WHITE, TEXT_DARK, TEXT_LIGHT, TEXT_MEDIUM,
    DEFAULT_BUTTON_COLOR, DEFAULT_BUTTON_COLOR_DOWN,
    GRAY_BUTTON_COLOR, GRAY_BUTTON_COLOR_DOWN
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
# Label Factories
# -----------------------------------------------------------------------------

def StyledLabel(**kwargs):
    """Base styled label with app font. All other label factories use this."""
    kwargs.setdefault('font_name', FONT_NAME)
    kwargs.setdefault('color', TEXT_DARK)
    return Label(**kwargs)


def TitleLabel(text, font_size='18sp', height=35, **kwargs):
    """Large title label for popups and screen headers.

    Defaults: font_size='18sp', color=TEXT_DARK, size_hint_y=None, height=dp(35)
    """
    kwargs.setdefault('color', TEXT_DARK)
    return StyledLabel(
        text=text,
        font_size=font_size,
        size_hint_y=None,
        height=dp(height),
        **kwargs
    )


def SubtitleLabel(text, font_size='14sp', height=25, **kwargs):
    """Secondary text label for instructions and descriptions.

    Defaults: font_size='14sp', color=TEXT_LIGHT, size_hint_y=None, height=dp(25)
    """
    kwargs.setdefault('color', TEXT_LIGHT)
    return StyledLabel(
        text=text,
        font_size=font_size,
        size_hint_y=None,
        height=dp(height),
        **kwargs
    )


def CaptionLabel(text, font_size='12sp', **kwargs):
    """Small text label for captions, table headers, and metadata.

    Defaults: font_size='12sp', color=TEXT_MEDIUM
    """
    kwargs.setdefault('color', TEXT_MEDIUM)
    return StyledLabel(
        text=text,
        font_size=font_size,
        **kwargs
    )
