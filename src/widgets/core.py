"""Core UI widgets for Yaque."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Ellipse, PopMatrix, PushMatrix, Rectangle, Rotate, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from ui_constants import (
    BUTTON_FONT_SIZE,
    BUTTON_HEIGHT,
    DEFAULT_BUTTON_COLOR,
    DEFAULT_BUTTON_COLOR_DOWN,
    DISABLED_OPACITY,
    FONT_NAME,
    GRAY_BUTTON_COLOR,
    GRAY_BUTTON_COLOR_DOWN,
    ICON_BTN_SIZE,
    ICON_LABEL_HEIGHT,
    ICON_LABEL_TOTAL,
    INDICATOR_CIRCLE_SIZE,
    INDICATOR_CURRENT,
    INDICATOR_OTHER,
    INDICATOR_SPACING,
    PANEL_BACKGROUND,
    POPUP_BACKGROUND,
    POPUP_WIDTH,
    QUEEN_GOLD,
    RADIUS_MD,
    RADIUS_SM,
    STYLES,
    TEXT_DARK,
    TEXT_MEDIUM,
    TEXT_WHITE,
)

# Path to icons directory
ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')

BUTTON_RADIUS = dp(RADIUS_MD)


# Type alias for color tuples
ColorTuple = tuple[float, float, float, float]


class RoundedButton(ButtonBehavior, Label):
    """A button with rounded corners. Use in ButtonRow or containers.

    Args:
        bg_color: Background color tuple (r, g, b, a). Defaults to salad green.
        bg_color_down: Pressed background color. Defaults to darker shade.
    """
    def __init__(self, bg_color: ColorTuple | None = None, bg_color_down: ColorTuple | None = None, **kwargs: Any) -> None:
        kwargs.setdefault('font_name', FONT_NAME)
        kwargs.setdefault('font_size', BUTTON_FONT_SIZE)
        kwargs.setdefault('color', TEXT_WHITE)
        kwargs.setdefault('markup', True)
        kwargs.setdefault('halign', 'center')
        kwargs.setdefault('valign', 'middle')
        kwargs.setdefault('height', dp(BUTTON_HEIGHT))
        super().__init__(**kwargs)
        self.bg_color = bg_color or DEFAULT_BUTTON_COLOR
        self.bg_color_down = bg_color_down or DEFAULT_BUTTON_COLOR_DOWN
        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)
        self.bind(size=self._update_text_size)

    def _update_text_size(self, *args: Any) -> None:
        self.text_size = self.size

    def _update_bg(self, *args: Any) -> None:
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*self.bg_color_down)
            else:
                Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[BUTTON_RADIUS])


def GrayRoundedButton(**kwargs: Any) -> RoundedButton:
    """Factory for gray rounded buttons in containers."""
    kwargs.setdefault('color', TEXT_DARK)
    return RoundedButton(
        bg_color=GRAY_BUTTON_COLOR,
        bg_color_down=GRAY_BUTTON_COLOR_DOWN,
        **kwargs
    )


def FixedRoundedButton(**kwargs: Any) -> RoundedButton:
    """Factory for standalone buttons with fixed height."""
    kwargs.setdefault('size_hint_y', None)
    return RoundedButton(**kwargs)


def TallRoundedButton(**kwargs: Any) -> RoundedButton:
    """Factory for tall buttons with tight line spacing (two-line text)."""
    kwargs.setdefault('size_hint_y', None)
    return RoundedButton(**STYLES['tall_btn'], **kwargs)


def FixedGrayRoundedButton(**kwargs: Any) -> RoundedButton:
    """Factory for standalone gray buttons with fixed height."""
    kwargs.setdefault('size_hint_y', None)
    return GrayRoundedButton(**kwargs)


class CrownBadge:
    """A tilted gold crown badge drawn on a button's canvas.before.

    Draws between the button background and text so text remains visible.
    Binds to the button's pos/size/state to redraw automatically.
    """

    _texture: Any = None

    def __init__(self, btn: RoundedButton, visible: bool = False) -> None:
        self.btn = btn
        self.visible = visible
        if CrownBadge._texture is None:
            CrownBadge._texture = CoreImage(
                os.path.join(ICONS_DIR, 'queen-small.png')
            ).texture
        btn.bind(pos=self._draw, size=self._draw, state=self._draw)

    def show(self) -> None:
        """Show the badge and redraw."""
        self.visible = True
        self.btn._update_bg()
        self._draw()

    def hide(self) -> None:
        """Hide the badge and redraw background."""
        self.visible = False
        self.btn._update_bg()

    def _draw(self, *args: Any) -> None:
        if not self.visible:
            return
        btn = self.btn
        with btn.canvas.before:
            Color(*QUEEN_GOLD)
            icon_size = btn.height * 0.4
            ix = btn.right - icon_size - dp(4)
            iy = btn.top - icon_size - dp(2)
            PushMatrix()
            Rotate(angle=-20, origin=(ix + icon_size / 2, iy + icon_size / 2))
            Rectangle(
                texture=CrownBadge._texture,
                pos=(ix, iy),
                size=(icon_size, icon_size),
            )
            PopMatrix()


# -----------------------------------------------------------------------------
# Generic Style Factory
# -----------------------------------------------------------------------------

def _convert_dp_props(props: dict[str, Any]) -> dict[str, Any]:
    """Convert dimension values to dp units."""
    result = props.copy()
    # Single value dimensions
    for key in ('height', 'width', 'spacing'):
        if key in result and isinstance(result[key], (int, float)):
            result[key] = dp(result[key])
    # Padding can be a single number or a list
    if 'padding' in result:
        if isinstance(result['padding'], (list, tuple)):
            result['padding'] = [dp(v) if isinstance(v, (int, float)) else v for v in result['padding']]
        elif isinstance(result['padding'], (int, float)):
            result['padding'] = dp(result['padding'])
    return result


def styled(widget_class: type, style: str, **overrides: Any) -> Any:
    """Create a widget with the specified style.

    Styles are defined in ui_constants.STYLES.
    Any kwargs override the style defaults.

    Args:
        widget_class: The widget class to instantiate (Label, BoxLayout, etc.)
        style: Style name from STYLES dict
        **overrides: Properties to override style defaults
    """
    # Style values are already dp-converted at import time
    props = STYLES.get(style, {}).copy()

    # Apply font_name default for text widgets
    if hasattr(widget_class, 'font_name'):
        props.setdefault('font_name', FONT_NAME)

    # Apply overrides (convert dp values for caller-provided dimensions)
    props.update(_convert_dp_props(overrides))

    return widget_class(**props)


# -----------------------------------------------------------------------------
# Label Factory
# -----------------------------------------------------------------------------

def styled_label(style: str = 'default', text: str = '', **overrides: Any) -> Label:
    """Create a label with the specified style.

    Styles are defined in ui_constants.STYLES.
    Any kwargs override the style defaults.

    Args:
        style: Style name ('title', 'subtitle', 'caption', or 'default')
        text: Label text
        **overrides: Properties to override style defaults
    """
    return styled(Label, style, text=text, **overrides)


# Convenience wrappers (content-only calls)
def StyledLabel(**kwargs: Any) -> Label:
    """Base styled label with app font."""
    return styled_label('default', **kwargs)


def TitleLgLabel(text: str, **kwargs: Any) -> Label:
    """Large title label for screen headers (24sp)."""
    return styled_label('title_lg', text, **kwargs)


def TitleMdLabel(text: str, **kwargs: Any) -> Label:
    """Medium title label for section headers (20sp)."""
    return styled_label('title_md', text, **kwargs)


def TitleLabel(text: str, **kwargs: Any) -> Label:
    """Title label for popups and screen headers (18sp)."""
    return styled_label('title', text, **kwargs)


def TitleSmLabel(text: str, **kwargs: Any) -> Label:
    """Small title label for game screen headers (16sp)."""
    return styled_label('title_sm', text, **kwargs)


def SubtitleLabel(text: str, **kwargs: Any) -> Label:
    """Subtitle label for descriptions (14sp)."""
    return styled_label('subtitle', text, **kwargs)


def CaptionLabel(text: str, **kwargs: Any) -> Label:
    """Caption label for small text and metadata (12sp)."""
    return styled_label('caption', text, **kwargs)


def MonthLabel(text: str, **kwargs: Any) -> Label:
    """Month/year display label for calendar (22sp)."""
    return styled_label('month', text, **kwargs)


def DayLabel(text: str, **kwargs: Any) -> Label:
    """Day name/number label for calendar (14sp)."""
    return styled_label('day', text, **kwargs)


def TableHeaderLabel(text: str, **kwargs: Any) -> Label:
    """Table column header label (11sp)."""
    return styled_label('table_header', text, **kwargs)


def TableCellLabel(text: str, **kwargs: Any) -> Label:
    """Table cell data label (13sp)."""
    return styled_label('table_cell', text, **kwargs)


def RatingLabel(text: str, **kwargs: Any) -> Label:
    """Star rating display label (gold, markup-enabled for font fallback)."""
    return styled_label('rating_cell', text, **kwargs)


def ClockLabel(text: str = '00:00', **kwargs: Any) -> Label:
    """Large clock/timer display label (36sp)."""
    return styled_label('clock', text, **kwargs)


def IconLabel(text: str, **kwargs: Any) -> Label:
    """Tiny label for icon button captions (9sp)."""
    return styled_label('icon_label', text, **kwargs)


def AboutTitleLabel(text: str, **kwargs: Any) -> Label:
    """Large title for About popup (28sp). Uses title_lg with larger font."""
    return styled_label('title_lg', text, font_size='28sp', **kwargs)


def AboutSubtitleLabel(text: str, **kwargs: Any) -> Label:
    """Subtitle for About popup (16sp). Uses subtitle with larger font."""
    return styled_label('subtitle', text, font_size='16sp', **kwargs)


# -----------------------------------------------------------------------------
# Layout Factories
# -----------------------------------------------------------------------------

def PopupContent(**kwargs: Any) -> BoxLayout:
    """Vertical BoxLayout with popup padding/spacing defaults."""
    return styled(BoxLayout, 'popup_content', **kwargs)


def styled_layout(style: str = 'button_row', **overrides: Any) -> BoxLayout:
    """Create a BoxLayout with the specified style.

    Styles are defined in ui_constants.STYLES.
    """
    return styled(BoxLayout, style, **overrides)


def ButtonRow(**kwargs: Any) -> BoxLayout:
    """Horizontal BoxLayout for button rows with standard height/spacing."""
    return styled_layout('button_row', **kwargs)


def SizeButtonRow(**kwargs: Any) -> BoxLayout:
    """Horizontal BoxLayout for size selection buttons."""
    return styled_layout('button_row', **kwargs)


class PanelLayout(BoxLayout):
    """BoxLayout with a dark rounded background panel."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._update_panel_bg()
        self.bind(pos=self._update_panel_bg, size=self._update_panel_bg)

    def _update_panel_bg(self, *args: Any) -> None:
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*PANEL_BACKGROUND)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(RADIUS_SM)])


