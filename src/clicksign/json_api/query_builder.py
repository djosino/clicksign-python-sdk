from __future__ import annotations

from typing import Any

from ..pagination import resolve_page_size


class QueryBuilder:
    def __init__(self) -> None:
        self._filters: dict[str, Any] = {}
        self._sort: str | None = None
        self._page: int | None = None
        self._per: int | None = None
        self._includes: list[str] = []
        self._fields: dict[str, list[str]] = {}

    def filter(self, **kwargs: Any) -> QueryBuilder:
        self._filters.update(kwargs)
        return self

    def order(self, field: str) -> QueryBuilder:
        self._sort = field
        return self

    def page(self, n: int) -> QueryBuilder:
        self._page = n
        return self

    def per(self, n: int) -> QueryBuilder:
        resolve_page_size(n)
        self._per = n
        return self

    def with_includes(self, *types: str) -> QueryBuilder:
        if not types:
            raise ValueError("with_includes requires at least one type")
        for t in types:
            if not isinstance(t, str):
                raise ValueError(f"include types must be str, got {type(t).__name__!r}")
        self._includes.extend(types)
        return self

    def fields(self, **types: list[str]) -> QueryBuilder:
        self._fields.update(types)
        return self

    def to_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        for key, value in self._filters.items():
            if isinstance(value, bool):
                params[f"filter[{key}]"] = "true" if value else "false"
            else:
                params[f"filter[{key}]"] = str(value)
        if self._sort is not None:
            params["sort"] = self._sort
        if self._page is not None:
            params["page[number]"] = str(self._page)
        if self._per is not None:
            params["page[size]"] = str(self._per)
        if self._includes:
            params["include"] = ",".join(self._includes)
        for resource_type, field_list in self._fields.items():
            params[f"fields[{resource_type}]"] = ",".join(field_list)
        return params
