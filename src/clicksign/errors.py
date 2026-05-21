from __future__ import annotations

from typing import Any

from .api_error import ApiError, first_error_code, first_source_pointer


class ClicksignError(Exception):
    retryable: bool = False

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        response_body: str | None = None,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.response_body = response_body
        self.errors: list[dict[str, Any]] = list(errors or [])

    @property
    def error_code(self) -> str | None:
        return first_error_code(self.errors)

    @property
    def source_pointer(self) -> str | None:
        return first_source_pointer(self.errors)

    @property
    def api_errors(self) -> list[ApiError]:
        return [ApiError.from_dict(entry) for entry in self.errors]


class AuthenticationError(ClicksignError):
    retryable = False


class NotFoundError(ClicksignError):
    retryable = False


class ValidationError(ClicksignError):
    retryable = False


class ConflictError(ClicksignError):
    retryable = False


class RateLimitError(ClicksignError):
    retryable = True

    def __init__(
        self,
        message: str,
        *,
        rate_limit_remaining: Any = None,
        rate_limit_reset: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.rate_limit_remaining = rate_limit_remaining
        self.rate_limit_reset = rate_limit_reset


class ServerError(ClicksignError):
    retryable = True


class TimeoutError(ClicksignError):
    retryable = True

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("status_code", None)
        super().__init__(message, **kwargs)


class WebhookSignatureError(ClicksignError):
    retryable = False


class WebhookPayloadError(ClicksignError):
    retryable = False
