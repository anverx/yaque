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
    CrownBadge,
    # Icon factories
    CrownIcon,
    DayLabel,
    FixedGrayRoundedButton,
    FixedRoundedButton,
    GrayRoundedButton,
    IconButton,
    IconLabel,
    LinkButton,
    MonthLabel,
    # Layout factories
    PanelLayout,
    Popup,
    PopupContent,
    RatingLabel,
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
    TallRoundedButton,
    TitleLabel,
    TitleLgLabel,
    TitleMdLabel,
    TitleSmLabel,
    TypeIcon,
    # Input factories
    UrlInput,
    # Widget helpers
    disable_widget,
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
    # Crown badge
    'CrownBadge',
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
