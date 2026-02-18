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
    RatingLabel,
    # Layout factories
    PanelLayout,
    PopupContent,
    # Icon factories
    CrownIcon,
    TypeIcon,
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
    # Widget helpers
    disable_widget,
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
    'RatingLabel',
    'ClockLabel',
    'IconLabel',
    'AboutTitleLabel',
    'AboutSubtitleLabel',
    'StatusLabel',
    # Layout factories
    'PanelLayout',
    'PopupContent',
    'styled_layout',
    'ButtonRow',
    'SizeButtonRow',
    'Popup',
    # Icon factories
    'CrownIcon',
    'TypeIcon',
    # Input factories
    'UrlInput',
    'CodeInput',
    # Indicators
    'SolutionIndicator',
    # Widget helpers
    'disable_widget',
    # Spinner
    'QueenSpinner',
    # Board
    'BoardWidget',
]
