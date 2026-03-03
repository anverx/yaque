"""Base screen classes with common UI patterns."""

from __future__ import annotations

from typing import Any

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen

from ui_constants import BACKGROUND_IMAGE, OVERLAY_WHITE, SPACING_LG, SPACING_XXL
from widgets import BackButton, styled


class BackgroundedScreen(Screen):
    """Base screen with background image and white overlay.

    Subclasses should override build_content() to add their UI elements
    to self.content_layout.
    """

    def __init__(self, app: Any, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.app = app

        # Root layout
        root = FloatLayout()

        # Background image
        bg_image = Image(
            source=BACKGROUND_IMAGE,
            fit_mode='cover'
        )
        root.add_widget(bg_image)

        # White overlay
        overlay = BoxLayout()
        with overlay.canvas:
            Color(*OVERLAY_WHITE)
            self._overlay_rect = Rectangle(pos=overlay.pos, size=overlay.size)
        overlay.bind(pos=self._update_overlay, size=self._update_overlay)
        root.add_widget(overlay)

        # Main content layout
        self.content_layout = BoxLayout(
            orientation='vertical',
            padding=dp(self.get_padding()),
            spacing=dp(self.get_spacing())
        )

        # Top spacer (pushes content below the splash image title)
        self.content_layout.add_widget(styled(BoxLayout, 'top_spacer'))

        # Let subclass build its content
        self.build_content()

        root.add_widget(self.content_layout)
        self.add_widget(root)

    def _update_overlay(self, instance: Any, value: Any) -> None:
        self._overlay_rect.pos = instance.pos
        self._overlay_rect.size = instance.size

    def get_padding(self) -> int:
        """Override to customize padding. Default is SPACING_XXL."""
        return SPACING_XXL

    def get_spacing(self) -> int:
        """Override to customize spacing. Default is SPACING_LG."""
        return SPACING_LG

    def build_content(self) -> None:
        """Override this method to build the screen's content.

        Add widgets to self.content_layout.
        """
        pass

    def add_back_button(self) -> BackButton:
        """Add a standard back button that returns to menu, pushed to the bottom."""
        self.content_layout.add_widget(BoxLayout(size_hint_y=0.1))
        back_btn = BackButton()
        back_btn.bind(on_press=lambda x: setattr(self.app.sm, 'current', 'menu'))
        self.content_layout.add_widget(back_btn)
        return back_btn
