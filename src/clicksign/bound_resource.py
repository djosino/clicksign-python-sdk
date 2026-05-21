from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from .client_scope import client_scope
from .resource import QueryProxy, Resource

if TYPE_CHECKING:
    from .clicksign_client import ClicksignClient
    from .request_options import RequestOptions


class BoundQueryProxy:
    def __init__(self, owner: ClicksignClient, proxy: QueryProxy[Any]) -> None:
        self._owner = owner
        self._proxy = proxy

    def filter(self, **kwargs: Any) -> BoundQueryProxy:
        self._proxy.filter(**kwargs)
        return self

    def order(self, field: str) -> BoundQueryProxy:
        self._proxy.order(field)
        return self

    def page(self, n: int) -> BoundQueryProxy:
        self._proxy.page(n)
        return self

    def per(self, n: int) -> BoundQueryProxy:
        self._proxy.per(n)
        return self

    def with_includes(self, *types: str) -> BoundQueryProxy:
        self._proxy.with_includes(*types)
        return self

    def fields(self, **types: builtins.list[str]) -> BoundQueryProxy:
        self._proxy.fields(**types)
        return self

    def on_page(self, callback: Any) -> BoundQueryProxy:
        self._proxy.on_page(callback)
        return self

    @property
    def page_responses(self) -> builtins.list[Any]:
        return self._proxy.page_responses

    def to_list(self, *, options: RequestOptions | dict[str, Any] | None = None) -> list[Resource]:
        with client_scope(self._owner.http, self._owner.bulk):
            return self._proxy.to_list(options=options)

    def first(self, *, options: RequestOptions | dict[str, Any] | None = None) -> Resource | None:
        with client_scope(self._owner.http, self._owner.bulk):
            return self._proxy.first(options=options)

    def last(self, *, options: RequestOptions | dict[str, Any] | None = None) -> Resource | None:
        with client_scope(self._owner.http, self._owner.bulk):
            return self._proxy.last(options=options)

    def count(self, *, options: RequestOptions | dict[str, Any] | None = None) -> int:
        with client_scope(self._owner.http, self._owner.bulk):
            return self._proxy.count(options=options)

    def __iter__(self) -> Iterator[Resource]:
        with client_scope(self._owner.http, self._owner.bulk):
            yield from self._proxy


class BoundResource:
    def __init__(self, owner: ClicksignClient, resource_cls: type[Resource]) -> None:
        self._owner = owner
        self._cls = resource_cls

    @property
    def resource_class(self) -> type[Resource]:
        return self._cls

    def list(self, *, options: RequestOptions | dict[str, Any] | None = None) -> list[Resource]:
        with client_scope(self._owner.http, self._owner.bulk):
            return self._cls.list(options=options)

    def retrieve(
        self,
        resource_id: str,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> Resource:
        with client_scope(self._owner.http, self._owner.bulk):
            return self._cls.retrieve(resource_id, options=options)

    def create(self, *args: Any, **kwargs: Any) -> Resource:
        with client_scope(self._owner.http, self._owner.bulk):
            return self._cls.create(*args, **kwargs)

    def filter(self, **kwargs: Any) -> BoundQueryProxy:
        return BoundQueryProxy(self._owner, self._cls.filter(**kwargs))

    def order(self, field: str) -> BoundQueryProxy:
        return BoundQueryProxy(self._owner, self._cls.order(field))

    def page(self, n: int) -> BoundQueryProxy:
        return BoundQueryProxy(self._owner, self._cls.page(n))

    def per(self, n: int) -> BoundQueryProxy:
        return BoundQueryProxy(self._owner, self._cls.per(n))

    def with_includes(self, *types: str) -> BoundQueryProxy:
        return BoundQueryProxy(self._owner, self._cls.with_includes(*types))

    def fields(self, **types: builtins.list[str]) -> BoundQueryProxy:
        return BoundQueryProxy(self._owner, self._cls.fields(**types))

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        attr = getattr(self._cls, name)
        if not callable(attr):
            return attr

        def bound(*args: Any, **kwargs: Any) -> Any:
            with client_scope(self._owner.http, self._owner.bulk):
                return attr(*args, **kwargs)

        return bound
