"""Core UI widgets for Yaque — inputs and indicators."""

from __future__ import annotations

from typing import Any

from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from ui_constants import (
    INDICATOR_CIRCLE_SIZE,
    INDICATOR_CURRENT,
    INDICATOR_OTHER,
    INDICATOR_SPACING,
)
from widgets.labels import styled

# -----------------------------------------------------------------------------
# Input Factories
# -----------------------------------------------------------------------------

def UrlInput(text: str, **kwargs: Any) -> TextInput:
    """Readonly text input for displaying URLs (small font, selectable)."""
    return styled(TextInput, 'url_input', text=text, **kwargs)


def CodeInput(**kwargs: Any) -> TextInput:
    """Text input for entering puzzle codes."""
    kwargs.setdefault('hint_text', 'Enter code here...')
    return styled(TextInput, 'code_input', **kwargs)


# -----------------------------------------------------------------------------
# Solution Indicator
# -----------------------------------------------------------------------------

class SolutionIndicator(Widget):
    """Shows gray circles for each solution with a golden indicator for current."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.num_solutions = 0
        self.current_index = 0
        self.bind(pos=self._draw, size=self._draw)

    def set_solutions(self, num_solutions: int, current_index: int = 0) -> None:
        self.num_solutions = num_solutions
        self.current_index = current_index
        self._draw()

    def set_current(self, index: int) -> None:
        self.current_index = index
        self._draw()

    def _draw(self, *args: Any) -> None:
        self.canvas.clear()
        if self.num_solutions <= 1:
            return

        with self.canvas:
            # Calculate circle positions (centered)
            circle_size = dp(INDICATOR_CIRCLE_SIZE)
            spacing = dp(INDICATOR_SPACING)
            total_width = self.num_solutions * circle_size + (self.num_solutions - 1) * (spacing - circle_size)
            start_x = self.center_x - total_width / 2

            for i in range(self.num_solutions):
                cx = start_x + i * spacing
                cy = self.center_y - circle_size / 2

                if i == self.current_index:
                    Color(*INDICATOR_CURRENT)
                    Ellipse(pos=(cx, cy), size=(circle_size, circle_size))
                else:
                    Color(*INDICATOR_OTHER)
                    Ellipse(pos=(cx, cy), size=(circle_size, circle_size))
