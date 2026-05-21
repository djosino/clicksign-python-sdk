from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ...request_options import RequestOptions
from ...resource import Resource
from ...types import NotarialEventCreateParams
from ...types._attrs import dict_attr, str_attr


class Event(Resource):
    """Envelope/document audit events (nested routes only).

    Use :meth:`Envelope.list_events`, :meth:`Document.list_events`, or
    :meth:`create_for_document` — there is no ``GET /events`` at account level.
    """

    resource_type = "events"
    endpoint = "/events"

    @property
    def name(self) -> str | None:
        return str_attr(self, "name")

    @property
    def data(self) -> dict[str, Any] | None:
        return dict_attr(self, "data")

    @property
    def created(self) -> str | None:
        return str_attr(self, "created")

    @classmethod
    def create_for_document(
        cls,
        envelope_id: str,
        document_id: str,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[NotarialEventCreateParams],
    ) -> Event:
        from ...json_api.serializer import serialize_create

        client = cls._get_client()
        path = f"/envelopes/{envelope_id}/documents/{document_id}/events"
        body = serialize_create(cls._get_resource_type(), dict(attrs))
        response = client.post(path, body, options=options)
        instances, _ = cls._parse_response(response)
        inst = instances[0]
        inst._base_path = path.rsplit("/", 1)[0]
        inst._parent_id = document_id
        cls._attach_from_client(client, [inst])
        return inst  # type: ignore[return-value]
