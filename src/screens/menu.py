from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from widgets import RoundedButton


class MainMenuScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        # Root layout
        root = FloatLayout()

        # Background image (washed out)
        bg_image = Image(
            source='assets/images/splashscreen.jpg',
            fit_mode='cover'
        )
        root.add_widget(bg_image)

        # White overlay to wash out the image (brightness up, contrast down)
        overlay = BoxLayout()
        with overlay.canvas:
            Color(1, 1, 1, 0.7)  # Semi-transparent white
            self._overlay_rect = Rectangle(pos=overlay.pos, size=overlay.size)
        overlay.bind(pos=self._update_overlay, size=self._update_overlay)
        root.add_widget(overlay)

        # Main content layout
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))

        # Top spacer (pushes content below the splash image title)
        layout.add_widget(BoxLayout(size_hint_y=None, height=dp(70)))
        layout.add_widget(BoxLayout(size_hint_y=0.2))

        # Daily puzzles section
        layout.add_widget(Label(
            text="Today's Puzzles",
            font_name='DMSansBlack',
            font_size='20sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=dp(40)
        ))

        daily_buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        self.daily_buttons = {}
        for size in [6, 7, 8]:
            btn = RoundedButton(text=f'{size}x{size}', font_size='18sp', font_name='DMSans')
            btn.bind(on_press=lambda x, s=size: self.app.start_daily_game(s))
            self.daily_buttons[size] = btn
            daily_buttons.add_widget(btn)
        layout.add_widget(daily_buttons)

        # Spacer before middle buttons
        layout.add_widget(BoxLayout(size_hint_y=0.25))

        # Calendar button
        calendar_btn = RoundedButton(
            text='Calendar',
            font_name='DMSans',
            font_size='18sp',
            size_hint_y=None,
            height=dp(48)
        )
        calendar_btn.bind(on_press=self.app.show_calendar)
        layout.add_widget(calendar_btn)

        # Random game button
        random_btn = RoundedButton(
            text='Random Game',
            font_name='DMSans',
            font_size='18sp',
            size_hint_y=None,
            height=dp(48)
        )
        random_btn.bind(on_press=self.app.start_random_game)
        layout.add_widget(random_btn)

        # Load shared puzzle button
        load_btn = RoundedButton(
            text='Load Shared Puzzle',
            font_name='DMSans',
            font_size='18sp',
            size_hint_y=None,
            height=dp(48)
        )
        load_btn.bind(on_press=self.app.show_load_popup)
        layout.add_widget(load_btn)

        # Logbook button
        logbook_btn = RoundedButton(
            text='Logbook',
            font_name='DMSans',
            font_size='18sp',
            size_hint_y=None,
            height=dp(48)
        )
        logbook_btn.bind(on_press=self.app.show_logbook)
        layout.add_widget(logbook_btn)

        # About button
        about_btn = RoundedButton(
            text='About',
            font_name='DMSans',
            font_size='18sp',
            size_hint_y=None,
            height=dp(48)
        )
        about_btn.bind(on_press=self.app.show_about)
        layout.add_widget(about_btn)

        # Spacer
        layout.add_widget(BoxLayout(size_hint_y=0.1))

        # Exit button
        exit_btn = RoundedButton(
            text='Exit',
            font_name='DMSans',
            font_size='18sp',
            size_hint_y=None,
            height=dp(48)
        )
        exit_btn.bind(on_press=self.app.exit_app)
        layout.add_widget(exit_btn)

        root.add_widget(layout)
        self.add_widget(root)

    def _update_overlay(self, instance, value):
        self._overlay_rect.pos = instance.pos
        self._overlay_rect.size = instance.size

    def on_enter(self):
        """Called when screen is entered - refresh completion status."""
        pass  # TODO: Add crown display later
