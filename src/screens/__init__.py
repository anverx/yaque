"""yaque screens. Splash comes straight from kivyshell; the rest subclass the
shared kivyshell screens and supply game-specific config."""

from kivyshell.shell.screens.splash import SplashScreen
from screens.calendar import CalendarScreen
from screens.game_board import GameScreen
from screens.logbook import LogbookScreen
from screens.menu import MainMenuScreen

__all__ = [
    'CalendarScreen',
    'GameScreen',
    'LogbookScreen',
    'MainMenuScreen',
    'SplashScreen',
]
