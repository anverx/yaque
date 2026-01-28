from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp


# Salad green button color
BUTTON_COLOR = (0.55, 0.78, 0.4, 1)
BUTTON_COLOR_DOWN = (0.45, 0.68, 0.3, 1)  # Darker when pressed
BUTTON_RADIUS = dp(12)


class RoundedButton(ButtonBehavior, Label):
    """A button with rounded corners."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = BUTTON_COLOR
        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*BUTTON_COLOR_DOWN)
            else:
                Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[BUTTON_RADIUS])


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
        for size in [6, 7, 8]:
            btn = RoundedButton(text=f'{size}x{size}', font_size='18sp', font_name='DMSans')
            btn.bind(on_press=lambda x, s=size: self.app.start_daily_game(s))
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

        # Spacer
        layout.add_widget(BoxLayout(size_hint_y=0.2))

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
