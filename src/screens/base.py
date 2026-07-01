"""Shim — BackgroundedScreen now lives in ``kivyshell.shell.screens.base``.

Background image, overlay, spacing and the back-to-menu navigation are provided
by the shared shell; yaque's theme supplies the background image.
"""

from kivyshell.shell.screens.base import BackgroundedScreen  # noqa: F401
