from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..resource import Resource


class IncludedIndex:
    """Index of sideloaded JSON:API resources keyed by (type, id)."""

    def __init__(self, entries: dict[tuple[str, str], dict[str, Any]] | None = None) -> None:
        self._entries = entries or {}

    @classmethod
    def from_included(cls, included: list[dict[str, Any]]) -> IncludedIndex:
        entries: dict[tuple[str, str], dict[str, Any]] = {}
        for item in included:
            resource_type = item.get("type")
            resource_id = item.get("id")
            if resource_type and resource_id:
                entries[(str(resource_type), str(resource_id))] = item
        return cls(entries)

    def get(self, resource_type: str, resource_id: str) -> dict[str, Any] | None:
        return self._entries.get((resource_type, resource_id))

    def __len__(self) -> int:
        return len(self._entries)

    def keys(self) -> list[tuple[str, str]]:
        return list(self._entries.keys())

    def to_resources(self) -> list[Resource]:
        from .resource_registry import get_resource_class

        resources: list[Resource] = []
        for (resource_type, _resource_id), item in self._entries.items():
            resource_cls = get_resource_class(resource_type)
            instance = resource_cls._from_parsed(item)
            instance._included_index = self
            instance._resolved_relationships = {}
            resources.append(instance)
        return resources
