"""Shim — the loading spinner now lives in ``kivyshell.uikit.spinner``.

yaque's spinning queen is just ``LoaderSpinner`` with ``theme.loader_icon`` set
to queen.png (see the kivyshell integration block in ui_constants). ``QueenSpinner``
is kept as an alias so existing imports keep working.
"""

from kivyshell.uikit.spinner import LoaderSpinner, QueenSpinner  # noqa: F401
