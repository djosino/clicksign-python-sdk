from __future__ import annotations

import pathlib

_DISTRIBUTION = "clicksign-python-sdk"


def _resolve_version() -> str:
    try:
        from importlib.metadata import version

        return version(_DISTRIBUTION)
    except Exception:
        pass

    revision = pathlib.Path(__file__).resolve().parent.parent.parent / "REVISION"
    if revision.is_file():
        return revision.read_text(encoding="utf-8").strip()

    return "0.0.0+unknown"


__version__ = _resolve_version()
