from __future__ import annotations

from typing import Any

from .response_metadata import ResponseMetadata


class RawResponse:
    """HTTP response wrapper returned by ``Client.raw_request``."""

    def __init__(
        self,
        *,
        status: int,
        headers: dict[str, str],
        body: dict[str, Any] | list[Any] | None,
        metadata: ResponseMetadata,
    ) -> None:
        self.status = status
        self.headers = headers
        self.body = body
        self.metadata = metadata

    @property
    def last_response(self) -> ResponseMetadata:
        return self.metadata

    @property
    def request_id(self) -> str | None:
        return self.metadata.request_id
