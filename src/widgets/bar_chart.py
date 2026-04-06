"""Bar chart widget for Yaque."""

from __future__ import annotations

from typing import Any

from kivy.graphics import Color, Line, RoundedRectangle
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

_Y_AXIS_WIDTH = dp(28)

# Colors for stacked bar segments by board size
SIZE_COLORS = {
    6: (0.55, 0.85, 0.55, 0.85),  # Light green
    7: (0.55, 0.70, 0.95, 0.85),  # Light blue
    8: (0.90, 0.65, 0.55, 0.85),  # Light coral
}
_DEFAULT_SEGMENT_COLOR = (1, 1, 1, 0.85)


class BarChart(BoxLayout):
    """A vertical bar chart with axis labels and guide lines.

    Args:
        data: List of (label, {size: count}) tuples for stacked bars,
              or list of (label, int) tuples for simple bars.
        bar_color: Color tuple for simple (non-stacked) bars.
    """

    def __init__(
        self,
        data: list[tuple[str, dict[int, int] | int]],
        bar_color: tuple[float, ...] = DEFAULT_BUTTON_COLOR,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('size_hint_y', None)
        super().__init__(**kwargs)
        self.data = data
        self.bar_color = bar_color
        self.height = dp(180)

        # Compute max total value per day
        max_val = 0
        for _, val in data:
            if isinstance(val, dict):
                max_val = max(max_val, sum(val.values()))
            else:
                max_val = max(max_val, val)

        # Main row: Y-axis labels + bar area
        chart_row = BoxLayout(orientation='horizontal', size_hint_y=1)

        y_axis = _YAxis(max_val=max_val, size_hint_x=None, width=_Y_AXIS_WIDTH)
        chart_row.add_widget(y_axis)

        bar_area = _BarArea(data=data, bar_color=bar_color, max_val=max_val, size_hint_y=1)
        chart_row.add_widget(bar_area)

        self.add_widget(chart_row)

        # Bottom row: spacer for Y-axis width + date labels
        bottom_row = BoxLayout(size_hint_y=None, height=dp(14))
        bottom_row.add_widget(Widget(size_hint_x=None, width=_Y_AXIS_WIDTH))

        label_row = BoxLayout(size_hint_x=1)
        if data:
            n = len(data)
            label_positions = [0, n // 4, n // 2, 3 * n // 4, n - 1]
            seen = set()
            unique_positions = []
            for p in label_positions:
                if p not in seen:
                    seen.add(p)
                    unique_positions.append(p)

            prev = 0
            for pos in unique_positions:
                if pos > prev:
                    label_row.add_widget(Widget(size_hint_x=pos - prev))
                date_str = data[pos][0]
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

        bottom_row.add_widget(label_row)
        self.add_widget(bottom_row)


class _YAxis(Widget):
    """Vertical axis labels at 0%, 25%, 50%, 75%, 100% of max value."""

    def __init__(self, max_val: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_val = max_val
        self._labels: list[tuple[float, Label]] = []

        if max_val == 0:
            return

        # Deduplicate labels when max_val is small
        seen_vals = set()
        fracs = []
        for frac in [0, 0.25, 0.5, 0.75, 1.0]:
            val = int(max_val * frac)
            if val not in seen_vals:
                seen_vals.add(val)
                fracs.append((frac, val))

        for frac, val in fracs:
            lbl = Label(
                text=str(val),
                font_name=FONT_NAME,
                font_size='9sp',
                color=TEXT_LIGHT,
                size_hint=(None, None),
                halign='right',
                valign='middle',
            )
            lbl.size = (self.width, dp(12))
            lbl.text_size = lbl.size
            self._labels.append((frac, lbl))
            self.add_widget(lbl)

        self.bind(pos=self._layout, size=self._layout)

    def _layout(self, *args: Any) -> None:
        chart_h = self.height * 0.9
        for frac, lbl in self._labels:
            lbl.size = (self.width - dp(3), dp(12))
            lbl.text_size = lbl.size
            y = self.y + frac * chart_h - dp(6)
            lbl.pos = (self.x, y)


class _BarArea(Widget):
    """Canvas-based bar rendering area with guide lines."""

    def __init__(self, data: list[tuple[str, dict[int, int] | int]],
                 bar_color: tuple[float, ...],
                 max_val: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.data = data
        self.bar_color = bar_color
        self.max_val = max_val
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args: Any) -> None:
        self.canvas.clear()
        if not self.data or self.max_val == 0:
            return

        max_val = self.max_val
        chart_h = self.height * 0.9

        n = len(self.data)
        bar_width = self.width / n
        gap = max(dp(1), bar_width * 0.15)
        actual_bar_w = bar_width - gap
        radius = min(dp(RADIUS_SM), actual_bar_w / 2)

        with self.canvas:
            # Guide lines at 25%, 50%, 75%, 100%
            for frac in [0, 0.25, 0.5, 0.75, 1.0]:
                y = self.y + frac * chart_h
                Color(1, 1, 1, 0.2)
                Line(points=[self.x, y, self.x + self.width, y], width=1)

            # Bars
            for i, (_, val) in enumerate(self.data):
                x = self.x + i * bar_width + gap / 2

                if isinstance(val, dict):
                    # Stacked bar: draw segments bottom-to-top
                    y_offset = self.y
                    total = sum(val.values())
                    if total == 0:
                        continue
                    # Sort by size for consistent stacking order
                    segments = sorted(val.items())
                    for j, (size, count) in enumerate(segments):
                        if count == 0:
                            continue
                        seg_h = (count / max_val) * chart_h
                        color = SIZE_COLORS.get(size, _DEFAULT_SEGMENT_COLOR)
                        Color(*color)
                        # Top segment gets rounded corners
                        is_top = j == len(segments) - 1 or all(
                            val.get(s, 0) == 0 for s, _ in segments[j + 1:]
                        )
                        r = [radius, radius, 0, 0] if is_top else [0, 0, 0, 0]
                        RoundedRectangle(
                            pos=(x, y_offset),
                            size=(actual_bar_w, seg_h),
                            radius=r,
                        )
                        y_offset += seg_h
                else:
                    # Simple bar
                    if val == 0:
                        continue
                    bar_h = (val / max_val) * chart_h
                    Color(*self.bar_color)
                    RoundedRectangle(
                        pos=(x, self.y),
                        size=(actual_bar_w, bar_h),
                        radius=[radius, radius, 0, 0],
                    )