def TypeIcon(daily_date: str | None, **kwargs: Any) -> Image:
    """Calendar/dice icon indicating daily vs random puzzle."""
    icon_name = 'calendar' if daily_date else 'dice'
    kwargs.setdefault('color', TEXT_MEDIUM)
    kwargs.setdefault('fit_mode', 'contain')
    return Image(source=os.path.join(ICONS_DIR, f'{icon_name}.png'), **kwargs)


def CrownIcon(color: tuple[float, ...], **kwargs: Any) -> Image:
    """Small queen/crown status icon."""
    kwargs.setdefault('fit_mode', 'contain')
    return Image(source=os.path.join(ICONS_DIR, 'queen-small.png'), color=color, **kwargs)


def Popup(content: Widget, height: float, width_hint: float = POPUP_WIDTH, auto_dismiss: bool = True) -> ModalView:
    """Create a styled ModalView popup.

    Args:
        content: Widget to add as popup content
        height: Popup height in dp units (raw number)
        width_hint: size_hint_x value (default POPUP_WIDTH)
        auto_dismiss: Whether tapping outside closes popup
    """
    popup = ModalView(
        size_hint=(width_hint, None),
        height=dp(height),
        auto_dismiss=auto_dismiss,
        background_color=POPUP_BACKGROUND
    )
    popup.add_widget(content)
    return popup


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


