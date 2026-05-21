from __future__ import annotations

from dataclasses import dataclass

_global_app_info: AppInfo | None = None


@dataclass(frozen=True)
class AppInfo:
    name: str
    version: str
    url: str | None = None


def set_app_info(name: str, version: str, url: str | None = None) -> None:
    global _global_app_info
    _global_app_info = AppInfo(name=name, version=version, url=url)


def get_app_info() -> AppInfo | None:
    return _global_app_info


def clear_app_info() -> None:
    global _global_app_info
    _global_app_info = None
