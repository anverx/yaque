import calendar
from datetime import date

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen


class CalendarScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.current_year = date.today().year
        self.current_month = date.today().month

        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Header with month/year and navigation
        header = BoxLayout(size_hint_y=None, height=50, spacing=10)

        prev_btn = Button(text='<', font_size='24sp', size_hint_x=None, width=50)
        prev_btn.bind(on_press=self.prev_month)
        header.add_widget(prev_btn)

        self.month_label = Label(
            text='',
            font_size='24sp',
            color=(0, 0, 0, 1)
        )
        header.add_widget(self.month_label)

        next_btn = Button(text='>', font_size='24sp', size_hint_x=None, width=50)
        next_btn.bind(on_press=self.next_month)
        header.add_widget(next_btn)

        self.main_layout.add_widget(header)

        # Day labels
        days_header = GridLayout(cols=7, size_hint_y=None, height=30, spacing=2)
        for day_name in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']:
            days_header.add_widget(Label(
                text=day_name,
                font_size='14sp',
                color=(0.3, 0.3, 0.3, 1)
            ))
        self.main_layout.add_widget(days_header)

        # Calendar grid
        self.calendar_grid = GridLayout(cols=7, spacing=2, size_hint_y=None)
        self.calendar_grid.bind(minimum_height=self.calendar_grid.setter('height'))
        self.main_layout.add_widget(self.calendar_grid)

        # Spacer
        self.main_layout.add_widget(BoxLayout())

        # Back button
        back_btn = Button(
            text='Back to Menu',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        back_btn.bind(on_press=lambda x: setattr(self.app.sm, 'current', 'menu'))
        self.main_layout.add_widget(back_btn)

        self.add_widget(self.main_layout)
        self.refresh_calendar()

    def prev_month(self, instance):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.refresh_calendar()

    def next_month(self, instance):
        today = date.today()
        # Don't allow going past current month
        if self.current_year == today.year and self.current_month >= today.month:
            return
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.refresh_calendar()

    def refresh_calendar(self):
        self.month_label.text = f'{calendar.month_name[self.current_month]} {self.current_year}'
        self.calendar_grid.clear_widgets()

        today = date.today()
        cal = calendar.Calendar(firstweekday=0)  # Monday first

        for day in cal.itermonthdays(self.current_year, self.current_month):
            if day == 0:
                # Empty cell
                self.calendar_grid.add_widget(Label(text='', size_hint_y=None, height=50))
            else:
                day_date = date(self.current_year, self.current_month, day)
                btn = Button(
                    text=str(day),
                    font_size='18sp',
                    size_hint_y=None,
                    height=50
                )
                # Disable future dates
                if day_date > today:
                    btn.disabled = True
                    btn.opacity = 0.5
                else:
                    btn.bind(on_press=lambda x, d=day_date: self.select_date(d))
                    # Highlight today
                    if day_date == today:
                        btn.background_color = (0.6, 0.8, 1, 1)
                self.calendar_grid.add_widget(btn)

    def select_date(self, selected_date):
        self.app.show_date_puzzles(selected_date)


class DatePuzzlesScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.selected_date = None

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Date label
        self.date_label = Label(
            text='',
            font_size='24sp',
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.date_label)

        # Puzzle buttons
        layout.add_widget(Label(
            text='Select Puzzle Size',
            font_size='20sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=40
        ))

        self.puzzle_buttons = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=200,
            spacing=10
        )
        for size in [6, 7, 8]:
            btn = Button(text=f'{size}x{size}', font_size='24sp')
            btn.bind(on_press=lambda x, s=size: self.start_puzzle(s))
            self.puzzle_buttons.add_widget(btn)
        layout.add_widget(self.puzzle_buttons)

        # Spacer
        layout.add_widget(BoxLayout())

        # Back button
        back_btn = Button(
            text='Back to Calendar',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        back_btn.bind(on_press=lambda x: setattr(self.app.sm, 'current', 'calendar'))
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def set_date(self, selected_date):
        self.selected_date = selected_date
        if selected_date == date.today():
            self.date_label.text = "Today's Puzzles"
        else:
            self.date_label.text = selected_date.strftime('%B %d, %Y')

    def start_puzzle(self, size):
        if self.selected_date:
            self.app.start_daily_game(size, self.selected_date)
