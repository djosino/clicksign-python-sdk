from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RequestOptions:
    """Per-request overrides for a single API call.

    Precedence: per-request options override the client's defaults (including ``max_retries``).
    """

    api_key: str | None = None
    headers: dict[str, str] | None = None
    open_timeout: float | None = None
    read_timeout: float | None = None
    write_timeout: float | None = None
    max_retries: int | None = None


def normalize_options(options: RequestOptions | dict[str, Any] | None) -> RequestOptions | None:
    if options is None:
        return None
    if isinstance(options, RequestOptions):
        return options
    return RequestOptions(**options)


def merge_headers(base: dict[str, str], options: RequestOptions | None) -> dict[str, str]:
    merged = dict(base)
    if options is not None:
        if options.api_key is not None:
            merged["Authorization"] = options.api_key
        if options.headers:
            merged.update(options.headers)
    return merged


def resolve_timeouts(
    default_open: float,
    default_read: float,
    default_write: float,
    options: RequestOptions | None,
) -> tuple[float, float, float]:
    if options is None:
        return default_open, default_read, default_write
    return (
        default_open if options.open_timeout is None else options.open_timeout,
        default_read if options.read_timeout is None else options.read_timeout,
        default_write if options.write_timeout is None else options.write_timeout,
    )


def resolve_max_retries(default: int, options: RequestOptions | None) -> int:
    if options is None or options.max_retries is None:
        return default
    if options.max_retries < 0:
        raise ValueError(f"max_retries must be >= 0, got {options.max_retries}")
    return options.max_retries
