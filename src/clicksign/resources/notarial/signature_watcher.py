from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ...resource import QueryProxy, Resource
from ...types import SignatureWatcherCreateParams, SignatureWatcherFilterParams
from ...types._attrs import str_attr


class SignatureWatcher(Resource):
    resource_type = "signature_watchers"
    endpoint = "/signature_watchers"

    @property
    def email(self) -> str | None:
        return str_attr(self, "email")

    @property
    def kind(self) -> str | None:
        return str_attr(self, "kind")

    @property
    def created_at(self) -> str | None:
        return str_attr(self, "created_at")

    @property
    def updated_at(self) -> str | None:
        return str_attr(self, "updated_at")

    @classmethod
    def filter(  # type: ignore[override]
        cls, **kwargs: Unpack[SignatureWatcherFilterParams]
    ) -> QueryProxy[SignatureWatcher]:
        return super().filter(**kwargs)

    @classmethod
    def list_for_envelope(cls, envelope_id: str) -> list[SignatureWatcher]:
        client = cls._get_client()
        path = f"/envelopes/{envelope_id}/signature_watchers"
        response = client.get(path)
        instances, _ = cls._parse_response(response)
        for inst in instances:
            inst._base_path = path
            inst._parent_id = envelope_id
        return instances  # type: ignore[return-value]

    @classmethod
    def create(  # type: ignore[override]
        cls, envelope_id: str, **attrs: Unpack[SignatureWatcherCreateParams]
    ) -> SignatureWatcher:
        from ...json_api.serializer import serialize_create

        client = cls._get_client()
        path = f"/envelopes/{envelope_id}/signature_watchers"
        body = serialize_create(cls._get_resource_type(), dict(attrs))
        response = client.post(path, body)
        instances, _ = cls._parse_response(response)
        inst = instances[0]
        inst._base_path = path
        inst._parent_id = envelope_id
        return inst  # type: ignore[return-value]

    @classmethod
    def retrieve(  # type: ignore[override]
        cls, watcher_id: str, envelope_id: str | None = None
    ) -> SignatureWatcher:
        client = cls._get_client()
        if envelope_id:
            path = f"/envelopes/{envelope_id}/signature_watchers/{watcher_id}"
        else:
            path = f"/signature_watchers/{watcher_id}"
        response = client.get(path)
        instances, _ = cls._parse_response(response)
        inst = instances[0]
        if envelope_id:
            inst._base_path = f"/envelopes/{envelope_id}/signature_watchers"
            inst._parent_id = envelope_id
        return inst  # type: ignore[return-value]

    def update(self, **attrs: object) -> SignatureWatcher:  # type: ignore[override]
        raise NotImplementedError("SignatureWatcher does not support update")
