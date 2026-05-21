from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..app_info import AppInfo

CORRELATION_ID_HEADER = "X-Correlation-Id"


def correlation_id(value: str) -> dict[str, str]:
    """Build headers dict for :class:`RequestOptions` to propagate a correlation id.

    Example::

        client.envelopes.retrieve(
            envelope_id,
            options=RequestOptions(headers=correlation_id(request.headers.get("X-Request-Id"))),
        )
    """
    if not value or not value.strip():
        raise ValueError("correlation_id value must be a non-empty string")
    return {CORRELATION_ID_HEADER: value}


def default_request_headers(api_key: str, app_info: AppInfo | None = None) -> dict[str, str]:
    from ..user_agent import build_user_agent

    return {
        "Authorization": api_key,
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
        "User-Agent": build_user_agent(app_info),
    }
