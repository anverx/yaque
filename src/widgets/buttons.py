"""Button widgets for Yaque."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, PopMatrix, PushMatrix, Rectangle, Rotate, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
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
    QUEEN_GOLD,
    RADIUS_MD,
    STYLES,
    TEXT_DARK,
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


def SmallRoundedButton(**kwargs: Any) -> RoundedButton:
    """Smaller rounded button for compact UI elements."""
    kwargs.setdefault('font_size', '14sp')
    return RoundedButton(**kwargs)


def BackButton(**kwargs: Any) -> RoundedButton:
    """Standard back button with fixed height."""
    kwargs.setdefault('text', 'Back')
    return FixedGrayRoundedButton(**STYLES['back_btn'], **kwargs)


def LinkButton(text: str, **kwargs: Any) -> Button:
    """Transparent button styled as a link."""
    from widgets.labels import styled
    return styled(Button, 'link_btn', text=text, **kwargs)


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


class SelectableButton(RoundedButton):
    """A button that can be selected/deselected with visual feedback.

    Use with SelectableButtonGroup for radio-style selection.
    """

    def __init__(self, selected: bool = False, **kwargs: Any) -> None:
        from ui_constants import BUTTON_UNSELECTED
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


class IconButton(ButtonBehavior, BoxLayout):
    """A clickable image button with optional label."""

    def __init__(self, icon_name: str, size_dp: int = ICON_BTN_SIZE, label: str | None = None, **kwargs: Any) -> None:
        super().__init__(orientation='vertical', **kwargs)
        self.icon_name = icon_name
        self.size_hint = (None, None)

        from widgets.labels import IconLabel

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


def disable_widget(widget: Widget) -> None:
    """Disable a widget with standard disabled styling."""
    widget.disabled = True
    widget.opacity = DISABLED_OPACITY
