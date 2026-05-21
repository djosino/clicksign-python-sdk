import json
from unittest.mock import MagicMock, patch

import pytest

from clicksign._http.transport import (
    HTTPStatusError,
    HttpxHTTPClient,
    UrllibHTTPClient,
    default_http_client,
)
from clicksign.client import Client
from clicksign.instrumentation import Instrumentation
from tests.support.fake_http_client import (
    FakeHTTPClient,
    connection_error,
    http_error,
    http_response,
)

BASE = "http://test.clicksign.com/api/v3"
KEY = "test-key"


def make_client(
    max_retries: int = 0,
    inst: Instrumentation | None = None,
    http_client: FakeHTTPClient | None = None,
    **kwargs: object,
) -> Client:
    return Client(
        api_key=KEY,
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=max_retries,
        instrumentation=inst or Instrumentation(),
        http_client=http_client or FakeHTTPClient(),
        **kwargs,  # type: ignore[arg-type]
    )


def test_get_sends_correct_headers():
    fake = FakeHTTPClient(http_response(200, {"data": []}))
    make_client(http_client=fake).get("/envelopes")
    assert fake.calls[0]["headers"]["Authorization"] == KEY
    assert fake.calls[0]["headers"]["Content-Type"] == "application/vnd.api+json"
    assert "Bearer" not in fake.calls[0]["headers"]["Authorization"]


def test_post_sends_body_as_json():
    body = {"data": {"id": "1", "type": "e", "attributes": {}, "relationships": {}}}
    fake = FakeHTTPClient(http_response(201, body))
    make_client(http_client=fake).post(
        "/envelopes", {"data": {"type": "envelopes", "attributes": {"name": "X"}}}
    )
    body = json.loads(fake.calls[0]["body"])
    assert body["data"]["attributes"]["name"] == "X"


def test_delete_sends_no_body():
    fake = FakeHTTPClient(http_response(204))
    make_client(http_client=fake).delete("/envelopes/1")
    assert fake.calls[0]["body"] is None


def test_passes_timeouts_to_http_client():
    fake = FakeHTTPClient(http_response(200, {"data": []}))
    make_client(http_client=fake).get("/envelopes")
    call = fake.calls[0]
    assert call["open_timeout"] == 2.0
    assert call["read_timeout"] == 5.0
    assert call["write_timeout"] == 7.0


def test_401_raises_authentication_error():
    from clicksign.errors import AuthenticationError

    fake = FakeHTTPClient(http_error(401, {"errors": [{"detail": "Unauthorized"}]}))
    with pytest.raises(AuthenticationError):
        make_client(http_client=fake).get("/envelopes")


def test_403_raises_authentication_error():
    from clicksign.errors import AuthenticationError

    fake = FakeHTTPClient(http_error(403, {}))
    with pytest.raises(AuthenticationError):
        make_client(http_client=fake).get("/envelopes")


def test_404_raises_not_found():
    from clicksign.errors import NotFoundError

    fake = FakeHTTPClient(http_error(404, {"errors": [{"detail": "Not Found"}]}))
    with pytest.raises(NotFoundError):
        make_client(http_client=fake).get("/envelopes/x")


def test_422_raises_validation_error():
    from clicksign.errors import ValidationError

    fake = FakeHTTPClient(http_error(422, {"errors": [{"detail": "Name can't be blank"}]}))
    with pytest.raises(ValidationError, match="Name can't be blank"):
        make_client(http_client=fake).post("/envelopes", {})


def test_500_raises_server_error():
    from clicksign.errors import ServerError

    fake = FakeHTTPClient(http_error(500, ""))
    with pytest.raises(ServerError):
        make_client(http_client=fake).get("/envelopes")


def test_max_retries_0_makes_exactly_one_request():
    fake = FakeHTTPClient(http_error(500, ""))
    from clicksign.errors import ServerError

    with pytest.raises(ServerError):
        make_client(max_retries=0, http_client=fake).get("/envelopes")
    assert len(fake.calls) == 1


def test_retries_on_500_and_succeeds():
    fake = FakeHTTPClient(
        http_error(500, ""),
        http_response(200, {"data": []}),
    )
    with patch("clicksign.retry_backoff.delay", return_value=0):
        result = make_client(max_retries=1, http_client=fake).get("/envelopes")
    assert result == {"data": []}
    assert len(fake.calls) == 2


