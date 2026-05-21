from __future__ import annotations

import asyncio
import concurrent.futures
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .async_client import AsyncClient


class AsyncClientSyncShim:
    """Blocking adapter so sync :class:`Resource` helpers can run inside asyncio."""

    name = "async-shim"

    def __init__(self, async_client: AsyncClient, loop: asyncio.AbstractEventLoop) -> None:
        self._client = async_client
        self._loop = loop

    @property
    def last_response(self) -> Any:
        return self._client.last_response

    def _run_coro(self, coro: Any) -> Any:
        if self._loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        return self._loop.run_until_complete(coro)

    def get(
        self,
        path: str,
        params: dict[str, str] | None = None,
        *,
        options: Any = None,
    ) -> Any:
        return self._run_coro(self._client.get(path, params, options=options))

    def post(
        self,
        path: str,
        body: dict[str, Any],
        *,
        options: Any = None,
    ) -> Any:
        return self._run_coro(self._client.post(path, body, options=options))

    def patch(
        self,
        path: str,
        body: dict[str, Any],
        *,
        options: Any = None,
    ) -> Any:
        return self._run_coro(self._client.patch(path, body, options=options))

    def delete(self, path: str, *, options: Any = None) -> None:
        self._run_coro(self._client.delete(path, options=options))
