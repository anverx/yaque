from __future__ import annotations

from typing import Any

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button

class Board(GridLayout):
    def __init__(self, size: int = 8, **kwargs: Any) -> None:
        super().__init__(cols=size, **kwargs)
        for _ in range(size * size):
            self.add_widget(Button(text=''))

class QueensApp(App):
    def build(self) -> Board:
        return Board()

QueensApp().run()