def test_retries_on_429_and_succeeds():
    fake = FakeHTTPClient(
        http_error(429, ""),
        http_response(200, {"data": []}),
    )
    with patch("clicksign.retry_backoff.delay", return_value=0):
        result = make_client(max_retries=1, http_client=fake).get("/envelopes")
    assert result == {"data": []}


def test_retries_on_429_honors_retry_after_header():
    fake = FakeHTTPClient(
        http_error(429, "", headers={"Retry-After": "2"}),
        http_response(200, {"data": []}),
    )
    sleeps: list[float] = []

    def record_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    with patch("clicksign._http.executor.time.sleep", side_effect=record_sleep):
        with patch("clicksign.retry_backoff.delay", return_value=0):
            make_client(max_retries=1, http_client=fake).get("/envelopes")
    assert len(sleeps) == 1
    assert sleeps[0] >= 2.0


def test_does_not_retry_on_422():
    from clicksign.errors import ValidationError

    fake = FakeHTTPClient(http_error(422, {"errors": [{"detail": "bad"}]}))
    with pytest.raises(ValidationError):
        make_client(max_retries=2, http_client=fake).post("/envelopes", {})
    assert len(fake.calls) == 1


def test_raises_after_exhausting_retries():
    from clicksign.errors import ServerError

    fake = FakeHTTPClient(http_error(500, ""), http_error(500, ""))
    with patch("clicksign.retry_backoff.delay", return_value=0):
        with pytest.raises(ServerError):
            make_client(max_retries=1, http_client=fake).get("/envelopes")
    assert len(fake.calls) == 2


def test_raises_timeout_error_on_connection_error():
    from clicksign.errors import TimeoutError

    fake = FakeHTTPClient(connection_error("timed out"))
    with pytest.raises(TimeoutError):
        make_client(http_client=fake).get("/envelopes")


def test_retries_on_timeout_and_succeeds():
    fake = FakeHTTPClient(
        connection_error("first timeout"),
        http_response(200, {"data": []}),
    )
    with patch("clicksign.retry_backoff.delay", return_value=0):
        result = make_client(max_retries=1, http_client=fake).get("/envelopes")
    assert result == {"data": []}


def test_instrumentation_request_event_published():
    events: list = []
    inst = Instrumentation()
    inst.on_request(lambda e: events.append(e))
    fake = FakeHTTPClient(http_response(200, {"data": []}))
    make_client(inst=inst, http_client=fake).get("/envelopes")
    assert len(events) == 1
    e = events[0]
    assert e["method"] == "get"
    assert e["path"] == "/envelopes"
    assert e["status"] == 200
    assert e["attempt"] == 1
    assert "duration_ms" in e


def test_instrumentation_error_event_published():
    from clicksign.errors import ServerError

    error_events: list = []
    inst = Instrumentation()
    inst.on_error(lambda e: error_events.append(e))
    fake = FakeHTTPClient(http_error(500, ""))
    with pytest.raises(ServerError):
        make_client(inst=inst, http_client=fake).get("/envelopes")
    assert len(error_events) == 1
    assert error_events[0]["status"] == 500


def test_instrumentation_request_published_on_error():
    from clicksign.errors import ServerError

    req_events: list = []
    inst = Instrumentation()
    inst.on_request(lambda e: req_events.append(e))
    fake = FakeHTTPClient(http_error(500, ""))
    with pytest.raises(ServerError):
        make_client(inst=inst, http_client=fake).get("/envelopes")
    assert len(req_events) == 1


def test_instrumentation_retry_event_published():
    retry_events: list = []
    inst = Instrumentation()
    inst.on_retry(lambda e: retry_events.append(e))
    fake = FakeHTTPClient(http_error(500, ""), http_response(200, {"data": []}))
    with patch("clicksign.retry_backoff.delay", return_value=0):
        make_client(max_retries=1, inst=inst, http_client=fake).get("/envelopes")
    assert len(retry_events) == 1
    assert retry_events[0]["attempt"] == 1
    assert retry_events[0]["max_retries"] == 1


def test_instrumentation_timeout_status_none():
    from clicksign.errors import TimeoutError

    req_events: list = []
    inst = Instrumentation()
    inst.on_request(lambda e: req_events.append(e))
    fake = FakeHTTPClient(connection_error("timed out"))
    with pytest.raises(TimeoutError):
        make_client(inst=inst, http_client=fake).get("/envelopes")
    assert req_events[0]["status"] is None


def test_204_returns_none():
    fake = FakeHTTPClient(http_response(204))
    result = make_client(http_client=fake).delete("/envelopes/1")
    assert result is None


