from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from ..json_api.query_builder import QueryBuilder
from ..request_options import RequestOptions, normalize_options
from ..resource import Resource

if TYPE_CHECKING:
    from ..response_metadata import ResponseMetadata
    from .client import AsyncClient

TResource = TypeVar("TResource", bound=Resource)


def attach_from_async_client(
    resource_class: type[Resource],
    client: AsyncClient,
    instances: list[Resource],
) -> list[Resource]:
    for instance in instances:
        instance._bound_async_client = client  # type: ignore[attr-defined]
    if client.last_response is not None:
        resource_class._attach_last_response(instances, client.last_response)
    return instances


class AsyncQueryProxy(Generic[TResource]):
    def __init__(self, resource_class: type[TResource], client: AsyncClient) -> None:
        self._class = resource_class
        self._client = client
        self._builder = QueryBuilder()
        self._last_response: ResponseMetadata | None = None
        self._page_responses: list[ResponseMetadata] = []
        self._on_page: Callable[[int, ResponseMetadata | None, list[TResource]], Any] | None = None

    @property
    def last_response(self) -> ResponseMetadata | None:
        return self._last_response

    @property
    def page_responses(self) -> list[ResponseMetadata]:
        return list(self._page_responses)

    def filter(self, **kwargs: Any) -> AsyncQueryProxy[TResource]:
        self._builder.filter(**kwargs)
        return self

    def order(self, field: str) -> AsyncQueryProxy[TResource]:
        self._builder.order(field)
        return self

    def page(self, n: int) -> AsyncQueryProxy[TResource]:
        self._builder.page(n)
        return self

    def per(self, n: int) -> AsyncQueryProxy[TResource]:
        self._builder.per(n)
        return self

    def with_includes(self, *types: str) -> AsyncQueryProxy[TResource]:
        self._builder.with_includes(*types)
        return self

    def fields(self, **types: list[str]) -> AsyncQueryProxy[TResource]:
        self._builder.fields(**types)
        return self

    def on_page(
        self,
        callback: Callable[[int, ResponseMetadata | None, list[TResource]], Any],
    ) -> AsyncQueryProxy[TResource]:
        self._on_page = callback
        return self

    async def to_list(
        self, *, options: RequestOptions | dict[str, Any] | None = None
    ) -> list[TResource]:
        return [item async for item in self._auto_paginate(options=options)]

    async def first(
        self, *, options: RequestOptions | dict[str, Any] | None = None
    ) -> TResource | None:
        items = await self._fetch_page(options=options)
        return items[0] if items else None

    async def last(
        self, *, options: RequestOptions | dict[str, Any] | None = None
    ) -> TResource | None:
        items = await self.to_list(options=options)
        return items[-1] if items else None

    async def count(self, *, options: RequestOptions | dict[str, Any] | None = None) -> int:
        return len(await self.to_list(options=options))

    def __aiter__(self) -> AsyncIterator[TResource]:
        return self._auto_paginate()

    async def _fetch_page(
        self,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> list[TResource]:
        params = self._builder.to_params()
        self._page_responses = []
        response = await self._client.get(
            self._class._get_endpoint(),
            params or None,
            options=options,
        )
        instances, _ = self._class._parse_response(response)
        self._last_response = self._client.last_response
        if self._last_response is not None:
            self._page_responses.append(self._last_response)
        attach_from_async_client(self._class, self._client, instances)
        return instances  # type: ignore[return-value]

    async def _auto_paginate(
        self,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> AsyncIterator[TResource]:
        from ..pagination import has_next_page, merge_page_params, resolve_page_size

        normalize_options(options)
        base_params = self._builder.to_params()
        if "page[size]" in base_params:
            per = resolve_page_size(int(base_params["page[size]"]))
        else:
            per = resolve_page_size(self._builder._per)
        page = 1
        self._page_responses = []

        while True:
            params = merge_page_params(base_params, page=page, per=per)
            response = await self._client.get(
                self._class._get_endpoint(),
                params,
                options=options,
            )
            instances, parsed = self._class._parse_response(response)
            self._last_response = self._client.last_response
            if self._last_response is not None:
                self._page_responses.append(self._last_response)
            attach_from_async_client(self._class, self._client, instances)

            if self._on_page is not None:
                self._on_page(page, self._last_response, instances)  # type: ignore[arg-type]

            for instance in instances:
                yield instance  # type: ignore[misc]

            if not has_next_page(parsed, len(instances), per):
                break

            page += 1
