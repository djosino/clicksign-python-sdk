import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from clicksign._http.transport import HTTPStatusError, HttpxAsyncHTTPClient


def test_httpx_async_client_requires_dependency():
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object):
        if name == "httpx":
            raise ImportError("No module named 'httpx'")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=fake_import):
        with pytest.raises(ImportError, match="httpx"):
            HttpxAsyncHTTPClient()


@pytest.mark.asyncio
async def test_httpx_async_client_delegates_to_injected_client():
    mock_httpx = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"data":[]}'
    mock_response.headers = {}
    mock_httpx.request.return_value = mock_response

    transport = HttpxAsyncHTTPClient(client=mock_httpx)
    response = await transport.request(
        "GET",
        "https://app.clicksign.com/api/v3/envelopes",
        headers={"Authorization": "token"},
        body=None,
        open_timeout=1.0,
        read_timeout=2.0,
        write_timeout=3.0,
    )

    assert response.body == '{"data":[]}'
    mock_httpx.request.assert_awaited_once()


@pytest.mark.asyncio
async def test_httpx_async_raises_http_status_error():
    mock_httpx = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.text = '{"errors":[]}'
    mock_response.headers = {}
    mock_httpx.request.return_value = mock_response

    transport = HttpxAsyncHTTPClient(client=mock_httpx)
    with pytest.raises(HTTPStatusError) as exc_info:
        await transport.request(
            "POST",
            "https://example.com/api/v3/envelopes",
            headers={},
            body=b"{}",
            open_timeout=1.0,
            read_timeout=2.0,
            write_timeout=3.0,
        )
    assert exc_info.value.status == 422


@pytest.mark.asyncio
async def test_httpx_async_aclose_when_owns_client():
    mock_httpx = AsyncMock()
    transport = HttpxAsyncHTTPClient(client=mock_httpx)
    transport._owns_client = True  # type: ignore[attr-defined]
    await transport.aclose()
    mock_httpx.aclose.assert_awaited_once()


def _httpx_named_exc(name: str, response: MagicMock | None = None, message: str = "") -> Exception:
    exc_type = type(name, (Exception,), {})
    exc = exc_type(message)
    if response is not None:
        exc.response = response  # type: ignore[attr-defined]
    return exc


@pytest.mark.asyncio
async def test_httpx_async_owned_client_uses_timeout_and_raises_status():
    mock_httpx = MagicMock()
    mock_httpx.Timeout = MagicMock(side_effect=lambda **kw: kw)
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "unavailable"
    mock_response.headers = {}
    mock_client.request.return_value = mock_response

    transport = HttpxAsyncHTTPClient(client=mock_client)
    transport._owns_client = True  # type: ignore[attr-defined]

    with patch.dict(sys.modules, {"httpx": mock_httpx}):
        with pytest.raises(HTTPStatusError) as exc_info:
            await transport.request(
                "GET",
                "https://example.com/api/v3/envelopes",
                headers={},
                body=None,
                open_timeout=1.0,
                read_timeout=2.0,
                write_timeout=3.0,
            )
    assert exc_info.value.status == 503
    mock_httpx.Timeout.assert_called_once()


@pytest.mark.asyncio
async def test_httpx_async_maps_httpx_status_error_exception():
    mock_httpx = MagicMock()
    mock_httpx.Timeout = MagicMock(side_effect=lambda **kw: kw)
    mock_client = AsyncMock()
    inner = MagicMock()
    inner.status_code = 401
    inner.text = "unauthorized"
    inner.headers = {}
    mock_client.request.side_effect = _httpx_named_exc("HTTPStatusError", inner)

    transport = HttpxAsyncHTTPClient(client=mock_client)
    transport._owns_client = True  # type: ignore[attr-defined]

    with patch.dict(sys.modules, {"httpx": mock_httpx}):
        with pytest.raises(HTTPStatusError) as exc_info:
            await transport.request(
                "GET",
                "https://example.com/",
                headers={},
                body=None,
                open_timeout=1.0,
                read_timeout=2.0,
                write_timeout=3.0,
            )
    assert exc_info.value.status == 401


@pytest.mark.asyncio
async def test_httpx_async_maps_request_error():
    from clicksign._http.transport import HTTPConnectionError

    mock_httpx = MagicMock()
    mock_httpx.Timeout = MagicMock(side_effect=lambda **kw: kw)
    mock_client = AsyncMock()
    mock_client.request.side_effect = _httpx_named_exc("RequestError", message="timeout")

    transport = HttpxAsyncHTTPClient(client=mock_client)
    transport._owns_client = True  # type: ignore[attr-defined]

    with patch.dict(sys.modules, {"httpx": mock_httpx}):
        with pytest.raises(HTTPConnectionError, match="timeout"):
            await transport.request(
                "GET",
                "https://example.com/",
                headers={},
                body=None,
                open_timeout=1.0,
                read_timeout=2.0,
                write_timeout=3.0,
            )
