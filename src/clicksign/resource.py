from __future__ import annotations

import builtins
import re
import threading
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from .client import Client
    from .request_options import RequestOptions
    from .response_metadata import ResponseMetadata

TResource = TypeVar("TResource", bound="Resource")


def _infer_resource_type(cls: type) -> str:
    name = cls.__name__
    if not name:
        return "unknown"
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    if snake.endswith("y") and not snake.endswith(("ay", "ey", "iy", "oy", "uy")):
        return snake[:-1] + "ies"
    if snake.endswith(("s", "sh", "ch", "x", "z")):
        return snake + "es"
    return snake + "s"


class Resource:
    resource_type: str | None = None
    endpoint: str | None = None
    _base_path: str | None = None
    _parent_id: str | None = None

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self._resolved_relationships: dict[str, Any] = {}

    @property
    def included_resources(self) -> builtins.list[Resource]:
        index = getattr(self, "_included_index", None)
        if index is None:
            return []
        return index.to_resources()

    @classmethod
    def _get_resource_type(cls) -> str:
        if cls.resource_type is not None:
            return cls.resource_type
        return _infer_resource_type(cls)

    @classmethod
    def _get_endpoint(cls) -> str:
        if cls.endpoint is not None:
            return cls.endpoint
        return "/" + cls._get_resource_type()

    @classmethod
    def _get_client(cls) -> Client:
        client: Client | None = threading.current_thread().__dict__.get("_clicksign_client")
        if client is not None:
            return client
        from . import _global_client

        return _global_client()  # type: ignore[no-any-return]

    # ── data accessors ──────────────────────────────────────────────────────

    @property
    def id(self) -> str | None:
        return self._data.get("id")

    @property
    def relationships(self) -> dict[str, Any]:
        return self._data.get("relationships") or {}

    @property
    def base_path(self) -> str:
        return self._base_path or self._get_endpoint()

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        attrs = self._data.get("attributes") or {}
        if name in attrs:
            return attrs[name]
        if name in self.relationships:
            return self._resolve_relationship(name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __getitem__(self, key: str) -> Any:
        attrs = self._data.get("attributes") or {}
        if key in attrs:
            return attrs[key]
        raise KeyError(key)

    @property
    def last_response(self) -> ResponseMetadata | None:
        return getattr(self, "_last_response", None)

    # ── internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _attach_last_response(
        instances: builtins.list[Resource],
        metadata: ResponseMetadata | None,
    ) -> None:
        if metadata is None:
            return
        for instance in instances:
            instance._last_response = metadata

    @classmethod
    def _attach_from_client(
        cls,
        client: Client,
        instances: builtins.list[Resource],
    ) -> builtins.list[Resource]:
        cls._attach_last_response(instances, client.last_response)
        return instances

    @classmethod
    def _from_parsed(cls, item: dict[str, Any]) -> Resource:
        instance = cls.__new__(cls)
        instance._data = item
        instance._resolved_relationships = {}
        bound = threading.current_thread().__dict__.get("_clicksign_client")
        if bound is not None:
            instance._bound_client = bound
        return instance

    @classmethod
    def _prepare_instances(
        cls,
        items: builtins.list[dict[str, Any]],
        included_index: Any,
    ) -> builtins.list[Resource]:
        instances = [cls._from_parsed(item) for item in items]
        for instance in instances:
            instance._included_index = included_index
        return instances

    def _resolve_relationship(self, name: str) -> Any:
        if name in self._resolved_relationships:
            return self._resolved_relationships[name]

        rel = self.relationships.get(name) or {}
        data = rel.get("data")
        if data is None:
            self._resolved_relationships[name] = None
            return None
        if isinstance(data, list):
            resolved = [self._resolve_resource_ref(ref) for ref in data]
            self._resolved_relationships[name] = resolved
            return resolved

        resolved = self._resolve_resource_ref(data)
        self._resolved_relationships[name] = resolved
        return resolved

    def _resolve_resource_ref(self, ref: dict[str, Any]) -> Resource | None:
        resource_type = ref.get("type")
        resource_id = ref.get("id")
        if not resource_type or not resource_id:
            return None

        index = getattr(self, "_included_index", None)
        if index is None:
            return None

        item = index.get(str(resource_type), str(resource_id))
        if item is None:
            return None

        from .json_api.resource_registry import get_resource_class

        resource_cls = get_resource_class(str(resource_type))
        instance = resource_cls._from_parsed(item)
        instance._included_index = index
        return instance

    def _copy_response_state(self, source: Resource) -> None:
        self._data = source._data
        self._included_index = getattr(source, "_included_index", None)
        self._resolved_relationships = {}

    def _resolve_client(self) -> Client:
        bound = getattr(self, "_bound_client", None)
        if bound is not None:
            return bound  # type: ignore[no-any-return]
        return self._get_client()

    @classmethod
    def _parse_response(
        cls, response: dict[str, Any]
    ) -> tuple[builtins.list[Resource], Any]:
        from .json_api.included import IncludedIndex
        from .json_api.parser import ParsedResponse, parse

        parsed: ParsedResponse = parse(response)
        included_index = IncludedIndex.from_included(parsed.included)
        instances = cls._prepare_instances(parsed.items, included_index)
        return instances, parsed

    def _build_path(self) -> str:
        base = self._base_path or self._get_endpoint()
        return f"{base}/{self.id}"

    # ── class methods (CRUD) ─────────────────────────────────────────────────

    @classmethod
    def list(
        cls: type[TResource],
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> builtins.list[TResource]:
        client = cls._get_client()
        response = client.get(cls._get_endpoint(), options=options)
        instances, _ = cls._parse_response(response)
        return cls._attach_from_client(client, instances)  # type: ignore[return-value]

    @classmethod
    def filter(cls: type[TResource], **kwargs: Any) -> QueryProxy[TResource]:
        return QueryProxy(cls).filter(**kwargs)

    @classmethod
    def retrieve(
        cls: type[TResource],
        resource_id: str,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> TResource:
        client = cls._get_client()
        path = f"{cls._get_endpoint()}/{resource_id}"
        response = client.get(path, options=options)
        instances, _ = cls._parse_response(response)
        return cls._attach_from_client(client, instances)[0]  # type: ignore[return-value]

    @classmethod
    def create(
        cls,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Any,
    ) -> Resource:
        from .json_api.serializer import serialize_create

        client = cls._get_client()
        body = serialize_create(cls._get_resource_type(), attrs, relationships or None)
        response = client.post(cls._get_endpoint(), body, options=options)
        instances, _ = cls._parse_response(response)
        return cls._attach_from_client(client, instances)[0]

    # ── instance methods ─────────────────────────────────────────────────────

    def update(
        self,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Any,
    ) -> Resource:
        from .json_api.serializer import serialize_update

        client = self._resolve_client()
        body = serialize_update(self._get_resource_type(), self.id, attrs, relationships or None)  # type: ignore[arg-type]
        response = client.patch(self._build_path(), body, options=options)
        instances, _ = self._parse_response(response)
        self._copy_response_state(instances[0])
        if client.last_response is not None:
            self._last_response = client.last_response
        return self

    def delete(self, *, options: RequestOptions | dict[str, Any] | None = None) -> None:
        client = self._resolve_client()
        client.delete(self._build_path(), options=options)
        if client.last_response is not None:
            self._last_response = client.last_response

    def reload(self, *, options: RequestOptions | dict[str, Any] | None = None) -> Resource:
        client = self._resolve_client()
        response = client.get(self._build_path(), options=options)
        instances, _ = self._parse_response(response)
        self._copy_response_state(instances[0])
        if client.last_response is not None:
            self._last_response = client.last_response
        return self

    def _resolve_async_client(self) -> Any:
        bound = getattr(self, "_bound_async_client", None)
        if bound is not None:
            return bound
        raise RuntimeError(
            "No async client bound. Retrieve or create the resource via AsyncClicksignClient."
        )

    async def update_async(
        self,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Any,
    ) -> Resource:
        from .json_api.serializer import serialize_update

        client = self._resolve_async_client()
        body = serialize_update(self._get_resource_type(), self.id, attrs, relationships or None)  # type: ignore[arg-type]
        response = await client.patch(self._build_path(), body, options=options)
        instances, _ = self._parse_response(response)
        self._copy_response_state(instances[0])
        if client.last_response is not None:
            self._last_response = client.last_response
        return self

    async def delete_async(self, *, options: RequestOptions | dict[str, Any] | None = None) -> None:
        client = self._resolve_async_client()
        await client.delete(self._build_path(), options=options)
        if client.last_response is not None:
            self._last_response = client.last_response

    async def reload_async(self, *, options: RequestOptions | dict[str, Any] | None = None) -> Resource:
        client = self._resolve_async_client()
        response = await client.get(self._build_path(), options=options)
        instances, _ = self._parse_response(response)
        self._copy_response_state(instances[0])
        if client.last_response is not None:
            self._last_response = client.last_response
        return self

    # ── nested resource helper ───────────────────────────────────────────────

    @classmethod
    def nested_list(
        cls,
        parent_id: str,
        nested_type: str,
        as_class: type[Resource] | None = None,
        params: dict[str, str] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> builtins.list[Resource]:
        client = cls._get_client()
        path = f"{cls._get_endpoint()}/{parent_id}/{nested_type}"
        response = client.get(path, params, options=options)
        target_cls: type[Resource] = as_class or cls
        instances, _ = target_cls._parse_response(response)
        target_cls._attach_from_client(client, instances)
        for inst in instances:
            inst._base_path = f"{cls._get_endpoint()}/{parent_id}/{nested_type}"
            inst._parent_id = parent_id
        return instances

    # ── query chain shortcuts ────────────────────────────────────────────────

    @classmethod
    def order(cls: type[TResource], field: str) -> QueryProxy[TResource]:
        return QueryProxy(cls).order(field)

    @classmethod
    def with_includes(cls: type[TResource], *types: str) -> QueryProxy[TResource]:
        return QueryProxy(cls).with_includes(*types)

    @classmethod
    def fields(cls: type[TResource], **types: builtins.list[str]) -> QueryProxy[TResource]:
        return QueryProxy(cls).fields(**types)

    @classmethod
    def page(cls: type[TResource], n: int) -> QueryProxy[TResource]:
        return QueryProxy(cls).page(n)

    @classmethod
    def per(cls: type[TResource], n: int) -> QueryProxy[TResource]:
        return QueryProxy(cls).per(n)


class QueryProxy(Generic[TResource]):
    def __init__(self, resource_class: type[TResource]) -> None:
        self._class = resource_class
        from .json_api.query_builder import QueryBuilder

        self._builder = QueryBuilder()
        self._last_response: ResponseMetadata | None = None
        self._page_responses: list[ResponseMetadata] = []
        self._on_page: Callable[[int, ResponseMetadata | None, list[TResource]], Any] | None = None

    @property
    def last_response(self) -> ResponseMetadata | None:
        """Metadata from the most recent page fetch (updated on each page while iterating)."""
        return self._last_response

    @property
    def page_responses(self) -> list[ResponseMetadata]:
        """Metadata for every page fetched in the current pagination run (cleared on new run)."""
        return list(self._page_responses)

    def filter(self, **kwargs: Any) -> QueryProxy[TResource]:
        self._builder.filter(**kwargs)
        return self

    def order(self, field: str) -> QueryProxy[TResource]:
        self._builder.order(field)
        return self

    def page(self, n: int) -> QueryProxy[TResource]:
        self._builder.page(n)
        return self

    def per(self, n: int) -> QueryProxy[TResource]:
        self._builder.per(n)
        return self

    def with_includes(self, *types: str) -> QueryProxy[TResource]:
        self._builder.with_includes(*types)
        return self

    def fields(self, **types: list[str]) -> QueryProxy[TResource]:
        self._builder.fields(**types)
        return self

    def on_page(
        self,
        callback: Callable[[int, ResponseMetadata | None, list[TResource]], Any],
    ) -> QueryProxy[TResource]:
        """Invoke ``callback(page_number, metadata, items)`` after each page in auto-pagination."""
        self._on_page = callback
        return self

    def to_list(
        self, *, options: RequestOptions | dict[str, Any] | None = None
    ) -> list[TResource]:
        return list(self._auto_paginate(options=options))

    def first(
        self, *, options: RequestOptions | dict[str, Any] | None = None
    ) -> TResource | None:
        items = self._fetch_page(options=options)
        return items[0] if items else None

    def last(
        self, *, options: RequestOptions | dict[str, Any] | None = None
    ) -> TResource | None:
        items = list(self._auto_paginate(options=options))
        return items[-1] if items else None

    def count(self, *, options: RequestOptions | dict[str, Any] | None = None) -> int:
        return len(list(self._auto_paginate(options=options)))

    def __iter__(self) -> Iterator[TResource]:
        return self._auto_paginate()

    def _fetch_page(
        self,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> list[TResource]:
        client = self._class._get_client()
        params = self._builder.to_params()
        self._page_responses = []
        response = client.get(self._class._get_endpoint(), params or None, options=options)
        instances, _ = self._class._parse_response(response)
        self._last_response = client.last_response
        if self._last_response is not None:
            self._page_responses.append(self._last_response)
        self._class._attach_from_client(client, instances)
        return instances  # type: ignore[return-value]

    def _auto_paginate(
        self,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> Iterator[TResource]:
        from .pagination import (
            has_next_page,
            merge_page_params,
            resolve_page_size,
        )

        client = self._class._get_client()
        base_params = self._builder.to_params()
        if "page[size]" in base_params:
            per = resolve_page_size(int(base_params["page[size]"]))
        else:
            per = resolve_page_size(self._builder._per)
        page = 1
        self._page_responses = []

        while True:
            params = merge_page_params(base_params, page=page, per=per)
            response = client.get(self._class._get_endpoint(), params, options=options)
            instances, parsed = self._class._parse_response(response)
            self._last_response = client.last_response
            if self._last_response is not None:
                self._page_responses.append(self._last_response)
            self._class._attach_from_client(client, instances)

            if self._on_page is not None:
                self._on_page(page, self._last_response, instances)  # type: ignore[arg-type]

            yield from instances

            if not has_next_page(parsed, len(instances), per):
                break

            page += 1
