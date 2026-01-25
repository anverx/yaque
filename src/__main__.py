from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button

class Board(GridLayout):
    def __init__(self, size=8, **kwargs):
        super().__init__(cols=size, **kwargs)
        for _ in range(size * size):
            self.add_widget(Button(text=''))

class QueensApp(App):
    def build(self):
        return Board()

QueensApp().run()
