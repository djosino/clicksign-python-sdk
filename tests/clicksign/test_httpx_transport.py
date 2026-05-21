import sys
from unittest.mock import MagicMock, patch

import pytest

from clicksign._http.transport import HTTPConnectionError, HTTPStatusError, HttpxHTTPClient


def _httpx_named_exc(name: str, response: MagicMock | None = None, message: str = "") -> Exception:
    exc_type = type(name, (Exception,), {})
    exc = exc_type(message)
    if response is not None:
        exc.response = response  # type: ignore[attr-defined]
    return exc


def test_httpx_owned_client_raises_on_status_code():
    mock_httpx = MagicMock()
    mock_httpx.Timeout = MagicMock(side_effect=lambda **kw: kw)
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "error"
    mock_response.headers = {"X-Request-Id": "1"}
    mock_client.request.return_value = mock_response

    transport = HttpxHTTPClient(client=mock_client)
    transport._owns_client = True  # type: ignore[attr-defined]

    with patch.dict(sys.modules, {"httpx": mock_httpx}):
        with pytest.raises(HTTPStatusError) as exc_info:
            transport.request(
                "GET",
                "https://example.com/api/v3/envelopes",
                headers={},
                body=None,
                open_timeout=1.0,
                read_timeout=2.0,
                write_timeout=3.0,
            )
    assert exc_info.value.status == 500
    mock_httpx.Timeout.assert_called_once()


def test_httpx_owned_client_maps_httpx_status_error_exception():
    mock_httpx = MagicMock()
    mock_httpx.Timeout = MagicMock(side_effect=lambda **kw: kw)
    mock_client = MagicMock()
    inner_response = MagicMock()
    inner_response.status_code = 429
    inner_response.text = "rate limited"
    inner_response.headers = {}
    mock_client.request.side_effect = _httpx_named_exc("HTTPStatusError", inner_response)

    transport = HttpxHTTPClient(client=mock_client)
    transport._owns_client = True  # type: ignore[attr-defined]

    with patch.dict(sys.modules, {"httpx": mock_httpx}):
        with pytest.raises(HTTPStatusError) as exc_info:
            transport.request(
                "GET",
                "https://example.com/api/v3/x",
                headers={},
                body=None,
                open_timeout=1.0,
                read_timeout=2.0,
                write_timeout=3.0,
            )
    assert exc_info.value.status == 429


def test_httpx_owned_client_maps_request_error():
    mock_httpx = MagicMock()
    mock_httpx.Timeout = MagicMock(side_effect=lambda **kw: kw)
    mock_client = MagicMock()
    mock_client.request.side_effect = _httpx_named_exc("RequestError", message="connection reset")

    transport = HttpxHTTPClient(client=mock_client)
    transport._owns_client = True  # type: ignore[attr-defined]

    with patch.dict(sys.modules, {"httpx": mock_httpx}):
        with pytest.raises(HTTPConnectionError, match="connection reset"):
            transport.request(
                "POST",
                "https://example.com/api/v3/envelopes",
                headers={},
                body=b"{}",
                open_timeout=1.0,
                read_timeout=2.0,
                write_timeout=3.0,
            )


def test_httpx_injected_client_uses_max_timeout():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "{}"
    mock_response.headers = {}
    mock_client.request.return_value = mock_response

    transport = HttpxHTTPClient(client=mock_client)
    transport.request(
        "GET",
        "https://example.com/",
        headers={},
        body=None,
        open_timeout=1.0,
        read_timeout=5.0,
        write_timeout=3.0,
    )
    _args, kwargs = mock_client.request.call_args
    assert kwargs["timeout"] == 5.0
