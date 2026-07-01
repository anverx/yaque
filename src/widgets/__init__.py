"""yaque game-specific widgets.

The reusable UI primitives now live in ``kivyshell.uikit`` and are imported from
there directly. This package holds only the widgets specific to the Queens game:
  - board.BoardWidget       the puzzle board
  - layouts.DayCell / LogbookRow  calendar cell + logbook row (yaque data shapes)
  - core.SolutionIndicator  solution-cycling dots
  - bar_chart.BarChart      thin wrapper binding yaque's per-size segment colors
"""
