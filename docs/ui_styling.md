# UI Styling System

Yaque's UI is built on Kivy primitives using a layered abstraction: raw constants at the bottom, a centralized style dictionary in the middle, and factory functions at the top. This document describes the principles and patterns used throughout.

## Architecture Overview

```
ui_constants.py          -- colors, dimensions, STYLES dict
    |
widgets/core.py          -- styled(), factories, base classes
    |
screens/, popups.py      -- concrete UI built from factories + styles
```

All visual properties (colors, sizes, spacing, fonts) live in `ui_constants.py`. Widgets never hardcode dimensions --- they pull from constants or STYLES.

## Density-Independent Pixels (dp)

Kivy's `dp()` converts logical pixels to physical pixels based on screen density. A value of `dp(48)` is ~48px on a 160dpi screen but ~96px on a 320dpi Android device.

**Rule:** Every dimension that reaches a widget must be in dp units. Raw integers are only used for declaration; conversion happens automatically.

STYLES values are pre-converted to dp at import time:

```python
# ui_constants.py (end of file)
for _style in STYLES.values():
    for _key in ('height', 'width', 'spacing'):
        if _key in _style and isinstance(_style[_key], (int, float)):
            _style[_key] = dp(_style[_key])
    if 'padding' in _style and isinstance(_style['padding'], (list, tuple)):
        _style['padding'] = [dp(_v) ... for _v in _style['padding']]
```

This means both consumption patterns produce correct sizing on all densities:

```python
# Via styled() factory
header = styled(BoxLayout, 'header_bar')

# Via direct unpacking
cell = DayCell(day=1, **STYLES['cell'])
```

The `styled()` function applies `_convert_dp_props()` only to caller-provided overrides (which arrive as raw numbers), not to the style dict itself (already converted).

## The STYLES Dictionary

STYLES is a flat dictionary of named property sets, similar to CSS classes. Each entry maps a name to a dict of Kivy widget properties:

```python
STYLES = {
    'title': {
        'font_size': '18sp',
        'color': TEXT_DARK,
        'size_hint_y': None,
        'height': 35,            # raw, converted to dp at import
    },
    'header_bar': {
        'size_hint_y': None,
        'height': HEADER_HEIGHT,  # raw constant
        'spacing': SPACING_LG,
    },
    'cell': {
        'size_hint_y': None,
        'height': CELL_HEIGHT,
    },
    ...
}
```

**Conventions:**

- `height`, `width`, `spacing` are raw integers (auto-converted to dp)
- `padding` is a list of raw integers (auto-converted element-wise)
- `font_size` uses sp strings (`'18sp'`) --- Kivy handles sp scaling
- `color` uses RGBA tuples in 0-1 range
- `size_hint_y: None` is required whenever an explicit `height` is set, otherwise Kivy's layout system ignores the height
- `size_hint: (None, None)` for widgets with both explicit width and height

## Style Consumption Patterns

There are three ways to apply styles, each with a specific use case.

### 1. `styled()` factory --- general-purpose

```python
header = styled(BoxLayout, 'header_bar')
label = styled(Label, 'cell', text='')
anchor = styled(AnchorLayout, 'play_area')
```

`styled(widget_class, style_name, **overrides)` fetches the style dict, merges in overrides (with dp conversion), and instantiates the widget. It also applies `font_name` for text widgets.

### 2. `**STYLES['name']` unpacking --- with custom widget classes

When a widget class has custom `__init__` parameters that `styled()` can't handle cleanly, unpack the style directly:

```python
cell = DayCell(day=day, completion_status=status, **STYLES['cell'])
btn = GrayRoundedButton(text='Cancel', **STYLES['small_centered_btn'])
```

Since STYLES values are pre-converted to dp, this is safe on all densities.

### 3. Convenience factories --- frequent widgets

For common widgets, named factories wrap `styled()`:

```python
title = TitleLabel('Hello')        # styled_label('title', 'Hello')
row = ButtonRow()                   # styled_layout('button_row')
content = PopupContent()            # styled(BoxLayout, 'popup_content')
```

These exist purely for readability and brevity.

## Widget Class Hierarchy

### Base classes (extend Kivy primitives)

| Class | Bases | Purpose |
|---|---|---|
| `RoundedButton` | ButtonBehavior + Label | Primary button with rounded-rect canvas |
| `SelectableButton` | RoundedButton | Toggle button with selected/unselected states |
| `IconButton` | ButtonBehavior + BoxLayout | Image icon + optional text label |
| `SolutionIndicator` | Widget | Canvas-drawn dot indicator |
| `BoardWidget` | Widget | Full game board with canvas drawing |
| `QueenSpinner` | Widget | Animated loading spinner |
| `DayCell` | ButtonBehavior + BoxLayout | Calendar day with queen icons |
| `LogbookRow` | ButtonBehavior + BoxLayout | Clickable list row |

**Pattern:** Clickable non-Button widgets use `ButtonBehavior` mixin. This gives `on_press`/`on_release` events and a `state` property ('normal'/'down') without Button's built-in background.

### Factory functions (return configured widgets)

| Factory | Returns | Notes |
|---|---|---|
| `GrayRoundedButton()` | RoundedButton | Gray bg, dark text |
| `FixedRoundedButton()` | RoundedButton | Sets size_hint_y=None |
| `FixedGrayRoundedButton()` | RoundedButton | Gray + fixed height |
| `SmallRoundedButton()` | RoundedButton | 14sp font |
| `BackButton()` | RoundedButton | Gray, "Back" text, fixed |
| `TitleLabel()`, `SubtitleLabel()`, etc. | Label | Pre-styled text |
| `ButtonRow()`, `SizeButtonRow()` | BoxLayout | Pre-styled containers |
| `Popup()` | ModalView | Styled modal wrapper |
| `LinkButton()` | Button | Transparent bg, link color |

