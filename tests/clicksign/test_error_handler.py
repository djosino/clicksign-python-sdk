import json

import pytest

from clicksign.error_handler import handle
from clicksign.errors import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


def _h(status: int, body: dict | str = "", headers: dict | None = None) -> None:
    if isinstance(body, dict):
        body = json.dumps(body)
    handle(status, body, headers or {})


def test_401_raises_authentication_error():
    with pytest.raises(AuthenticationError):
        _h(401)


def test_403_raises_authentication_error():
    with pytest.raises(AuthenticationError):
        _h(403)


def test_404_raises_not_found():
    with pytest.raises(NotFoundError):
        _h(404)


def test_400_raises_validation_error():
    with pytest.raises(ValidationError):
        _h(400)


def test_422_raises_validation_error_with_detail():
    with pytest.raises(ValidationError, match="Name is blank"):
        _h(422, {"errors": [{"detail": "Name is blank"}]})


def test_409_raises_conflict_error():
    with pytest.raises(ConflictError):
        _h(409)


def test_429_raises_rate_limit_error():
    with pytest.raises(RateLimitError):
        _h(429)


def test_500_raises_server_error():
    with pytest.raises(ServerError):
        _h(500)


def test_non_json_body_uses_http_reason():
    err = pytest.raises(ServerError, _h, 500, "not json")
    assert "HTTP 500" in str(err.value)


def test_json_array_body_uses_http_reason():
    err = pytest.raises(ServerError, _h, 500, json.dumps([{"error": "bad"}]))
    assert "HTTP 500" in str(err.value)


def test_errors_title_fallback():
    with pytest.raises(ValidationError, match="Record invalid"):
        _h(422, {"errors": [{"title": "Record invalid"}]})


def test_empty_body_uses_http_reason():
    with pytest.raises(NotFoundError, match="HTTP 404"):
        _h(404, "")


def test_status_code_exposed():
    try:
        _h(422, {"errors": [{"detail": "bad"}]})
    except ValidationError as e:
        assert e.status_code == 422


def test_request_id_from_header():
    try:
        _h(404, "", {"X-Request-Id": "req-abc"})
    except NotFoundError as e:
        assert e.request_id == "req-abc"


def test_rate_limit_headers():
    try:
        _h(429, "", {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "999"})
    except RateLimitError as e:
        assert e.rate_limit_remaining == "0"
        assert e.rate_limit_reset == "999"


def test_2xx_does_not_raise():
    _h(200)
    _h(204)
    _h(201)
