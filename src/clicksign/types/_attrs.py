from __future__ import annotations

from typing import Any

from ..resource import Resource


def str_attr(resource: Resource, key: str) -> str | None:
    value = (resource._data.get("attributes") or {}).get(key)
    return value if isinstance(value, str) else None


def bool_attr(resource: Resource, key: str) -> bool | None:
    value = (resource._data.get("attributes") or {}).get(key)
    return value if isinstance(value, bool) else None


def int_attr(resource: Resource, key: str) -> int | None:
    value = (resource._data.get("attributes") or {}).get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def list_str_attr(resource: Resource, key: str) -> list[str] | None:
    value = (resource._data.get("attributes") or {}).get(key)
    if not isinstance(value, list):
        return None
    return [item for item in value if isinstance(item, str)]


def dict_attr(resource: Resource, key: str) -> dict[str, Any] | None:
    value = (resource._data.get("attributes") or {}).get(key)
    return value if isinstance(value, dict) else None