def test_custom_http_client_is_used():
    fake = FakeHTTPClient(http_response(200, {"data": []}))
    client = make_client(http_client=fake)
    assert client.http_client is fake


def test_raises_when_custom_http_client_and_proxy():
    fake = FakeHTTPClient()
    with pytest.raises(ValueError, match="custom http_client"):
        Client(
            api_key=KEY,
            base_url=BASE,
            open_timeout=2.0,
            read_timeout=5.0,
            write_timeout=5.0,
            max_retries=0,
            instrumentation=Instrumentation(),
            http_client=fake,
            proxy="http://proxy:8080",
        )


def test_default_http_client_is_urllib():
    client = Client(
        api_key=KEY,
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=5.0,
        max_retries=0,
        instrumentation=Instrumentation(),
    )
    assert isinstance(client.http_client, UrllibHTTPClient)


def test_configure_passes_custom_http_client():
    import clicksign

    fake = FakeHTTPClient(http_response(200, {"data": []}))
    clicksign.configure(http_client=fake, api_key=KEY, base_url=BASE)
    client = clicksign._global_client()
    assert client.http_client is fake


def test_urllib_direct_request_success():
    client = UrllibHTTPClient()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b'{"ok": true}'
    mock_resp.getheaders.return_value = [("Content-Type", "application/json")]

    mock_conn = MagicMock()
    mock_conn.getresponse.return_value = mock_resp

    with patch("http.client.HTTPSConnection", return_value=mock_conn):
        response = client.request(
            "GET",
            "https://app.clicksign.com/api/v3/envelopes",
            headers={"Authorization": "token"},
            body=None,
            open_timeout=1.0,
            read_timeout=2.0,
            write_timeout=3.0,
        )

    assert response.status == 200
    assert response.body == '{"ok": true}'
    mock_conn.request.assert_called_once()
    mock_conn.close.assert_called_once()


def test_urllib_direct_request_http_error():
    client = UrllibHTTPClient()
    mock_resp = MagicMock()
    mock_resp.status = 422
    mock_resp.read.return_value = b'{"errors":[{"detail":"bad"}]}'
    mock_resp.getheaders.return_value = []

    mock_conn = MagicMock()
    mock_conn.getresponse.return_value = mock_resp

    with patch("http.client.HTTPSConnection", return_value=mock_conn):
        with pytest.raises(HTTPStatusError) as exc_info:
            client.request(
                "POST",
                "https://app.clicksign.com/api/v3/envelopes",
                headers={},
                body=b"{}",
                open_timeout=1.0,
                read_timeout=2.0,
                write_timeout=3.0,
            )
    assert exc_info.value.status == 422


def test_urllib_proxy_uses_urlopen():
    client = UrllibHTTPClient(proxy="http://proxy.local:8080")
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.read.return_value = b"{}"
    fake_response.headers = {}
    fake_response.__enter__ = MagicMock(return_value=fake_response)
    fake_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.build_opener") as build_opener:
        opener = MagicMock()
        opener.open.return_value = fake_response
        build_opener.return_value = opener
        response = client.request(
            "GET",
            "https://app.clicksign.com/api/v3/envelopes",
            headers={},
            body=None,
            open_timeout=1.0,
            read_timeout=2.0,
            write_timeout=3.0,
        )

    assert response.status == 200
    build_opener.assert_called_once()


def test_httpx_client_requires_dependency():
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object):
        if name == "httpx":
            raise ImportError("No module named 'httpx'")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=fake_import):
        with pytest.raises(ImportError, match="httpx"):
            HttpxHTTPClient()


def test_httpx_client_delegates_to_injected_client():
    mock_httpx = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"data":[]}'
    mock_response.headers = {}
    mock_httpx.request.return_value = mock_response

    transport = HttpxHTTPClient(client=mock_httpx)
    response = transport.request(
        "GET",
        "https://app.clicksign.com/api/v3/envelopes",
        headers={"Authorization": "token"},
        body=None,
        open_timeout=1.0,
        read_timeout=2.0,
        write_timeout=3.0,
    )

    assert response.body == '{"data":[]}'
    mock_httpx.request.assert_called_once()


def test_default_http_client_factory():
    assert isinstance(default_http_client(), UrllibHTTPClient)
    assert isinstance(
        default_http_client(proxy="http://proxy:8080", verify_ssl_certs=False),
        UrllibHTTPClient,
    )
