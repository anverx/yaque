"""Yaque UI widgets package."""

from widgets.bar_chart import BarChart
from widgets.board import BoardWidget
from widgets.buttons import (
    BackButton,
    # Types
    ColorTuple,
    CrownBadge,
    FixedGrayRoundedButton,
    FixedRoundedButton,
    GrayRoundedButton,
    IconButton,
    LinkButton,
    # Button classes and factories
    RoundedButton,
    SelectableButton,
    SelectableButtonGroup,
    SmallRoundedButton,
    TallRoundedButton,
    # Widget helpers
    disable_widget,
)
from widgets.core import (
    CodeInput,
    # Indicators
    SolutionIndicator,
    # Input factories
    UrlInput,
)
from widgets.labels import (
    AboutSubtitleLabel,
    AboutTitleLabel,
    CaptionLabel,
    ClockLabel,
    DayLabel,
    IconLabel,
    MonthLabel,
    RatingLabel,
    StatusLabel,
    StyledLabel,
    SubtitleLabel,
    TableCellLabel,
    TableHeaderLabel,
    TitleLabel,
    TitleLgLabel,
    TitleMdLabel,
    TitleSmLabel,
    # Generic style factory
    styled,
    # Label factories
    styled_label,
)
from widgets.layouts import (
    # Layout factories
    ButtonRow,
    # Icon factories
    CrownIcon,
    DateSeparator,
    DayCell,
    LogbookRow,
    PanelLayout,
    Popup,
    PopupContent,
    SizeButtonRow,
    StatRow,
    TypeIcon,
    styled_layout,
)
from widgets.spinner import QueenSpinner

__all__ = [
    # Charts
    'BarChart',
    # Types
    'ColorTuple',
    # Crown badge
    'CrownBadge',
    'DateSeparator',
    'DayCell',
    'LogbookRow',
    'StatRow',
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
