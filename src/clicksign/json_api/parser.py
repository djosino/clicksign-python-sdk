from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "type": item.get("type"),
        "attributes": item.get("attributes") or {},
        "relationships": item.get("relationships") or {},
    }


@dataclass
class ParsedResponse:
    items: list[dict[str, Any]] = field(default_factory=list)
    included: list[dict[str, Any]] = field(default_factory=list)
    links: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


def parse(body: dict[str, Any]) -> ParsedResponse:
    data = body.get("data")
    included_raw = [item for item in (body.get("included") or []) if item.get("type")]
    links = body.get("links") or {}
    meta = body.get("meta") or {}

    if data is None:
        items_raw: list[dict[str, Any]] = []
    elif isinstance(data, list):
        items_raw = data
    else:
        items_raw = [data]

    items = [normalize_item(item) for item in items_raw]
    included = [normalize_item(item) for item in included_raw]

    return ParsedResponse(items=items, included=included, links=links, meta=meta)
