from __future__ import annotations

from typing import Any

from ..resource import Resource


class AccessControlList(Resource):
    resource_type = "access_control_lists"
    endpoint = "/access_control_lists"

    @classmethod
    def create(cls, folder_id: str, group_id: str) -> AccessControlList:  # type: ignore[override]
        from ..json_api.serializer import serialize_create

        client = cls._get_client()
        rels: dict[str, Any] = {
            "folder": {"data": {"type": "folders", "id": folder_id}},
            "group": {"data": {"type": "groups", "id": group_id}},
        }
        body = serialize_create(cls._get_resource_type(), {}, rels)
        response = client.post(cls._get_endpoint(), body)
        instances, _ = cls._parse_response(response)
        return instances[0]  # type: ignore[return-value]

    @classmethod
    def destroy(cls, folder_id: str, group_id: str) -> None:  # noqa: ARG003
        client = cls._get_client()
        client.delete(cls._get_endpoint())
