from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ...resource import QueryProxy, Resource
from ...types import RequirementCreateParams, RequirementFilterParams, RequirementUpdateParams
from ...types._attrs import bool_attr, str_attr


class Requirement(Resource):
    resource_type = "requirements"
    endpoint = "/requirements"

    @property
    def action(self) -> str | None:
        return str_attr(self, "action")

    @property
    def role(self) -> str | None:
        return str_attr(self, "role")

    @property
    def rubricate(self) -> bool | None:
        return bool_attr(self, "rubricate")

    @property
    def created_at(self) -> str | None:
        return str_attr(self, "created_at")

    @property
    def updated_at(self) -> str | None:
        return str_attr(self, "updated_at")

    @property
    def envelope_id(self) -> str | None:
        return (self.relationships.get("envelope") or {}).get("data", {}).get("id")  # type: ignore[no-any-return]

    @property
    def document_id(self) -> str | None:
        return (self.relationships.get("document") or {}).get("data", {}).get("id")  # type: ignore[no-any-return]

    @property
    def signer_id(self) -> str | None:
        return (self.relationships.get("signer") or {}).get("data", {}).get("id")  # type: ignore[no-any-return]

    @classmethod
    def filter(cls, **kwargs: Unpack[RequirementFilterParams]) -> QueryProxy[Requirement]:  # type: ignore[override]
        return super().filter(**kwargs)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        envelope_id: str,
        relationships: dict[str, Any] | None = None,
        **attrs: Unpack[RequirementCreateParams],
    ) -> Requirement:
        from ...json_api.serializer import serialize_create

        client = cls._get_client()
        path = f"/envelopes/{envelope_id}/requirements"
        body = serialize_create(cls._get_resource_type(), dict(attrs), relationships or None)
        response = client.post(path, body)
        instances, _ = cls._parse_response(response)
        inst = instances[0]
        inst._base_path = path
        inst._parent_id = envelope_id
        return inst  # type: ignore[return-value]

    @classmethod
    def retrieve(  # type: ignore[override]
        cls, requirement_id: str, envelope_id: str | None = None
    ) -> Requirement:
        client = cls._get_client()
        if envelope_id:
            path = f"/envelopes/{envelope_id}/requirements/{requirement_id}"
        else:
            path = f"/requirements/{requirement_id}"
        response = client.get(path)
        instances, _ = cls._parse_response(response)
        inst = instances[0]
        if envelope_id:
            inst._base_path = f"/envelopes/{envelope_id}/requirements"
            inst._parent_id = envelope_id
        return inst  # type: ignore[return-value]

    def update(self, **attrs: Unpack[RequirementUpdateParams]) -> Requirement:  # type: ignore[override]
        super().update(None, **attrs)
        return self

    @classmethod
    def list_for_document(cls, document_id: str, **filters: Any) -> list[Requirement]:
        client = cls._get_client()
        path = f"/documents/{document_id}/relationships/requirements"
        params = {f"filter[{k}]": str(v) for k, v in filters.items()} if filters else None
        response = client.get(path, params)
        instances, _ = cls._parse_response(response)
        return instances  # type: ignore[return-value]

    @classmethod
    def list_for_signer(cls, signer_id: str, **filters: Any) -> list[Requirement]:
        client = cls._get_client()
        path = f"/signers/{signer_id}/relationships/requirements"
        params = {f"filter[{k}]": str(v) for k, v in filters.items()} if filters else None
        response = client.get(path, params)
        instances, _ = cls._parse_response(response)
        return instances  # type: ignore[return-value]
