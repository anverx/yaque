"""Spinner widgets for loading indicators."""

from __future__ import annotations

import os
from typing import Any

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Ellipse, Line, PopMatrix, PushMatrix, Rectangle, Rotate
from kivy.metrics import dp
from kivy.uix.widget import Widget

from ui_constants import COLOR_WHITE, SPINNER_BORDER, SPINNER_LINE_WIDTH

# Path to icons
ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')


class QueenSpinner(Widget):
    """Animated spinning queen widget for loading indicators."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.rotation_angle: float = 0
        self.queen_texture = CoreImage(os.path.join(ICONS_DIR, 'queen.png')).texture
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args: Any) -> None:
        """Draw the spinner."""
        self.canvas.clear()

        w, h = self.size
        x, y = self.pos
        cx, cy = x + w / 2, y + h / 2

        circle_radius = min(w, h) / 2 * 0.7
        queen_size = circle_radius * 1.3

        with self.canvas:
            # White circle background
            Color(*COLOR_WHITE)
            Ellipse(pos=(cx - circle_radius, cy - circle_radius),
                    size=(circle_radius * 2, circle_radius * 2))

            # Light gray border
            Color(*SPINNER_BORDER)
            Line(ellipse=(cx - circle_radius, cy - circle_radius,
                          circle_radius * 2, circle_radius * 2), width=dp(SPINNER_LINE_WIDTH))

            # Spinning queen
            PushMatrix()
            Rotate(angle=self.rotation_angle, origin=(cx, cy))
            Color(*COLOR_WHITE)
            Rectangle(
                pos=(cx - queen_size / 2, cy - queen_size / 2),
                size=(queen_size, queen_size),
                texture=self.queen_texture
            )
            PopMatrix()

    def rotate(self, angle_delta: float = 3) -> None:
        """Rotate the queen by the given angle."""
        self.rotation_angle = (self.rotation_angle + angle_delta) % 360
        self._draw()

    def reset(self) -> None:
        """Reset rotation to initial position."""
        self.rotation_angle = 0
        self._draw()