def LinkButton(text: str, **kwargs: Any) -> Button:
    """Transparent button styled as a link."""
    return styled(Button, 'link_btn', text=text, **kwargs)


def SmallRoundedButton(**kwargs: Any) -> RoundedButton:
    """Smaller rounded button for compact UI elements."""
    kwargs.setdefault('font_size', '14sp')
    return RoundedButton(**kwargs)


class SelectableButton(RoundedButton):
    """A button that can be selected/deselected with visual feedback.

    Use with SelectableButtonGroup for radio-style selection.
    """

    def __init__(self, selected: bool = False, **kwargs: Any) -> None:
        from ui_constants import BUTTON_UNSELECTED
        # Set initial colors based on selected state
        if not selected:
            kwargs.setdefault('bg_color', BUTTON_UNSELECTED)
        super().__init__(**kwargs)
        self._selected = selected

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool) -> None:
        from ui_constants import BUTTON_UNSELECTED
        self._selected = value
        if value:
            self.bg_color = DEFAULT_BUTTON_COLOR_DOWN
        else:
            self.bg_color = BUTTON_UNSELECTED
        self._update_bg()


class SelectableButtonGroup:
    """Manages a group of SelectableButtons for radio-style selection."""

    def __init__(self, on_select: Callable[[Any], None] | None = None) -> None:
        self.buttons: dict[Any, SelectableButton] = {}
        self.selected_value: Any = None
        self.on_select = on_select

    def add(self, value: Any, button: SelectableButton) -> None:
        """Add a button to the group with associated value."""
        self.buttons[value] = button
        button.bind(on_press=lambda btn: self.select(value))
        if button.selected:
            self.selected_value = value

    def select(self, value: Any) -> None:
        """Select a button by its value."""
        self.selected_value = value
        for v, btn in self.buttons.items():
            btn.selected = (v == value)
        if self.on_select:
            self.on_select(value)


