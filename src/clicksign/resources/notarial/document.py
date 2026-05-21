from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from .event import Event

from ...resource import QueryProxy, Resource
from ...types import (
    DocumentCreateParams,
    DocumentFilterParams,
    DocumentUpdateParams,
    NotarialEventFilterParams,
)
from ...types._attrs import str_attr


class Document(Resource):
    resource_type = "documents"
    endpoint = "/documents"

    @property
    def filename(self) -> str | None:
        return str_attr(self, "filename")

    @property
    def status(self) -> str | None:
        return str_attr(self, "status")

    @property
    def content_base64(self) -> str | None:
        return str_attr(self, "content_base64")

    @property
    def template_key(self) -> str | None:
        return str_attr(self, "template_key")

    @property
    def created_at(self) -> str | None:
        return str_attr(self, "created_at")

    @property
    def updated_at(self) -> str | None:
        return str_attr(self, "updated_at")

    @property
    def envelope_id(self) -> str | None:
        return (self.relationships.get("envelope") or {}).get("data", {}).get("id")  # type: ignore[no-any-return]

    @classmethod
    def filter(cls, **kwargs: Unpack[DocumentFilterParams]) -> QueryProxy[Document]:  # type: ignore[override]
        return super().filter(**kwargs)

    @classmethod
    def list_for_envelope(cls, envelope_id: str) -> list[Document]:
        client = cls._get_client()
        path = f"/envelopes/{envelope_id}/documents"
        response = client.get(path)
        instances, _ = cls._parse_response(response)
        for inst in instances:
            inst._base_path = path
            inst._parent_id = envelope_id
        return instances  # type: ignore[return-value]

    @classmethod
    def create(cls, envelope_id: str, **attrs: Unpack[DocumentCreateParams]) -> Document:  # type: ignore[override]
        from ...json_api.serializer import serialize_create

        client = cls._get_client()
        path = f"/envelopes/{envelope_id}/documents"
        body = serialize_create(cls._get_resource_type(), dict(attrs))
        response = client.post(path, body)
        instances, _ = cls._parse_response(response)
        inst = instances[0]
        inst._base_path = path
        inst._parent_id = envelope_id
        return inst  # type: ignore[return-value]

    @classmethod
    def retrieve(  # type: ignore[override]
        cls, document_id: str, envelope_id: str | None = None
    ) -> Document:
        client = cls._get_client()
        if envelope_id:
            path = f"/envelopes/{envelope_id}/documents/{document_id}"
        else:
            path = f"/documents/{document_id}"
        response = client.get(path)
        instances, _ = cls._parse_response(response)
        inst = instances[0]
        if envelope_id:
            inst._base_path = f"/envelopes/{envelope_id}/documents"
            inst._parent_id = envelope_id
        return inst  # type: ignore[return-value]

    def update(self, **attrs: Unpack[DocumentUpdateParams]) -> Document:  # type: ignore[override]
        super().update(None, **attrs)
        return self

    @classmethod
    def list_events(
        cls,
        document_id: str,
        *,
        envelope_id: str,
        **kwargs: Unpack[NotarialEventFilterParams],
    ) -> list[Event]:
        from ...json_api.query_builder import QueryBuilder
        from .event import Event

        client = cls._get_client()
        path = f"/envelopes/{envelope_id}/documents/{document_id}/events"
        params = QueryBuilder().filter(**kwargs).to_params() if kwargs else None
        response = client.get(path, params)
        instances, _ = Event._parse_response(response)
        Event._attach_from_client(client, instances)
        for inst in instances:
            inst._base_path = path
            inst._parent_id = document_id
        return instances  # type: ignore[return-value]
