from clicksign.errors import (
    AuthenticationError,
    ClicksignError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
    WebhookPayloadError,
    WebhookSignatureError,
)


def test_all_inherit_from_base():
    for cls in (
        AuthenticationError,
        NotFoundError,
        ValidationError,
        ConflictError,
        RateLimitError,
        ServerError,
        TimeoutError,
        WebhookPayloadError,
        WebhookSignatureError,
    ):
        assert issubclass(cls, ClicksignError)


def test_retryable_flags():
    assert RateLimitError.retryable is True
    assert ServerError.retryable is True
    assert TimeoutError.retryable is True
    assert ValidationError.retryable is False
    assert NotFoundError.retryable is False
    assert AuthenticationError.retryable is False
    assert ConflictError.retryable is False


def test_exception_attributes():
    err = ValidationError(
        "bad input",
        status_code=422,
        request_id="req-123",
        response_body='{"errors":[]}',
        errors=[{"detail": "bad input", "code": "invalid"}],
    )
    assert str(err) == "bad input"
    assert err.message == "bad input"
    assert err.status_code == 422
    assert err.request_id == "req-123"
    assert err.response_body == '{"errors":[]}'
    assert err.errors[0]["code"] == "invalid"
    assert err.error_code == "invalid"


def test_rate_limit_error_extra_attrs():
    err = RateLimitError(
        "rate limited", status_code=429, rate_limit_remaining="0", rate_limit_reset="1700000000"
    )
    assert err.rate_limit_remaining == "0"
    assert err.rate_limit_reset == "1700000000"
    assert err.retryable is True


def test_timeout_error_has_none_status():
    err = TimeoutError("timed out")
    assert err.status_code is None
