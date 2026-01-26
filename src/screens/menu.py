from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen


class MainMenuScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Title
        layout.add_widget(Label(
            text='Yaque',
            font_size='48sp',
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=100
        ))

        # Daily puzzles section
        layout.add_widget(Label(
            text="Today's Puzzles",
            font_size='24sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=50
        ))

        daily_buttons = BoxLayout(size_hint_y=None, height=60, spacing=10)
        for size in [6, 7, 8]:
            btn = Button(text=f'{size}x{size}', font_size='20sp')
            btn.bind(on_press=lambda x, s=size: self.app.start_daily_game(s))
            daily_buttons.add_widget(btn)
        layout.add_widget(daily_buttons)

        # Spacer
        layout.add_widget(BoxLayout(size_hint_y=0.3))

        # Calendar button
        calendar_btn = Button(
            text='Calendar',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        calendar_btn.bind(on_press=self.app.show_calendar)
        layout.add_widget(calendar_btn)

        # Random game button
        random_btn = Button(
            text='Random Game',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        random_btn.bind(on_press=self.app.start_random_game)
        layout.add_widget(random_btn)

        # Load shared puzzle button
        load_btn = Button(
            text='Load Shared Puzzle',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        load_btn.bind(on_press=self.app.show_load_popup)
        layout.add_widget(load_btn)

        # Spacer
        layout.add_widget(BoxLayout(size_hint_y=0.3))

        # Exit button
        exit_btn = Button(
            text='Exit',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        exit_btn.bind(on_press=self.app.exit_app)
        layout.add_widget(exit_btn)

        self.add_widget(layout)
