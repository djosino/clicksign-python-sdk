from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from ..client_scope import client_scope
from ..json_api.serializer import serialize_create
from ..resource import Resource
from .bridge import AsyncClientSyncShim
from .resource import AsyncQueryProxy, attach_from_async_client

if TYPE_CHECKING:
    from ..request_options import RequestOptions
    from .clicksign_client import AsyncClicksignClient


class AsyncBoundQueryProxy:
    def __init__(self, owner: AsyncClicksignClient, proxy: AsyncQueryProxy) -> None:
        self._owner = owner
        self._proxy = proxy

    def filter(self, **kwargs: Any) -> AsyncBoundQueryProxy:
        self._proxy.filter(**kwargs)
        return self

    def order(self, field: str) -> AsyncBoundQueryProxy:
        self._proxy.order(field)
        return self

    def page(self, n: int) -> AsyncBoundQueryProxy:
        self._proxy.page(n)
        return self

    def per(self, n: int) -> AsyncBoundQueryProxy:
        self._proxy.per(n)
        return self

    def with_includes(self, *types: str) -> AsyncBoundQueryProxy:
        self._proxy.with_includes(*types)
        return self

    def fields(self, **types: list[str]) -> AsyncBoundQueryProxy:
        self._proxy.fields(**types)
        return self

    def on_page(self, callback: Any) -> AsyncBoundQueryProxy:
        self._proxy.on_page(callback)
        return self

    @property
    def last_response(self):
        return self._proxy.last_response

    @property
    def page_responses(self):
        return self._proxy.page_responses

    async def to_list(
        self, *, options: RequestOptions | dict[str, Any] | None = None
    ) -> list[Resource]:
        return await self._proxy.to_list(options=options)

    async def first(
        self, *, options: RequestOptions | dict[str, Any] | None = None
    ) -> Resource | None:
        return await self._proxy.first(options=options)

    async def last(
        self, *, options: RequestOptions | dict[str, Any] | None = None
    ) -> Resource | None:
        return await self._proxy.last(options=options)

    async def count(self, *, options: RequestOptions | dict[str, Any] | None = None) -> int:
        return await self._proxy.count(options=options)

    def __aiter__(self) -> AsyncIterator[Resource]:
        return self._proxy._auto_paginate()


class AsyncBoundResource:
    def __init__(self, owner: AsyncClicksignClient, resource_cls: type[Resource]) -> None:
        self._owner = owner
        self._cls = resource_cls

    @property
    def resource_class(self) -> type[Resource]:
        return self._cls

    async def list(
        self, *, options: RequestOptions | dict[str, Any] | None = None
    ) -> list[Resource]:
        client = self._owner.http
        response = await client.get(self._cls._get_endpoint(), options=options)
        instances, _ = self._cls._parse_response(response)
        return attach_from_async_client(self._cls, client, instances)

    async def retrieve(
        self,
        resource_id: str,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> Resource:
        client = self._owner.http
        path = f"{self._cls._get_endpoint()}/{resource_id}"
        response = await client.get(path, options=options)
        instances, _ = self._cls._parse_response(response)
        return attach_from_async_client(self._cls, client, instances)[0]

    async def create(self, *args: Any, **kwargs: Any) -> Resource:
        relationships = kwargs.pop("relationships", None)
        options = kwargs.pop("options", None)
        if args:
            if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
                kwargs = args[0]
            else:
                raise TypeError("create() accepts keyword attributes or a single attributes dict")
        client = self._owner.http
        body = serialize_create(self._cls._get_resource_type(), kwargs, relationships)
        response = await client.post(self._cls._get_endpoint(), body, options=options)
        instances, _ = self._cls._parse_response(response)
        return attach_from_async_client(self._cls, client, instances)[0]

    def filter(self, **kwargs: Any) -> AsyncBoundQueryProxy:
        proxy = AsyncQueryProxy(self._cls, self._owner.http).filter(**kwargs)
        return AsyncBoundQueryProxy(self._owner, proxy)

    def order(self, field: str) -> AsyncBoundQueryProxy:
        proxy = AsyncQueryProxy(self._cls, self._owner.http).order(field)
        return AsyncBoundQueryProxy(self._owner, proxy)

    def page(self, n: int) -> AsyncBoundQueryProxy:
        proxy = AsyncQueryProxy(self._cls, self._owner.http).page(n)
        return AsyncBoundQueryProxy(self._owner, proxy)

    def per(self, n: int) -> AsyncBoundQueryProxy:
        proxy = AsyncQueryProxy(self._cls, self._owner.http).per(n)
        return AsyncBoundQueryProxy(self._owner, proxy)

    def with_includes(self, *types: str) -> AsyncBoundQueryProxy:
        return AsyncBoundQueryProxy(
            self._owner,
            AsyncQueryProxy(self._cls, self._owner.http).with_includes(*types),
        )

    def fields(self, **types: list[str]) -> AsyncBoundQueryProxy:
        return AsyncBoundQueryProxy(
            self._owner,
            AsyncQueryProxy(self._cls, self._owner.http).fields(**types),
        )

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        attr = getattr(self._cls, name)
        if not callable(attr):
            return attr

        async def bound(*args: Any, **kwargs: Any) -> Any:
            loop = asyncio.get_running_loop()
            shim = AsyncClientSyncShim(self._owner.http, loop)
            with client_scope(shim, None):  # type: ignore[arg-type]
                result = attr(*args, **kwargs)
            client = self._owner.http
            if isinstance(result, Resource):
                result._bound_async_client = client  # type: ignore[attr-defined]
                if client.last_response is not None:
                    result._last_response = client.last_response
            elif isinstance(result, list):
                attach_from_async_client(self._cls, client, result)
            return result

        return bound
