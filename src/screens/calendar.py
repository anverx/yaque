import calendar
from datetime import date

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.utils import platform


# Salad green button color (same as menu)
BUTTON_COLOR = (0.55, 0.78, 0.4, 1)
BUTTON_COLOR_DOWN = (0.45, 0.68, 0.3, 1)
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

        for day in cal.itermonthdays(self.current_year, self.current_month):
            if day == 0:
                # Empty cell
                self.calendar_grid.add_widget(Label(text='', size_hint_y=None, height=dp(44)))
            else:
                day_date = date(self.current_year, self.current_month, day)
                btn = RoundedButton(
                    text=str(day),
                    font_name='DMSans',
                    font_size='16sp',
                    size_hint_y=None,
                    height=dp(44)
                )
                # Disable future dates
                if day_date > today:
                    btn.disabled = True
                    btn.opacity = 0.4
                else:
                    btn.bind(on_press=lambda x, d=day_date: self.select_date(d))
                    # Highlight today with slightly different color
                    if day_date == today:
                        btn.background_color = (0.4, 0.7, 0.9, 1)
                self.calendar_grid.add_widget(btn)

    def select_date(self, selected_date):
        self.app.show_date_puzzles(selected_date)

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


class DatePuzzlesScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.selected_date = None

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
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

        # Date label
        self.date_label = Label(
            text='',
            font_name='DMSansBlack',
            font_size='24sp',
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None,
            height=dp(50)
        )
        layout.add_widget(self.date_label)

        # Puzzle buttons section
        layout.add_widget(Label(
            text='Select Puzzle Size',
            font_name='DMSans',
            font_size='18sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=dp(40)
        ))

        self.puzzle_buttons = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(180),
            spacing=dp(12)
        )
        for size in [6, 7, 8]:
            btn = RoundedButton(
                text=f'{size}x{size}',
                font_name='DMSans',
                font_size='20sp',
                size_hint_y=None,
                height=dp(48)
            )
            btn.bind(on_press=lambda x, s=size: self.start_puzzle(s))
            self.puzzle_buttons.add_widget(btn)
        layout.add_widget(self.puzzle_buttons)

        # Spacer
        layout.add_widget(BoxLayout())

        # Back button
        back_btn = RoundedButton(
            text='Back to Calendar',
            font_name='DMSans',
            font_size='18sp',
            size_hint_y=None,
            height=dp(48)
        )
        back_btn.bind(on_press=lambda x: setattr(self.app.sm, 'current', 'calendar'))
        layout.add_widget(back_btn)

        root.add_widget(layout)
        self.add_widget(root)

    def _update_overlay(self, instance, value):
        self._overlay_rect.pos = instance.pos
        self._overlay_rect.size = instance.size

    def set_date(self, selected_date):
        self.selected_date = selected_date
        if selected_date == date.today():
            self.date_label.text = "Today's Puzzles"
        else:
            self.date_label.text = selected_date.strftime('%B %d, %Y')

    def start_puzzle(self, size):
        if self.selected_date:
            self.app.start_daily_game(size, self.selected_date, from_calendar=True)

    # Swipe from left edge to go back to calendar
    def on_touch_down(self, touch):
        if platform == 'android' and touch.x < dp(20):
            touch.ud['swipe_from_edge'] = True
            touch.ud['start_x'] = touch.x
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if platform == 'android' and touch.ud.get('swipe_from_edge'):
            if touch.x - touch.ud.get('start_x', 0) > dp(100):
                self.app.sm.current = 'calendar'
                return True
        return super().on_touch_up(touch)
