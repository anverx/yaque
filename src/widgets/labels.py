"""Shim — labels and the generic ``styled()`` factory now live in
``kivyshell.uikit.labels``.

Kept as a thin re-export so existing ``from widgets import ...`` and
``from widgets.labels import ...`` call sites keep working during the kivyshell
extraction. yaque hands its tuned STYLES + theme to kivyshell in ui_constants
(see the kivyshell integration block there), so rendering is unchanged.
"""

from kivyshell.uikit.labels import *  # noqa: F401,F403
from kivyshell.uikit.labels import styled, styled_label  # noqa: F401
