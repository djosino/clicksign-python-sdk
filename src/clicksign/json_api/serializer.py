from __future__ import annotations

from typing import Any


def serialize_create(
    resource_type: str,
    attributes: dict[str, Any],
    relationships: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "type": resource_type,
        "attributes": attributes,
    }
    if relationships:
        data["relationships"] = relationships
    return {"data": data}


def serialize_update(
    resource_type: str,
    resource_id: str,
    attributes: dict[str, Any],
    relationships: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": resource_id,
        "type": resource_type,
        "attributes": attributes,
    }
    if relationships:
        data["relationships"] = relationships
    return {"data": data}
