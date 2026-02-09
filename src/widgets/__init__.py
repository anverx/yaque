"""Yaque UI widgets package."""

from widgets.core import (
    # Types
    ColorTuple,
    # Button classes and factories
    RoundedButton,
    GrayRoundedButton,
    FixedRoundedButton,
    FixedGrayRoundedButton,
    SmallRoundedButton,
    SelectableButton,
    SelectableButtonGroup,
    BackButton,
    LinkButton,
    # Label factories
    styled_label,
    StyledLabel,
    TitleLgLabel,
    TitleMdLabel,
    TitleLabel,
    TitleSmLabel,
    SubtitleLabel,
    CaptionLabel,
    MonthLabel,
    DayLabel,
    TableHeaderLabel,
    TableCellLabel,
    ClockLabel,
    IconLabel,
    AboutTitleLabel,
    AboutSubtitleLabel,
    StatusLabel,
    # Layout factories
    PopupContent,
    styled_layout,
    ButtonRow,
    SizeButtonRow,
    Popup,
    # Input factories
    UrlInput,
    CodeInput,
)

from widgets.spinner import QueenSpinner

from widgets.board import BoardWidget

__all__ = [
    # Types
    'ColorTuple',
    # Button classes and factories
    'RoundedButton',
    'GrayRoundedButton',
    'FixedRoundedButton',
    'FixedGrayRoundedButton',
    'SmallRoundedButton',
    'SelectableButton',
    'SelectableButtonGroup',
    'BackButton',
    'LinkButton',
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
    # Spinner
    'QueenSpinner',
    # Board
    'BoardWidget',
]
