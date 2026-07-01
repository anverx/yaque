"""Popups.

Generic dialogs (loading, share, code-load) now live in kivyshell.uikit.popups;
the thin wrappers below keep yaque's call sites and its yaque://-URL / Game.from_code
parsing. The size / kingdom-strategy / solution selectors stay here — they are
specific to the Queens game.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

import database
from game import Game
from ui_constants import STYLES
from widgets import (
    CrownBadge,
    FixedGrayRoundedButton,
    FixedRoundedButton,
    Popup,
    PopupContent,
    RoundedButton,
    SelectableButton,
    SelectableButtonGroup,
    SizeButtonRow,
    SubtitleLabel,
    TitleLabel,
    styled,
)

# Generic dialogs from the shared library.
from kivyshell.uikit.popups import LoadingPopup, load_code_popup  # noqa: F401
from kivyshell.uikit.popups import share_popup as _share_popup

__all__ = [
    "LoadingPopup", "show_share_popup", "show_load_popup",
    "show_game_size_popup", "show_date_puzzles_popup",
]


def show_share_popup(share_url: str, code: str) -> None:
    _share_popup(share_url, code, title="Share Puzzle")


def show_load_popup(on_game_loaded: Callable[[Game], None]) -> None:
    """Load a shared puzzle from a pasted code or yaque:// URL."""

    def submit(text: str) -> str | None:
        code = text
        if text.startswith("yaque://"):
            if "?game=" in text:
                code = text.split("?game=")[-1]
            elif "?g=" in text:
                code = text.split("?g=")[-1]
        try:
            game = Game.from_code(code)
        except Exception:
            return "Invalid puzzle code"
        on_game_loaded(game)
        return None

    load_code_popup(submit, title="Load Shared Puzzle",
                    subtitle="Paste puzzle code or URL:", height=300)


# -----------------------------------------------------------------------------
# Game-specific selectors (Queens)
# -----------------------------------------------------------------------------

def _show_size_selection_popup(
    title: str,
    sizes: list[list[int]],
    on_size_selected: Callable[[int], None],
    popup_height: float,
    completed: dict[int, bool] | None = None,
) -> None:
    content = PopupContent()
    content.add_widget(TitleLabel(title, height=40))

    popup = None

    def make_callback(size: int) -> Callable[[Any], None]:
        def callback(btn: Any) -> None:
            popup.dismiss()
            on_size_selected(size)
        return callback

    for row_sizes in sizes:
        row = SizeButtonRow()
        for size in row_sizes:
            btn = RoundedButton(text=f'{size}x{size}')
            btn.bind(on_press=make_callback(size))
            if completed and completed.get(size):
                btn._crown_badge = CrownBadge(btn, visible=True)
            row.add_widget(btn)
        content.add_widget(row)

    content.add_widget(styled(Widget, 'spacer_sm'))

    cancel_btn = FixedGrayRoundedButton(text='Cancel')
    content.add_widget(cancel_btn)

    popup = Popup(content, height=popup_height, width_hint=0.8)
    cancel_btn.bind(on_press=popup.dismiss)
    popup.open()


def show_date_puzzles_popup(selected_date: date, on_size_selected: Callable[[int], None]) -> None:
    if selected_date == date.today():
        title = "Today's Puzzles"
    else:
        title = selected_date.strftime('%B %d, %Y')

    status = database.get_daily_completion_status(selected_date.isoformat())
    _show_size_selection_popup(
        title=title, sizes=[[6, 7, 8]], on_size_selected=on_size_selected,
        popup_height=200, completed=status,
    )


_last_random_options: dict[str, Any] = {
    'size': 8,
    'strategy': 'mixed',
    'max_solutions': 1,
    'queen_placement': 'backtrack',
}


def show_game_size_popup(on_game_options_selected: Callable[[int, str, int, str], None]) -> None:
    content = PopupContent()
    content.add_widget(TitleLabel('Random Puzzle'))

    popup = None
    selected_size = [_last_random_options['size']]
    selected_strategy = [_last_random_options['strategy']]
    selected_max_solutions = [_last_random_options['max_solutions']]
    selected_queen_placement = [_last_random_options['queen_placement']]

    content.add_widget(SubtitleLabel('Size'))
    size_row = styled(BoxLayout, 'selection_row')
    size_group = SelectableButtonGroup(on_select=lambda value: selected_size.__setitem__(0, value))
    for size in [6, 7, 8, 9]:
        btn = SelectableButton(text=f'{size}x{size}', selected=(size == selected_size[0]), **STYLES['selection_btn'])
        size_group.add(size, btn)
        size_row.add_widget(btn)
    content.add_widget(size_row)

    content.add_widget(SubtitleLabel('Kingdom Style'))
    strategy_row = styled(BoxLayout, 'selection_row')
    strategy_group = SelectableButtonGroup(on_select=lambda value: selected_strategy.__setitem__(0, value))
    for strategy, label in [('classic', 'Classic'), ('mixed', 'Mixed'), ('jagged', 'Jagged')]:
        btn = SelectableButton(text=label, selected=(strategy == selected_strategy[0]), **STYLES['selection_btn'])
        strategy_group.add(strategy, btn)
        strategy_row.add_widget(btn)
    content.add_widget(strategy_row)

    content.add_widget(SubtitleLabel('Solutions'))
    solutions_row = styled(BoxLayout, 'selection_row')
    solutions_group = SelectableButtonGroup(on_select=lambda value: selected_max_solutions.__setitem__(0, value))
    for max_sol, label in [(1, 'Unique'), (4, '< 4'), (10, '< 10')]:
        btn = SelectableButton(text=label, selected=(max_sol == selected_max_solutions[0]), **STYLES['selection_btn'])
        solutions_group.add(max_sol, btn)
        solutions_row.add_widget(btn)
    content.add_widget(solutions_row)

    content.add_widget(SubtitleLabel('Queens'))
    queens_row = styled(BoxLayout, 'selection_row')
    queens_group = SelectableButtonGroup(on_select=lambda value: selected_queen_placement.__setitem__(0, value))
    for placement, label in [('backtrack', 'Classic'), ('uniform', 'Uniform')]:
        btn = SelectableButton(text=label, selected=(placement == selected_queen_placement[0]), **STYLES['selection_btn'])
        queens_group.add(placement, btn)
        queens_row.add_widget(btn)
    content.add_widget(queens_row)

    content.add_widget(styled(Widget, 'spacer_sm'))

    def on_play(btn: Any) -> None:
        _last_random_options['size'] = selected_size[0]
        _last_random_options['strategy'] = selected_strategy[0]
        _last_random_options['max_solutions'] = selected_max_solutions[0]
        _last_random_options['queen_placement'] = selected_queen_placement[0]
        popup.dismiss()
        on_game_options_selected(
            selected_size[0], selected_strategy[0],
            selected_max_solutions[0], selected_queen_placement[0],
        )

    play_btn = FixedRoundedButton(text='Play')
    play_btn.bind(on_press=on_play)
    content.add_widget(play_btn)

    cancel_btn = FixedGrayRoundedButton(text='Cancel')
    content.add_widget(cancel_btn)

    popup = Popup(content, height=490)
    cancel_btn.bind(on_press=popup.dismiss)
    popup.open()
