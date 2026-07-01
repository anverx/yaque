"""SolutionIndicator: solution-cycling dots (game-specific).

Inputs (UrlInput/CodeInput) live in kivyshell.uikit.inputs; import them from
there directly where needed.
"""

from __future__ import annotations

from typing import Any

from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivy.uix.widget import Widget

from ui_constants import (
    INDICATOR_CIRCLE_SIZE,
    INDICATOR_CURRENT,
    INDICATOR_OTHER,
    INDICATOR_SPACING,
)


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
            circle_size = dp(INDICATOR_CIRCLE_SIZE)
            spacing = dp(INDICATOR_SPACING)
            total_width = self.num_solutions * circle_size + (self.num_solutions - 1) * (spacing - circle_size)
            start_x = self.center_x - total_width / 2

            for i in range(self.num_solutions):
                cx = start_x + i * spacing
                cy = self.center_y - circle_size / 2
                Color(*(INDICATOR_CURRENT if i == self.current_index else INDICATOR_OTHER))
                Ellipse(pos=(cx, cy), size=(circle_size, circle_size))
