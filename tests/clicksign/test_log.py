import importlib
import logging

import pytest

import clicksign
from clicksign.client import Client
from clicksign.instrumentation import Instrumentation
from clicksign.log import (
    get_log,
    get_logger,
    sanitize_body,
    sanitize_headers,
    set_log,
)
from tests.support.fake_http_client import FakeHTTPClient, http_error, http_response

BASE = "http://test.clicksign.com/api/v3"
KEY = "super-secret-api-key"


@pytest.fixture(autouse=True)
def reset_logging():
    set_log(None)
    logger = get_logger()
    logger.handlers.clear()
    yield
    set_log(None)
    logger.handlers.clear()


def _enable_caplog_logging(level: str) -> list[str]:
    set_log(level)
    logger = get_logger()
    logger.handlers.clear()
    messages: list[str] = []

    class _Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            messages.append(record.getMessage())

    logger.addHandler(_Collector())
    return messages


def test_set_and_get_log_level():
    set_log("debug")
    assert get_log() == "debug"
    set_log(None)
    assert get_log() is None


def test_invalid_log_level_raises():
    with pytest.raises(ValueError, match="Invalid log level"):
        set_log("verbose")


def test_sanitize_headers_redacts_authorization():
    headers = sanitize_headers(
        {
            "Authorization": KEY,
            "Content-Type": "application/json",
            "X-Request-Id": "req-1",
        }
    )
    assert headers["Authorization"] == "<redacted>"
    assert headers["Content-Type"] == "application/json"
    assert headers["X-Request-Id"] == "req-1"


def test_sanitize_body_truncates_large_payload():
    body = sanitize_body("x" * 5000)
    assert body is not None
    assert body.endswith("...(truncated)")
    assert len(body) < 5000


def test_info_logs_request_summary():
    messages = _enable_caplog_logging("info")
    fake = FakeHTTPClient(http_response(200, {"data": []}))
    client = Client(
        api_key=KEY,
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=fake,
    )

    client.get("/envelopes")

    assert len(messages) == 1
    message = messages[0]
    assert "GET /envelopes" in message
    assert "status=200" in message
    assert KEY not in message


def test_debug_logs_sanitized_headers_and_bodies():
    messages = _enable_caplog_logging("debug")
    fake = FakeHTTPClient(http_response(200, {"data": {"id": "1"}}))
    client = Client(
        api_key=KEY,
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=fake,
    )

    client.post("/envelopes", {"data": {"type": "envelopes", "attributes": {"name": "X"}}})

    assert len(messages) == 1
    message = messages[0]
    assert "request_headers=" in message
    assert "<redacted>" in message
    assert "request_body=" in message
    assert "response_body=" in message
    assert KEY not in message


def test_error_logs_final_http_failure():
    messages = _enable_caplog_logging("error")
    fake = FakeHTTPClient(
        http_error(
            401,
            '{"errors":[{"detail":"bad key"}]}',
            {"Content-Type": "application/vnd.api+json"},
        )
    )
    client = Client(
        api_key=KEY,
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=fake,
    )

    from clicksign.errors import AuthenticationError

    with pytest.raises(AuthenticationError):
        client.get("/envelopes")

    assert any("error GET /envelopes" in message for message in messages)
    assert KEY not in " ".join(messages)


def test_warn_logs_retry_without_final_error(monkeypatch):
    messages = _enable_caplog_logging("warn")
    responses = [
        http_error(
            503,
            '{"errors":[{"detail":"busy"}]}',
            {"Content-Type": "application/vnd.api+json"},
        ),
        http_response(200, {"data": []}),
    ]
    fake = FakeHTTPClient(*responses)
    client = Client(
        api_key=KEY,
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=1,
        instrumentation=Instrumentation(),
        http_client=fake,
    )
    monkeypatch.setattr("clicksign.http_executor.time.sleep", lambda _seconds: None)

    client.get("/envelopes")

    assert any("retry GET /envelopes" in message for message in messages)
    assert not any("error GET /envelopes" in message for message in messages)


def test_configure_accepts_log(monkeypatch):
    monkeypatch.delenv("CLICKSIGN_LOG", raising=False)
    mod = importlib.reload(clicksign)
    mod.set_log(None)
    mod.configure(api_key="k", log="info")
    assert mod.get_log() == "info"


def test_module_log_getter_setter():
    import clicksign as sdk

    sdk.log = "debug"
    assert sdk.log == "debug"
    sdk.log = None
    assert sdk.log is None
