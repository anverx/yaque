"""Bar chart widget for Yaque."""

from __future__ import annotations

from typing import Any

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from ui_constants import (
    DEFAULT_BUTTON_COLOR,
    FONT_NAME,
    RADIUS_SM,
    TEXT_LIGHT,
)


class BarChart(BoxLayout):
    """A simple vertical bar chart with date labels.

    Args:
        data: List of (label, value) tuples.
        bar_color: Color tuple for the bars.
    """

    def __init__(
        self,
        data: list[tuple[str, int]],
        bar_color: tuple[float, ...] = DEFAULT_BUTTON_COLOR,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('size_hint_y', None)
        super().__init__(**kwargs)
        self.data = data
        self.bar_color = bar_color
        self.height = dp(180)

        # Bar area (draws bars on canvas)
        self._bar_area = _BarArea(data=data, bar_color=bar_color, size_hint_y=1)
        self.add_widget(self._bar_area)

        # Date labels row
        label_row = BoxLayout(size_hint_y=None, height=dp(14))
        if data:
            # Show a few evenly spaced date labels
            n = len(data)
            label_positions = [0, n // 4, n // 2, 3 * n // 4, n - 1]
            # Remove duplicates while preserving order
            seen = set()
            unique_positions = []
            for p in label_positions:
                if p not in seen:
                    seen.add(p)
                    unique_positions.append(p)

            # Build label row with spacers
            prev = 0
            for pos in unique_positions:
                if pos > prev:
                    label_row.add_widget(Widget(size_hint_x=pos - prev))
                date_str = data[pos][0]
                # Show as "Mar 5" format
                month_day = date_str[5:]  # "MM-DD"
                parts = month_day.split('-')
                months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                short = f"{months[int(parts[0])]} {int(parts[1])}"
                lbl = Label(
                    text=short,
                    font_name=FONT_NAME,
                    font_size='9sp',
                    color=TEXT_LIGHT,
                    size_hint_x=1,
                    halign='center',
                )
                lbl.bind(size=lbl.setter('text_size'))
                label_row.add_widget(lbl)
                prev = pos + 1
            remaining = n - prev
            if remaining > 0:
                label_row.add_widget(Widget(size_hint_x=remaining))

        self.add_widget(label_row)


class _BarArea(Widget):
    """Canvas-based bar rendering area."""

    def __init__(self, data: list[tuple[str, int]], bar_color: tuple[float, ...], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.data = data
        self.bar_color = bar_color
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args: Any) -> None:
        self.canvas.clear()
        if not self.data:
            return

        max_val = max(v for _, v in self.data)
        if max_val == 0:
            return

        n = len(self.data)
        bar_width = self.width / n
        gap = max(dp(1), bar_width * 0.15)
        actual_bar_w = bar_width - gap
        radius = min(dp(RADIUS_SM), actual_bar_w / 2)

        with self.canvas:
            for i, (_, val) in enumerate(self.data):
                if val == 0:
                    continue
                bar_h = (val / max_val) * self.height * 0.9
                x = self.x + i * bar_width + gap / 2
                y = self.y

                Color(*self.bar_color)
                RoundedRectangle(
                    pos=(x, y),
                    size=(actual_bar_w, bar_h),
                    radius=[radius, radius, 0, 0],
                )
