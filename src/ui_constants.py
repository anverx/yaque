# UI Constants - centralized colors, dimensions, and fonts

from kivy.metrics import dp

# Window settings
WINDOW_SIZE = (360, 640)  # Logical phone resolution for desktop testing
WINDOW_CLEARCOLOR = (0.95, 0.95, 0.95, 1)  # Light background

# Font
FONT_NAME = 'DMSansBlack'

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

# Button colors
DEFAULT_BUTTON_COLOR = (0.55, 0.78, 0.4, 1)       # Salad green
DEFAULT_BUTTON_COLOR_DOWN = (0.45, 0.68, 0.3, 1)  # Darker salad green (also used for selected state)
GRAY_BUTTON_COLOR = (0.75, 0.75, 0.75, 1)
GRAY_BUTTON_COLOR_DOWN = (0.6, 0.6, 0.6, 1)
BUTTON_UNSELECTED = (0.7, 0.7, 0.7, 1)            # Unselected toggle button

# Popup colors
POPUP_BACKGROUND = (1, 1, 1, 0.95)

# Input field colors
INPUT_BACKGROUND = (0.95, 0.95, 0.95, 1)
INPUT_HINT_COLOR = (0.6, 0.6, 0.6, 1)

# Status/feedback colors
STATUS_SUCCESS = (0.2, 0.6, 0.2, 1)  # Green for success messages
STATUS_ERROR = (0.8, 0.2, 0.2, 1)    # Red for error messages

# Spinner colors
SPINNER_BORDER = (0.8, 0.8, 0.8, 1)

# =============================================================================
# Dimensions (raw values, use with dp())
# =============================================================================

# Spacing scale
SPACING_MIN = 1
SPACING_XS = 2
SPACING_SM = 4
SPACING_MD = 8
SPACING_LG = 10
SPACING_XL = 15
SPACING_XXL = 20

# Padding presets (horizontal, vertical)
PADDING_POPUP = (15, 10)
PADDING_POPUP_LARGE = (20, 15)
PADDING_ROW = (10, 5)
PADDING_CELL = (2, 2)

# Button dimensions
BUTTON_HEIGHT_SM = 40
BUTTON_HEIGHT = 48
BUTTON_HEIGHT_LG = 58
BUTTON_FONT_SIZE = '22sp'  # 50% larger than default 15sp

# Layout heights
TOP_SPACER_HEIGHT = 70
HEADER_HEIGHT = 50
ROW_HEIGHT = 50
CELL_HEIGHT = 52
NAV_BUTTON_WIDTH = 50
DAYS_HEADER_HEIGHT = 30
DATE_SEPARATOR_HEIGHT = 30
TABLE_HEADER_HEIGHT = 20
CAPTION_HEIGHT = 22
CAPTION_HEIGHT_SM = 18
CAPTION_HEIGHT_XS = 20
LINK_HEIGHT = 30
SPACER_SM = 5

# Popup-specific dimensions
QR_IMAGE_HEIGHT = 180
SMALL_BUTTON_WIDTH = 100
SPINNER_LINE_WIDTH = 2

# Game screen dimensions
ICON_BTN_SIZE = 40
ICON_BTN_SIZE_LG = 56
CONTROL_BAR_HEIGHT = 56
PLAY_AREA_HEIGHT = 72
INDICATOR_HEIGHT = 20
INDICATOR_CIRCLE_SIZE = 8
INDICATOR_SPACING = 14
INDICATOR_DOT_HEIGHT = 12
SUBTITLE_HEIGHT = 24
SOLUTIONS_BTN_WIDTH = 120
SOLUTIONS_BTN_HEIGHT = 40
SOLUTIONS_BTN_AREA_HEIGHT = 44
ICON_LABEL_HEIGHT = 12
ICON_LABEL_TOTAL = 14  # Height + padding

# Touch/gesture thresholds
SWIPE_EDGE_THRESHOLD = 20
SWIPE_DISTANCE_THRESHOLD = 100

# Popup dimensions (size_hint_x values)
POPUP_WIDTH = 0.85
POPUP_WIDTH_NARROW = 0.7

# Border radius
RADIUS_SM = 8
RADIUS_MD = 12

# Background image path
BACKGROUND_IMAGE = 'assets/images/splashscreen.jpg'

