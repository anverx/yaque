import calendar
import os
from datetime import date

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.utils import platform

import database
from popups import show_date_puzzles_popup
from widgets import RoundedButton, DEFAULT_BUTTON_COLOR, DEFAULT_BUTTON_COLOR_DOWN

# Path to icons
ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')

# Queen icon colors
QUEEN_GRAY = (0.6, 0.6, 0.6, 1)
QUEEN_GOLD = (1.0, 0.84, 0.0, 1)


class DayCell(ButtonBehavior, BoxLayout):
    """Calendar day cell with day number and 3 queen status icons."""
    def __init__(self, day, completion_status=None, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.day = day
        self.background_color = DEFAULT_BUTTON_COLOR
        self._update_bg()
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._update_bg)

        # Day number
        self.day_label = Label(
            text=str(day),
            font_name='DMSans',
            font_size='14sp',
            color=(1, 1, 1, 1),
            size_hint_y=0.5
        )
        self.add_widget(self.day_label)

        # Queen icons row
        icons_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.5,
            spacing=dp(1),
            padding=[dp(2), 0, dp(2), dp(2)]
        )

        self.queen_icons = []
        for size in [6, 7, 8]:
            completed = completion_status.get(size, False) if completion_status else False
            icon = Image(
                source=os.path.join(ICONS_DIR, 'queen-small.png'),
                color=QUEEN_GOLD if completed else QUEEN_GRAY,
                fit_mode='contain'
            )
            self.queen_icons.append(icon)
            icons_row.add_widget(icon)

        self.add_widget(icons_row)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(*DEFAULT_BUTTON_COLOR_DOWN)
            else:
                Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])


class CalendarScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.current_year = date.today().year
        self.current_month = date.today().month

        # Root layout with background
        root = FloatLayout()

        # Background image (washed out)
        bg_image = Image(
            source='assets/images/splashscreen.jpg',
            fit_mode='cover'
        )
        root.add_widget(bg_image)

        # White overlay to wash out the image
        overlay = BoxLayout()
        with overlay.canvas:
            Color(1, 1, 1, 0.7)
            self._overlay_rect = Rectangle(pos=overlay.pos, size=overlay.size)
        overlay.bind(pos=self._update_overlay, size=self._update_overlay)
        root.add_widget(overlay)

        # Main content layout
        self.main_layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(10)
        )

        # Header with month/year and navigation
        header = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))

        prev_btn = RoundedButton(
            text='<',
            font_name='DMSansBlack',
            font_size='24sp',
            size_hint_x=None,
            width=dp(50)
        )
        prev_btn.bind(on_press=self.prev_month)
        header.add_widget(prev_btn)

        self.month_label = Label(
            text='',
            font_name='DMSansBlack',
            font_size='22sp',
            color=(0.2, 0.2, 0.2, 1)
        )
        header.add_widget(self.month_label)

        next_btn = RoundedButton(
            text='>',
            font_name='DMSansBlack',
            font_size='24sp',
            size_hint_x=None,
            width=dp(50)
        )
        next_btn.bind(on_press=self.next_month)
        header.add_widget(next_btn)

        self.main_layout.add_widget(header)

        # Day labels
        days_header = GridLayout(cols=7, size_hint_y=None, height=dp(30), spacing=dp(2))
        for day_name in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']:
            days_header.add_widget(Label(
                text=day_name,
                font_name='DMSans',
                font_size='14sp',
                color=(0.3, 0.3, 0.3, 1)
            ))
        self.main_layout.add_widget(days_header)

        # Calendar grid
        self.calendar_grid = GridLayout(cols=7, spacing=dp(4), size_hint_y=None)
        self.calendar_grid.bind(minimum_height=self.calendar_grid.setter('height'))
        self.main_layout.add_widget(self.calendar_grid)

        # Spacer
        self.main_layout.add_widget(BoxLayout())

        # Back button
        back_btn = RoundedButton(
            text='Back to Menu',
            font_name='DMSans',
            font_size='18sp',
            size_hint_y=None,
            height=dp(48)
        )
        back_btn.bind(on_press=lambda x: setattr(self.app.sm, 'current', 'menu'))
        self.main_layout.add_widget(back_btn)

        root.add_widget(self.main_layout)
        self.add_widget(root)
        self.refresh_calendar()

    def _update_overlay(self, instance, value):
        self._overlay_rect.pos = instance.pos
        self._overlay_rect.size = instance.size

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

        # Fetch completion status for entire month in one query
        month_status = database.get_month_completion_status(self.current_year, self.current_month)

        for day in cal.itermonthdays(self.current_year, self.current_month):
            if day == 0:
                # Empty cell
                self.calendar_grid.add_widget(Label(text='', size_hint_y=None, height=dp(52)))
            else:
                day_date = date(self.current_year, self.current_month, day)
                date_str = day_date.isoformat()
                completion_status = month_status.get(date_str, {6: False, 7: False, 8: False})

                cell = DayCell(
                    day=day,
                    completion_status=completion_status,
                    size_hint_y=None,
                    height=dp(52)
                )

                # Disable future dates
                if day_date > today:
                    cell.disabled = True
                    cell.opacity = 0.4
                else:
                    cell.bind(on_press=lambda x, d=day_date: self.select_date(d))
                    # Highlight today with slightly different color
                    if day_date == today:
                        cell.background_color = (0.4, 0.7, 0.9, 1)

                self.calendar_grid.add_widget(cell)

    def select_date(self, selected_date):
        def on_size_selected(size):
            self.app.start_daily_game(size, selected_date, from_calendar=True)
        show_date_puzzles_popup(selected_date, on_size_selected)

    def on_enter(self):
        """Refresh calendar when screen is shown to reflect completion changes."""
        self.refresh_calendar()

    # Swipe from left edge to go back to menu
    def on_touch_down(self, touch):
        if platform == 'android' and touch.x < dp(20):
            touch.ud['swipe_from_edge'] = True
            touch.ud['start_x'] = touch.x
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if platform == 'android' and touch.ud.get('swipe_from_edge'):
            if touch.x - touch.ud.get('start_x', 0) > dp(100):
                self.app.sm.current = 'menu'
                return True
        return super().on_touch_up(touch)
