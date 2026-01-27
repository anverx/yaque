from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen


class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Full screen splash image, cropped to fill
        splash = Image(
            source='assets/images/splashscreen.jpg',
            fit_mode='cover'  # Crops to fill entire screen
        )
        self.add_widget(splash)

    def set_status(self, text):
        pass  # No longer showing status text
