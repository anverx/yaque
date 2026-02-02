import os
from datetime import date

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle, RoundedRectangle, PushMatrix, PopMatrix, Rotate
from kivy.metrics import dp

import database

# Path to icons
ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')


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


class DailyButton(ButtonBehavior, RelativeLayout):
    """A daily puzzle button that can show a crown when completed."""
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.completed = False

        # Background label (for the button appearance)
        self.label = Label(
            text=text,
            font_size='18sp',
            font_name='DMSans',
            size_hint=(1, 1)
        )
        self.add_widget(self.label)

        # Crown image (positioned at top-right, tilted) - using queen icon
        self.crown = Image(
            source=os.path.join(ICONS_DIR, 'queen.png'),
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            opacity=0,
            pos_hint={'right': 1.1, 'top': 1.15}
        )
        self.add_widget(self.crown)

        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*BUTTON_COLOR_DOWN)
            else:
                Color(*BUTTON_COLOR)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[BUTTON_RADIUS])

        # Draw tilted crown
        self.crown.canvas.before.clear()
        if self.completed:
            self.crown.opacity = 1
            with self.crown.canvas.before:
                PushMatrix()
                Rotate(angle=15, origin=(self.crown.center_x, self.crown.center_y))
            with self.crown.canvas.after:
                PopMatrix()
        else:
            self.crown.opacity = 0

    def set_completed(self, completed):
        """Set whether this puzzle has been completed."""
        self.completed = completed
        self._update_bg()


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

        self.daily_buttons_container = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        self.daily_buttons = {}
        for size in [6, 7, 8]:
            btn = DailyButton(text=f'{size}x{size}')
            btn.bind(on_press=lambda x, s=size: self.app.start_daily_game(s))
            self.daily_buttons[size] = btn
            self.daily_buttons_container.add_widget(btn)
        layout.add_widget(self.daily_buttons_container)

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

    def on_enter(self):
        """Called when screen is entered - refresh completion status."""
        self._refresh_daily_status()

    def _refresh_daily_status(self):
        """Update the crown display on daily buttons based on completion status."""
        today = date.today().isoformat()
        status = database.get_daily_completion_status(today)
        for size, btn in self.daily_buttons.items():
            btn.set_completed(status.get(size, False))
