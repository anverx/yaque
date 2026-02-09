"""Base screen classes with common UI patterns."""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ui_constants import FONT_NAME, OVERLAY_WHITE, BACKGROUND_IMAGE, TOP_SPACER_HEIGHT, BACK_BUTTON_HEIGHT, TEXT_DARK
from widgets import GrayRoundedButton


class BackgroundedScreen(Screen):
    """Base screen with background image and white overlay.

    Subclasses should override build_content() to add their UI elements
    to self.content_layout.
    """

    def __init__(self, app, **kwargs):
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
        self.content_layout.add_widget(
            BoxLayout(size_hint_y=None, height=dp(TOP_SPACER_HEIGHT))
        )

        # Let subclass build its content
        self.build_content()

        root.add_widget(self.content_layout)
        self.add_widget(root)

    def _update_overlay(self, instance, value):
        self._overlay_rect.pos = instance.pos
        self._overlay_rect.size = instance.size

    def get_padding(self):
        """Override to customize padding. Default is 20."""
        return 20

    def get_spacing(self):
        """Override to customize spacing. Default is 10."""
        return 10

    def build_content(self):
        """Override this method to build the screen's content.

        Add widgets to self.content_layout.
        """
        pass

    def add_back_button(self):
        """Add a standard back button that returns to menu."""
        back_btn = GrayRoundedButton(
            text='Back',
            font_size='18sp',
            color=TEXT_DARK,
            size_hint_y=None,
            height=dp(BACK_BUTTON_HEIGHT)
        )
        back_btn.bind(on_press=lambda x: setattr(self.app.sm, 'current', 'menu'))
        self.content_layout.add_widget(back_btn)
        return back_btn


# Re-export for convenience
from ui_constants import (
    TEXT_DARK, TEXT_MEDIUM, TEXT_LIGHT, TEXT_HEADER, TEXT_WHITE,
    OVERLAY_WHITE, ROW_BACKGROUND, ROW_PRESSED,
    QUEEN_GRAY, QUEEN_GOLD, QUEEN_SILVER,
    TODAY_HIGHLIGHT, TOP_SPACER_HEIGHT, BUTTON_HEIGHT, BACK_BUTTON_HEIGHT
)
