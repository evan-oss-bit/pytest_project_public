# -*- coding: utf-8 -*-
import locale
import logging
import os
import sys

_configured_encoding = None


def configure_console_streams():
    """Keep Chinese output readable on Windows consoles and UTF-8 logs."""
    global _configured_encoding

    console_encoding = os.getenv("PYTEST_TOOL_CONSOLE_ENCODING")
    if not console_encoding and os.name == "nt":
        console_encoding = "cp936"
    if _configured_encoding == console_encoding:
        return

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if not reconfigure:
            continue

        if os.name == "nt":
            encoding = console_encoding
        elif getattr(stream, "isatty", lambda: False)():
            encoding = console_encoding or locale.getpreferredencoding(False) or "utf-8"
        else:
            encoding = "utf-8"

        try:
            reconfigure(encoding=encoding, errors="replace")
        except Exception:
            pass

    for handler in logging.getLogger().handlers:
        stream = getattr(handler, "stream", None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding=console_encoding or "utf-8", errors="replace")
            except Exception:
                pass
    _configured_encoding = console_encoding
