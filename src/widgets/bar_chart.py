"""Shim — BarChart now lives in ``kivyshell.uikit.charts``.

yaque colors stacked bar segments by board size; it binds that palette
(SIZE_COLORS) here so the logbook activity charts render exactly as before while
the chart itself stays game-agnostic.
"""

from __future__ import annotations

from typing import Any

from kivyshell.uikit.charts import BarChart as _BarChart

# Stacked bar segment colors by board size.
SIZE_COLORS = {
    6: (0.55, 0.85, 0.55, 0.85),  # light green
    7: (0.55, 0.70, 0.95, 0.85),  # light blue
    8: (0.90, 0.65, 0.55, 0.85),  # light coral
}


def BarChart(data: list[tuple[str, dict[int, int] | int]], **kwargs: Any) -> _BarChart:
    kwargs.setdefault("segment_colors", SIZE_COLORS)
    return _BarChart(data, **kwargs)
