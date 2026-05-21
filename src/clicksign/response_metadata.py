from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _header_value(headers: dict[str, str], name: str) -> str | None:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


@dataclass(frozen=True)
class ResponseMetadata:
    status: int
    headers: dict[str, str]
    request_id: str | None
    duration_ms: float

    @property
    def rate_limit_remaining(self) -> str | None:
        return _header_value(self.headers, "X-RateLimit-Remaining")

    @property
    def rate_limit_reset(self) -> str | None:
        return _header_value(self.headers, "X-RateLimit-Reset")


def build_response_metadata(
    status: int,
    headers: dict[str, str],
    duration_ms: float,
) -> ResponseMetadata:
    return ResponseMetadata(
        status=status,
        headers=dict(headers),
        request_id=_header_value(headers, "X-Request-Id"),
        duration_ms=duration_ms,
    )


@dataclass(frozen=True)
class HttpResult:
    data: Any
    metadata: ResponseMetadata
