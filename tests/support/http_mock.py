"""Utilities for mocking HTTP transport in tests."""

from __future__ import annotations

import json
import urllib.error
from contextlib import contextmanager
from io import BytesIO
from typing import Any
from unittest.mock import MagicMock, patch

from clicksign.http_transport import (
    HTTPConnectionError,
    HTTPResponse,
    HTTPStatusError,
    UrllibHTTPClient,
)


class _FakeHTTPResponse:
    def __init__(self, status: int, body: bytes, headers: dict[str, str] | None = None) -> None:
        self.status = status
        self._body = body
        self.headers = headers or {}

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeHTTPResponse:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


def make_response(
    status: int = 200,
    body: bytes | str | dict | None = None,
    headers: dict[str, str] | None = None,
) -> _FakeHTTPResponse:
    if body is None:
        raw = b""
    elif isinstance(body, dict):
        raw = json.dumps(body).encode("utf-8")
    elif isinstance(body, str):
        raw = body.encode("utf-8")
    else:
        raw = body
    return _FakeHTTPResponse(status, raw, headers)


def make_http_error(
    status: int,
    body: bytes | str | dict | None = None,
    headers: dict[str, str] | None = None,
) -> urllib.error.HTTPError:
    if body is None:
        raw = b""
    elif isinstance(body, dict):
        raw = json.dumps(body).encode("utf-8")
    elif isinstance(body, str):
        raw = body.encode("utf-8")
    else:
        raw = body

    msg = MagicMock()
    msg.headers = headers or {}
    err = urllib.error.HTTPError(
        url="http://test",
        code=status,
        msg="Error",
        hdrs=msg,  # type: ignore[arg-type]
        fp=BytesIO(raw),
    )
    return err


def _resolve_queue_item(item: Any) -> HTTPResponse:
    if isinstance(item, BaseException):
        if isinstance(item, HTTPStatusError):
            raise item
        if isinstance(item, urllib.error.HTTPError):
            response_body = item.read().decode("utf-8") if item.fp else ""
            raise HTTPStatusError(
                item.code,
                response_body,
                dict(item.headers) if item.headers else {},
            )
        raise HTTPConnectionError(str(item))

    if isinstance(item, _FakeHTTPResponse):
        response_body = item.read().decode("utf-8")
        if item.status >= 400:
            raise HTTPStatusError(item.status, response_body, dict(item.headers))
        return HTTPResponse(status=item.status, body=response_body, headers=dict(item.headers))

    raise TypeError(f"Unsupported mock response type: {type(item)!r}")


@contextmanager
def mock_urlopen(*responses: Any, capture: dict[str, Any] | None = None):
    """
    Patches UrllibHTTPClient.request for tests that use the global Client.

    Usage:
        with mock_urlopen(make_response(200, {...}), make_http_error(500, b"")):
            Envelope.list()

        captured = {}
        with mock_urlopen(make_response(201, {...}), capture=captured):
            Envelope.create(name="X")
        assert captured["body"]["data"]["attributes"]["name"] == "X"
    """
    queue = list(responses)

    def fake_request(
        self: UrllibHTTPClient,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
        open_timeout: float,
        read_timeout: float,
        write_timeout: float,
    ) -> HTTPResponse:
        if capture is not None:
            capture["method"] = method
            capture["url"] = url
            capture["headers"] = headers
            capture["body"] = json.loads(body.decode("utf-8")) if body else None
        if not queue:
            raise RuntimeError("mock_urlopen: no more responses queued")
        return _resolve_queue_item(queue.pop(0))

    with patch.object(UrllibHTTPClient, "request", fake_request):
        yield