def BackButton(**kwargs: Any) -> RoundedButton:
    """Standard back button with fixed height."""
    kwargs.setdefault('text', 'Back')
    return FixedGrayRoundedButton(**STYLES['back_btn'], **kwargs)


def disable_widget(widget: Widget) -> None:
    """Disable a widget with standard disabled styling."""
    widget.disabled = True
    widget.opacity = DISABLED_OPACITY


def StatusLabel(text: str, **kwargs: Any) -> Label:
    """Centered status label for loading popups."""
    label = styled(Label, 'status_label', text=text, **kwargs)
    label.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
    return label


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


# -----------------------------------------------------------------------------
# Icon Button
# -----------------------------------------------------------------------------

class IconButton(ButtonBehavior, BoxLayout):
    """A clickable image button with optional label."""

    def __init__(self, icon_name: str, size_dp: int = ICON_BTN_SIZE, label: str | None = None, **kwargs: Any) -> None:
        super().__init__(orientation='vertical', **kwargs)
        self.icon_name = icon_name
        self.size_hint = (None, None)

        # Icon
        self.icon = Image(
            source=os.path.join(ICONS_DIR, f'{icon_name}.png'),
            size_hint=(None, None),
            size=(dp(size_dp), dp(size_dp)),
            fit_mode='contain'
        )
        self.add_widget(self.icon)

        # Optional label
        if label:
            self.label_widget = IconLabel(
                label,
                size_hint=(None, None),
                size=(dp(size_dp), dp(ICON_LABEL_HEIGHT)),
                halign='center'
            )
            self.label_widget.bind(size=self.label_widget.setter('text_size'))
            self.add_widget(self.label_widget)
            self.size = (dp(size_dp), dp(size_dp + ICON_LABEL_TOTAL))
        else:
            self.size = (dp(size_dp), dp(size_dp))

    def set_icon(self, icon_name: str, label: str | None = None) -> None:
        """Change the icon and optionally the label."""
        self.icon_name = icon_name
        self.icon.source = os.path.join(ICONS_DIR, f'{icon_name}.png')
        if label and hasattr(self, 'label_widget'):
            self.label_widget.text = label
