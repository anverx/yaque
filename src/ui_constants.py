# UI Constants - centralized colors and dimensions

# Text colors
TEXT_DARK = (0.3, 0.3, 0.3, 1)
TEXT_MEDIUM = (0.5, 0.5, 0.5, 1)
TEXT_LIGHT = (0.4, 0.4, 0.4, 1)
TEXT_HEADER = (0.2, 0.2, 0.2, 1)
TEXT_WHITE = (1, 1, 1, 1)

# Background colors
OVERLAY_WHITE = (1, 1, 1, 0.7)
ROW_BACKGROUND = (1, 1, 1, 0.7)
ROW_PRESSED = (0.9, 0.9, 0.9, 1)

# Crown/queen icon colors (for calendar, logbook)
QUEEN_GRAY = (0.5, 0.5, 0.5, 0.3)  # Not completed / random
QUEEN_GOLD = (1.0, 0.84, 0.0, 1)   # Solved on the same day
QUEEN_SILVER = (0.85, 0.88, 0.95, 1)  # Solved on a later day

# Calendar colors
TODAY_HIGHLIGHT = (0.4, 0.7, 0.9, 1)

# Common dimensions (as raw values, use with dp())
TOP_SPACER_HEIGHT = 70
BUTTON_HEIGHT = 48
BACK_BUTTON_HEIGHT = 48

# Background image path
BACKGROUND_IMAGE = 'assets/images/splashscreen.jpg'

# =============================================================================
# Board Widget Colors
# =============================================================================

# Basic colors
COLOR_BLACK = (0, 0, 0, 1)
COLOR_WHITE = (1, 1, 1, 1)

# Hidden board colors
BOARD_HIDDEN_BG = (0.85, 0.85, 0.85, 1)
BOARD_HIDDEN_GRID = (0.7, 0.7, 0.7, 1)
BOARD_HIDDEN_BORDER = (0.5, 0.5, 0.5, 1)

# Board grid colors
BOARD_CELL_BORDER = (0.5, 0.5, 0.5, 1)
BOARD_KINGDOM_BORDER = (0, 0, 0, 1)

# Queen/mark colors on board
BOARD_QUEEN_NORMAL = (1, 1, 1, 1)
BOARD_QUEEN_GOLDEN = (1.0, 0.85, 0.2, 1)
BOARD_QUEEN_CONFLICT = (0.9, 0.3, 0.3, 1)
BOARD_QUEEN_SOLUTION = (0.5, 0.5, 1, 0.8)  # Blue tint for solution display

# Circle mark colors
BOARD_CIRCLE_NORMAL = (0.4, 0.4, 0.4, 1)
BOARD_CIRCLE_BLOCKED = (0.9, 0.3, 0.3, 1)

# Solution indicator colors
INDICATOR_CURRENT = (1.0, 0.85, 0.2, 1)  # Golden for current solution
INDICATOR_OTHER = (0.7, 0.7, 0.7, 1)     # Gray for other solutions

# Kingdom colors (RGB, 0-1 range)
KINGDOM_COLORS = [
    (0.9, 0.6, 0.6),   # 0: light red
    (0.6, 0.9, 0.6),   # 1: light green
    (0.6, 0.6, 0.9),   # 2: light blue
    (0.9, 0.9, 0.6),   # 3: light yellow
    (0.9, 0.6, 0.9),   # 4: light magenta
    (0.6, 0.9, 0.9),   # 5: light cyan
    (0.9, 0.8, 0.6),   # 6: light orange
    (0.8, 0.6, 0.9),   # 7: light purple
    (0.6, 0.8, 0.7),   # 8: light teal
    (0.85, 0.7, 0.7),  # 9: dusty rose
]
