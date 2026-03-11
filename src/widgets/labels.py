"""Label widgets and style utilities for Yaque."""

from __future__ import annotations

from typing import Any

from kivy.metrics import dp
from kivy.uix.label import Label

from ui_constants import FONT_NAME, STYLES

# -----------------------------------------------------------------------------
# Generic Style Factory
# -----------------------------------------------------------------------------

def _convert_dp_props(props: dict[str, Any]) -> dict[str, Any]:
    """Convert dimension values to dp units."""
    result = props.copy()
    # Single value dimensions
    for key in ('height', 'width', 'spacing'):
        if key in result and isinstance(result[key], (int, float)):
            result[key] = dp(result[key])
    # Padding can be a single number or a list
    if 'padding' in result:
        if isinstance(result['padding'], (list, tuple)):
            result['padding'] = [dp(v) if isinstance(v, (int, float)) else v for v in result['padding']]
        elif isinstance(result['padding'], (int, float)):
            result['padding'] = dp(result['padding'])
    return result


def styled(widget_class: type, style: str, **overrides: Any) -> Any:
    """Create a widget with the specified style.

    Styles are defined in ui_constants.STYLES.
    Any kwargs override the style defaults.

    Args:
        widget_class: The widget class to instantiate (Label, BoxLayout, etc.)
        style: Style name from STYLES dict
        **overrides: Properties to override style defaults
    """
    # Style values are already dp-converted at import time
    props = STYLES.get(style, {}).copy()

    # Apply font_name default for text widgets
    if hasattr(widget_class, 'font_name'):
        props.setdefault('font_name', FONT_NAME)

    # Apply overrides (convert dp values for caller-provided dimensions)
    props.update(_convert_dp_props(overrides))

    return widget_class(**props)


# -----------------------------------------------------------------------------
# Label Factory
# -----------------------------------------------------------------------------

def styled_label(style: str = 'default', text: str = '', **overrides: Any) -> Label:
    """Create a label with the specified style.

    Styles are defined in ui_constants.STYLES.
    Any kwargs override the style defaults.

    Args:
        style: Style name ('title', 'subtitle', 'caption', or 'default')
        text: Label text
        **overrides: Properties to override style defaults
    """
    return styled(Label, style, text=text, **overrides)


# Convenience wrappers (content-only calls)
def StyledLabel(**kwargs: Any) -> Label:
    """Base styled label with app font."""
    return styled_label('default', **kwargs)


def TitleLgLabel(text: str, **kwargs: Any) -> Label:
    """Large title label for screen headers (24sp)."""
    return styled_label('title_lg', text, **kwargs)


def TitleMdLabel(text: str, **kwargs: Any) -> Label:
    """Medium title label for section headers (20sp)."""
    return styled_label('title_md', text, **kwargs)


def TitleLabel(text: str, **kwargs: Any) -> Label:
    """Title label for popups and screen headers (18sp)."""
    return styled_label('title', text, **kwargs)


def TitleSmLabel(text: str, **kwargs: Any) -> Label:
    """Small title label for game screen headers (16sp)."""
    return styled_label('title_sm', text, **kwargs)


def SubtitleLabel(text: str, **kwargs: Any) -> Label:
    """Subtitle label for descriptions (14sp)."""
    return styled_label('subtitle', text, **kwargs)


def CaptionLabel(text: str, **kwargs: Any) -> Label:
    """Caption label for small text and metadata (12sp)."""
    return styled_label('caption', text, **kwargs)


def MonthLabel(text: str, **kwargs: Any) -> Label:
    """Month/year display label for calendar (22sp)."""
    return styled_label('month', text, **kwargs)


def DayLabel(text: str, **kwargs: Any) -> Label:
    """Day name/number label for calendar (14sp)."""
    return styled_label('day', text, **kwargs)


def TableHeaderLabel(text: str, **kwargs: Any) -> Label:
    """Table column header label (11sp)."""
    return styled_label('table_header', text, **kwargs)


def TableCellLabel(text: str, **kwargs: Any) -> Label:
    """Table cell data label (13sp)."""
    return styled_label('table_cell', text, **kwargs)


def RatingLabel(text: str, **kwargs: Any) -> Label:
    """Star rating display label (gold, markup-enabled for font fallback)."""
    return styled_label('rating_cell', text, **kwargs)


def ClockLabel(text: str = '00:00', **kwargs: Any) -> Label:
    """Large clock/timer display label (36sp)."""
    return styled_label('clock', text, **kwargs)


def IconLabel(text: str, **kwargs: Any) -> Label:
    """Tiny label for icon button captions (9sp)."""
    return styled_label('icon_label', text, **kwargs)


def AboutTitleLabel(text: str, **kwargs: Any) -> Label:
    """Large title for About popup (28sp). Uses title_lg with larger font."""
    return styled_label('title_lg', text, font_size='28sp', **kwargs)


def AboutSubtitleLabel(text: str, **kwargs: Any) -> Label:
    """Subtitle for About popup (16sp). Uses subtitle with larger font."""
    return styled_label('subtitle', text, font_size='16sp', **kwargs)


def StatusLabel(text: str, **kwargs: Any) -> Label:
    """Centered status label for loading popups."""
    label = styled(Label, 'status_label', text=text, **kwargs)
    label.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
    return label