## Color System

Colors are RGBA tuples in 0-1 range, grouped by purpose.

**Text hierarchy** (darkest to lightest):
- `TEXT_HEADER` (0.2) --- emphasized headings
- `TEXT_DARK` (0.3) --- primary body text
- `TEXT_LIGHT` (0.4) --- secondary descriptive text
- `TEXT_MEDIUM` (0.5) --- captions, metadata
- `TEXT_WHITE` (1.0) --- text on colored buttons

**Button colors:**
- Primary: `DEFAULT_BUTTON_COLOR` (salad green) / `_DOWN` (darker)
- Secondary: `GRAY_BUTTON_COLOR` / `_DOWN`
- Toggle: `BUTTON_UNSELECTED` / `DEFAULT_BUTTON_COLOR_DOWN` (selected)

**Status feedback:**
- `STATUS_SUCCESS` (green) --- confirmation messages
- `STATUS_ERROR` (red) --- error messages
- `QUEEN_GOLD` / `QUEEN_SILVER` / `QUEEN_GRAY` --- completion status

**Board colors:** Separate group for game grid rendering (cell borders, queen states, kingdom fills).

## Dimension & Spacing Scale

All raw values, converted to dp when consumed.

**Spacing scale** (used for gaps, margins):
```
SPACING_MIN=1  XS=2  SM=4  MD=8  LG=10  XL=15  XXL=20
```

**Button heights:**
```
BUTTON_HEIGHT_SM=40  BUTTON_HEIGHT=48  BUTTON_HEIGHT_LG=58
```

**Padding presets** (horizontal, vertical):
```
PADDING_POPUP=(15, 10)  PADDING_ROW=(10, 5)  PADDING_CELL=(2, 2)
```

## Font System

- Single font family: `DMSansBlack` (`FONT_NAME` constant)
- Sizes in sp (scales with user accessibility settings): `'9sp'` to `'36sp'`
- `BUTTON_FONT_SIZE = '22sp'` --- 50% larger than Kivy's default 15sp
- Font name is auto-applied by `styled()` for any widget with a `font_name` attribute

**Typography scale used in STYLES:**
```
icon_label: 9sp    table_header: 11sp   caption/link: 12sp
table_cell: 13sp   day/subtitle: 14sp   title_sm/code: 16sp
title: 18sp        title_md: 20sp       month/button: 22sp
title_lg: 24sp     about_title: 28sp    clock: 36sp
```

## Layout Patterns

### Fixed vs. flexible sizing

Kivy uses `size_hint` (0-1 proportion) by default. To set an explicit pixel size, you must set the corresponding `size_hint` axis to `None`:

```python
# Fixed height, flexible width
'header_bar': {'size_hint_y': None, 'height': 50}

# Both fixed
'solutions_btn': {'size_hint': (None, None), 'width': 120, 'height': 40}
```

**Common layout composition:**
```python
layout = BoxLayout(orientation='vertical')
layout.add_widget(fixed_header)       # size_hint_y=None, height=50dp
layout.add_widget(flexible_content)   # size_hint_y=1 (default, fills remaining)
layout.add_widget(fixed_footer)       # size_hint_y=None, height=48dp
```

### Screen template (BackgroundedScreen)

All screens extend `BackgroundedScreen`, which provides:

```
FloatLayout
  +-- Image (background: splashscreen.jpg)
  +-- BoxLayout (overlay: translucent white)
  +-- BoxLayout (content_layout, vertical)
        +-- Spacer (70dp, pushes content below splash area)
        +-- [subclass content via build_content()]
```

Subclasses override `build_content()` to populate `self.content_layout`. The `add_back_button()` helper appends a standard BackButton.

### Popup composition

Popups follow a consistent structure:

```python
content = PopupContent()                 # vertical BoxLayout with padding/spacing
content.add_widget(TitleLabel('...'))
content.add_widget(...)                  # body widgets
content.add_widget(ButtonRow())          # action buttons
popup = Popup(content, height=300)       # ModalView wrapper
popup.open()
```

## Canvas Drawing

Widgets that need custom rendering (RoundedButton, DayCell, BoardWidget, QueenSpinner) draw directly on the Kivy canvas:

```python
def _update_bg(self, *args):
    self.canvas.before.clear()
    with self.canvas.before:
        Color(*self.bg_color)
        RoundedRectangle(pos=self.pos, size=self.size, radius=[BUTTON_RADIUS])
```

**Principles:**
- Draw on `canvas.before` for backgrounds (renders behind children)
- Bind to `pos` and `size` to redraw on layout changes
- Use `canvas.clear()` before redrawing to avoid stacking
- Load textures once, reuse across draws (board queen icon)

## Adding New Styles

1. Define raw constants in `ui_constants.py` (dimensions section)
2. Add a named entry to the `STYLES` dict with raw integer dimensions
3. The dp pre-conversion loop handles the rest automatically
4. Consume via `styled()`, `**STYLES['name']`, or a new factory function

## Common Pitfalls

- **Missing `size_hint_y: None`:** If you set `height` in a style but omit `size_hint_y: None`, the layout system ignores your height and uses proportional sizing instead.
- **Double dp conversion:** Never call `dp()` on a value from `STYLES` --- it's already converted. Only raw numbers from constants or literals need `dp()`.
- **Font sizes:** Use `'Nsp'` strings, not raw numbers. Kivy's sp scales with accessibility; dp does not.
- **RoundedButton height default:** RoundedButton's `__init__` calls `kwargs.setdefault('height', dp(48))`. If your style doesn't include `height`, the button gets 48dp. If it does include `height`, the style value wins.
