from __future__ import annotations

from typing import Any

from clicksign._http.transport import HTTPResponse, HTTPStatusError


class FakeAsyncHTTPClient:
    name = "fake-async"

    def __init__(self, *responses: Any) -> None:
        self.calls: list[dict[str, Any]] = []
        self._queue: list[Any] = list(responses)

    async def request(
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
            raise RuntimeError("FakeAsyncHTTPClient: no more responses queued")
        item = self._queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        if isinstance(item, HTTPStatusError):
            raise item
        return item

    async def aclose(self) -> None:
        pass
