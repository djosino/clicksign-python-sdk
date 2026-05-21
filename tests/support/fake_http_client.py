"""In-memory HTTP client for SDK tests."""

from __future__ import annotations

import json
from typing import Any

from clicksign.http_transport import HTTPConnectionError, HTTPResponse, HTTPStatusError


class FakeHTTPClient:
    name = "fake"

    def __init__(self, *responses: Any) -> None:
        self.calls: list[dict[str, Any]] = []
        self._queue: list[Any] = list(responses)

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
        open_timeout: float,
        read_timeout: float,
        write_timeout: float,
    ) -> HTTPResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "body": body,
                "open_timeout": open_timeout,
                "read_timeout": read_timeout,
                "write_timeout": write_timeout,
            }
        )
        if not self._queue:
            raise RuntimeError("FakeHTTPClient: no more responses queued")
        item = self._queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        if isinstance(item, HTTPStatusError):
            raise item
        return item


def http_response(
    status: int = 200,
    body: bytes | str | dict | None = None,
    headers: dict[str, str] | None = None,
) -> HTTPResponse:
    if body is None:
        raw = ""
    elif isinstance(body, dict):
        raw = json.dumps(body)
    elif isinstance(body, bytes):
        raw = body.decode("utf-8")
    else:
        raw = body
    return HTTPResponse(status=status, body=raw, headers=headers or {})


def http_error(
    status: int,
    body: bytes | str | dict | None = None,
    headers: dict[str, str] | None = None,
) -> HTTPStatusError:
    if body is None:
        raw = ""
    elif isinstance(body, dict):
        raw = json.dumps(body)
    elif isinstance(body, bytes):
        raw = body.decode("utf-8")
    else:
        raw = body
    return HTTPStatusError(status, raw, headers or {})


def connection_error(message: str = "connection failed") -> HTTPConnectionError:
    return HTTPConnectionError(message)
