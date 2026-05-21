from __future__ import annotations

import datetime
import random
from email.utils import parsedate_to_datetime
from typing import Any


def ceiling(attempt: int) -> float:
    return min(0.5 * (2 ** (attempt - 1)), 30.0)  # type: ignore[no-any-return]


def delay(attempt: int) -> float:
    c = ceiling(attempt)
    if c == 0.0:
        return 0.0
    return random.uniform(0, c)


def _header_value(headers: dict[str, Any], name: str) -> str | None:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return str(value)
    return None


def parse_retry_after(headers: dict[str, Any] | None) -> float | None:
    if not headers:
        return None
    raw = _header_value(headers, "Retry-After")
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    try:
        seconds = float(value)
        return max(0.0, seconds)
    except ValueError:
        pass
    try:
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=datetime.timezone.utc)
        delta = (retry_at - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        return max(0.0, delta)
    except (TypeError, ValueError, OverflowError):
        return None


def retry_delay(attempt: int, headers: dict[str, Any] | None = None) -> float:
    jitter = delay(attempt)
    retry_after = parse_retry_after(headers)
    if retry_after is None:
        return jitter
    return max(jitter, retry_after)
