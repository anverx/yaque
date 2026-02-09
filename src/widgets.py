"""Shared UI widgets for Yaque."""

from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

from ui_constants import (
    FONT_NAME,
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
    return RoundedButton(
        bg_color=GRAY_BUTTON_COLOR,
        bg_color_down=GRAY_BUTTON_COLOR_DOWN,
        **kwargs
    )
