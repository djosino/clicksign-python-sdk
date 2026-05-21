from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApiError:
    """Structured JSON:API error entry."""

    detail: str | None = None
    title: str | None = None
    code: str | None = None
    status: str | None = None
    source: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ApiError:
        source = data.get("source")
        return cls(
            detail=_as_str(data.get("detail")),
            title=_as_str(data.get("title")),
            code=_as_str(data.get("code")),
            status=_as_str(data.get("status")),
            source=source if isinstance(source, dict) else None,
            raw=data,
        )

    @property
    def pointer(self) -> str | None:
        if not self.source:
            return None
        return _as_str(self.source.get("pointer"))

    @property
    def parameter(self) -> str | None:
        if not self.source:
            return None
        return _as_str(self.source.get("parameter"))


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def parse_api_errors(body_text: str) -> list[dict[str, Any]]:
    if not body_text or not body_text.strip():
        return []
    try:
        body = json.loads(body_text)
    except (json.JSONDecodeError, ValueError):
        return []
    if not isinstance(body, dict):
        return []
    errs = body.get("errors")
    if not isinstance(errs, list):
        return []
    return [entry for entry in errs if isinstance(entry, dict)]


def parse_api_error_objects(body_text: str) -> list[ApiError]:
    return [ApiError.from_dict(entry) for entry in parse_api_errors(body_text)]


def first_error_message(errors: list[dict[str, Any]], fallback: str) -> str:
    if not errors:
        return fallback
    first = errors[0]
    detail = first.get("detail")
    if detail:
        return str(detail)
    title = first.get("title")
    if title:
        return str(title)
    return fallback


def first_error_code(errors: list[dict[str, Any]]) -> str | None:
    if not errors:
        return None
    code = errors[0].get("code")
    return str(code) if code is not None else None


def first_source_pointer(errors: list[dict[str, Any]]) -> str | None:
    if not errors:
        return None
    source = errors[0].get("source")
    if not isinstance(source, dict):
        return None
    pointer = source.get("pointer")
    return str(pointer) if pointer is not None else None