# Link color (for clickable text)
LINK_COLOR = (0.2, 0.5, 0.8, 1)

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

# =============================================================================
# Styles (CSS-like style definitions)
# =============================================================================
# Each style is a named set of properties that can be applied to any widget.
# 'height' and 'spacing' values are raw numbers (converted to dp by factory).
# Styles can be overridden at call site.

STYLES = {
    # Default label style
    'default': {
        'color': TEXT_DARK,
    },
    # Title variants (largest to smallest)
    'title_lg': {
        'font_size': '24sp',
        'color': TEXT_DARK,
        'size_hint_y': None,
        'height': 40,
    },
    'title_md': {
        'font_size': '20sp',
        'color': TEXT_DARK,
        'size_hint_y': None,
        'height': 40,
    },
    'title': {
        'font_size': '18sp',
        'color': TEXT_DARK,
        'size_hint_y': None,
        'height': 35,
    },
    'title_sm': {
        'font_size': '16sp',
        'color': TEXT_DARK,
        'size_hint_y': None,
        'height': 22,
    },
    'subtitle': {
        'font_size': '14sp',
        'color': TEXT_LIGHT,
        'size_hint_y': None,
        'height': 25,
    },
    'caption': {
        'font_size': '12sp',
        'color': TEXT_MEDIUM,
    },
    # Special styles
    'clock': {
        'font_size': '36sp',
        'color': COLOR_BLACK,
    },
    'month': {
        'font_size': '22sp',
        'color': TEXT_HEADER,
    },
    'day': {
        'font_size': '14sp',
    },
    # Table styles
    'table_header': {
        'font_size': '11sp',
        'color': TEXT_MEDIUM,
    },
    'table_cell': {
        'font_size': '13sp',
        'color': TEXT_DARK,
    },
    'icon_label': {
        'font_size': '9sp',
        'color': TEXT_MEDIUM,
    },
    # About popup styles
    'about_title': {
        'font_size': '28sp',
        'color': TEXT_DARK,
        'size_hint_y': None,
        'height': 40,
    },
    'about_subtitle': {
        'font_size': '16sp',
        'color': TEXT_LIGHT,
        'size_hint_y': None,
        'height': 25,
    },
    # Layout styles
    'button_row': {
        'size_hint_y': None,
        'height': BUTTON_HEIGHT,
        'spacing': SPACING_LG,
    },
    'size_button_row': {
        'size_hint_y': None,
        'height': ROW_HEIGHT,
        'spacing': SPACING_LG,
    },
    'selection_row': {
        'size_hint_y': None,
        'height': BUTTON_HEIGHT_SM,
        'spacing': SPACING_MD,
    },
    # Popup feedback areas
    'status_area': {
        'size_hint_y': None,
        'height': CAPTION_HEIGHT,
    },
    'timer_area': {
        'size_hint_y': None,
        'height': CAPTION_HEIGHT_SM,
    },
    # Selection button
    'selection_btn': {
        'font_size': '14sp',
    },
    # Small centered button (e.g., cancel in loading popup)
    'small_centered_btn': {
        'size_hint': (None, None),
        'width': SMALL_BUTTON_WIDTH,
        'height': BUTTON_HEIGHT_SM,
        'pos_hint': {'center_x': 0.5},
    },
    # QR code image
    'qr_image': {
        'size_hint_y': None,
        'height': QR_IMAGE_HEIGHT,
    },
    # Small vertical spacer
    'spacer_sm': {
        'size_hint_y': None,
        'height': SPACER_SM,
    },
    # Popup content layout
    'popup_content': {
        'orientation': 'vertical',
        'padding': [PADDING_POPUP[0], PADDING_POPUP[1]],
        'spacing': SPACING_LG,
    },
    # URL display input (readonly, small font)
    'url_input': {
        'font_size': '11sp',
        'size_hint_y': None,
        'height': BUTTON_HEIGHT_SM,
        'padding': [SPACING_MD, SPACING_LG],
        'readonly': True,
        'multiline': False,
        'background_color': INPUT_BACKGROUND,
        'foreground_color': TEXT_DARK,
    },
    # Code entry input
    'code_input': {
        'font_size': '16sp',
        'size_hint_y': None,
        'height': BUTTON_HEIGHT,
        'padding': [SPACING_LG, SPACING_XL],
        'multiline': False,
        'background_color': INPUT_BACKGROUND,
        'foreground_color': TEXT_HEADER,
        'cursor_color': TEXT_DARK,
        'hint_text_color': INPUT_HINT_COLOR,
    },
    # Link-style button (transparent background)
    'link_btn': {
        'font_size': '12sp',
        'size_hint_y': None,
        'height': LINK_HEIGHT,
        'background_color': (0, 0, 0, 0),
        'color': LINK_COLOR,
    },
    # Back button
    'back_btn': {
        'font_size': '18sp',
    },
    # Status label (centered, for loading popups)
    'status_label': {
        'font_size': '16sp',
        'halign': 'center',
        'valign': 'middle',
        'size_hint_y': None,
        'height': 45,
    },
    # Screen layouts
    'top_spacer': {
        'size_hint_y': None,
        'height': TOP_SPACER_HEIGHT,
    },
    'header_bar': {
        'size_hint_y': None,
        'height': HEADER_HEIGHT,
        'spacing': SPACING_LG,
    },
    # Calendar styles
    'nav_btn': {
        'size_hint_x': None,
        'width': NAV_BUTTON_WIDTH,
    },
    'days_header': {
        'cols': 7,
        'size_hint_y': None,
        'height': DAYS_HEADER_HEIGHT,
        'spacing': SPACING_XS,
    },
    'calendar_grid': {
        'cols': 7,
        'size_hint_y': None,
        'spacing': SPACING_SM,
    },
    'cell': {
        'size_hint_y': None,
        'height': CELL_HEIGHT,
    },
    # Logbook styles
    'logbook_row': {
        'size_hint_y': None,
        'height': ROW_HEIGHT,
        'padding': [PADDING_ROW[0], PADDING_ROW[1]],
        'spacing': SPACING_MD,
    },
    'date_separator': {
        'size_hint_y': None,
        'height': DATE_SEPARATOR_HEIGHT,
        'padding': [PADDING_ROW[0], PADDING_ROW[1]],
    },
    'table_header_row': {
        'size_hint_y': None,
        'height': TABLE_HEADER_HEIGHT,
        'padding': [PADDING_ROW[0], 0],
        'spacing': SPACING_MD,
    },
    'list_layout': {
        'orientation': 'vertical',
        'size_hint_y': None,
        'spacing': SPACING_XS,
        'padding': [0, PADDING_ROW[1]],
    },
    # Game screen styles
    'game_layout': {
        'orientation': 'vertical',
        'padding': SPACING_LG,
        'spacing': SPACING_SM,
    },
    'subtitle_area': {
        'size_hint_y': None,
        'height': SUBTITLE_HEIGHT,
    },
    'indicator_area': {
        'size_hint_y': None,
        'height': INDICATOR_HEIGHT,
    },
    'control_bar': {
        'size_hint': (None, None),
        'height': CONTROL_BAR_HEIGHT,
        'spacing': SPACING_XL,
    },
    'control_anchor': {
        'size_hint_y': None,
        'height': CONTROL_BAR_HEIGHT,
        'anchor_x': 'center',
    },
    'play_area': {
        'size_hint_y': None,
        'height': PLAY_AREA_HEIGHT,
        'anchor_x': 'center',
    },
    'solutions_btn': {
        'size_hint': (None, None),
        'width': SOLUTIONS_BTN_WIDTH,
        'height': SOLUTIONS_BTN_HEIGHT,
    },
    'solutions_btn_area': {
        'size_hint_y': None,
        'height': SOLUTIONS_BTN_AREA_HEIGHT,
        'anchor_x': 'center',
    },
}

# Pre-convert all dimension values in STYLES to dp units so that both
# styled() and direct **STYLES[...] unpacking produce correct sizing
# on all screen densities (especially Android).
for _style in STYLES.values():
    for _key in ('height', 'width', 'spacing'):
        if _key in _style and isinstance(_style[_key], (int, float)):
            _style[_key] = dp(_style[_key])
    if 'padding' in _style and isinstance(_style['padding'], (list, tuple)):
        _style['padding'] = [dp(_v) if isinstance(_v, (int, float)) else _v for _v in _style['padding']]

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
