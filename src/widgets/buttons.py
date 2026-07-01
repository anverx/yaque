"""Shim — buttons now live in ``kivyshell.uikit.buttons``.

Thin re-export so existing ``from widgets import RoundedButton`` / ``IconButton`` /
``CrownBadge`` etc. keep working during the kivyshell extraction. Colors, the
button font, the icons directory and the badge icon/color are supplied by yaque's
Theme (see the kivyshell integration block in ui_constants).
"""

from kivyshell.uikit.buttons import *  # noqa: F401,F403
