from __future__ import annotations

from typing import Any

from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen


class SplashScreen(Screen):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # Full screen splash image, cropped to fill
        splash = Image(
            source='assets/images/splashscreen.jpg',
            fit_mode='cover'  # Crops to fill entire screen
        )
        self.add_widget(splash)

    def set_status(self, text: str) -> None:
        pass  # No longer showing status text
