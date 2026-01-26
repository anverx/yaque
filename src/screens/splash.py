from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle


class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Solid background
        with layout.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self._bg = Rectangle(pos=layout.pos, size=layout.size)
        layout.bind(pos=self._update_bg, size=self._update_bg)

        # Splash screen image
        splash = Image(
            source='assets/images/splashscreen.jpg',
            allow_stretch=True,
            keep_ratio=True
        )
        layout.add_widget(splash)

        # Loading text
        self.status_label = Label(
            text='Loading...',
            font_size='20sp',
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.status_label)

        self.add_widget(layout)

    def _update_bg(self, instance, value):
        self._bg.pos = instance.pos
        self._bg.size = instance.size

    def set_status(self, text):
        self.status_label.text = text
