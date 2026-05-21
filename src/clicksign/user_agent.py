from __future__ import annotations

import platform
import re

from .app_info import AppInfo, get_app_info
from .version import __version__


def _sanitize_token(value: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", value.strip()) or "unknown"


def build_user_agent(app_info: AppInfo | None = None) -> str:
    parts = [
        f"clicksign-python/{__version__}",
        f"Python/{platform.python_version()}",
    ]
    resolved = app_info if app_info is not None else get_app_info()
    if resolved is not None:
        parts.append(f"{_sanitize_token(resolved.name)}/{_sanitize_token(resolved.version)}")
    return " ".join(parts)
