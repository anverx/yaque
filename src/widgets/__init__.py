"""Yaque UI widgets package."""

from widgets.board import BoardWidget
from widgets.core import (
    AboutSubtitleLabel,
    AboutTitleLabel,
    BackButton,
    ButtonRow,
    CaptionLabel,
    ClockLabel,
    CodeInput,
    # Types
    ColorTuple,
    DayLabel,
    FixedGrayRoundedButton,
    FixedRoundedButton,
    GrayRoundedButton,
    TallRoundedButton,
    IconButton,
    IconLabel,
    LinkButton,
    MonthLabel,
    Popup,
    # Layout factories
    PopupContent,
    # Button classes and factories
    RoundedButton,
    SelectableButton,
    SelectableButtonGroup,
    SizeButtonRow,
    SmallRoundedButton,
    # Indicators
    SolutionIndicator,
    StatusLabel,
    StyledLabel,
    SubtitleLabel,
    TableCellLabel,
    TableHeaderLabel,
    TitleLabel,
    TitleLgLabel,
    TitleMdLabel,
    TitleSmLabel,
    # Input factories
    UrlInput,
    # Generic style factory
    styled,
    # Label factories
    styled_label,
    styled_layout,
)
from widgets.spinner import QueenSpinner

__all__ = [
    # Types
    'ColorTuple',
    # Generic style factory
    'styled',
    # Button classes and factories
    'RoundedButton',
    'GrayRoundedButton',
    'FixedRoundedButton',
    'FixedGrayRoundedButton',
    'TallRoundedButton',
    'SmallRoundedButton',
    'SelectableButton',
    'SelectableButtonGroup',
    'BackButton',
    'LinkButton',
    'IconButton',
    # Label factories
    'styled_label',
    'StyledLabel',
    'TitleLgLabel',
    'TitleMdLabel',
    'TitleLabel',
    'TitleSmLabel',
    'SubtitleLabel',
    'CaptionLabel',
    'MonthLabel',
    'DayLabel',
    'TableHeaderLabel',
    'TableCellLabel',
    'ClockLabel',
    'IconLabel',
    'AboutTitleLabel',
    'AboutSubtitleLabel',
    'StatusLabel',
    # Layout factories
    'PopupContent',
    'styled_layout',
    'ButtonRow',
    'SizeButtonRow',
    'Popup',
    # Input factories
    'UrlInput',
    'CodeInput',
    # Indicators
    'SolutionIndicator',
    # Spinner
    'QueenSpinner',
    # Board
    'BoardWidget',
]
