from __future__ import annotations

from typing import Any

from . import errors
from .api_error import first_error_message, parse_api_errors


def handle(status_code: int, body_text: str, headers: dict[str, Any]) -> None:
    if status_code < 400:
        return

    parsed_errors = parse_api_errors(body_text)
    message = first_error_message(parsed_errors, f"HTTP {status_code}")
    request_id = headers.get("X-Request-Id") or headers.get("x-request-id")

    kwargs: dict[str, Any] = {
        "status_code": status_code,
        "request_id": request_id,
        "response_body": body_text,
        "errors": parsed_errors,
    }

    if status_code in (401, 403):
        raise errors.AuthenticationError(message, **kwargs)
    elif status_code == 404:
        raise errors.NotFoundError(message, **kwargs)
    elif status_code in (400, 422):
        raise errors.ValidationError(message, **kwargs)
    elif status_code == 409:
        raise errors.ConflictError(message, **kwargs)
    elif status_code == 429:
        rate_limit_remaining = headers.get("X-RateLimit-Remaining") or headers.get(
            "x-ratelimit-remaining"
        )
        rate_limit_reset = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset")
        raise errors.RateLimitError(
            message,
            rate_limit_remaining=rate_limit_remaining,
            rate_limit_reset=rate_limit_reset,
            **kwargs,
        )
    elif 500 <= status_code < 600:
        raise errors.ServerError(message, **kwargs)
    else:
        raise errors.ClicksignError(message, **kwargs)
