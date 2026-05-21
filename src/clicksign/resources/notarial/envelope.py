from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...request_options import RequestOptions
from ...resource import QueryProxy, Resource
from ...types import (
    EnvelopeCreateParams,
    EnvelopeFilterParams,
    EnvelopeUpdateParams,
    NotarialEventFilterParams,
)
from ...types._attrs import bool_attr, int_attr, str_attr

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from .document import Document
    from .event import Event
    from .requirement import Requirement
    from .signature_watcher import SignatureWatcher
    from .signer import Signer


class Envelope(Resource):
    resource_type = "envelopes"
    endpoint = "/envelopes"

    @property
    def name(self) -> str | None:
        return str_attr(self, "name")

    @property
    def status(self) -> str | None:
        return str_attr(self, "status")

    @property
    def locale(self) -> str | None:
        return str_attr(self, "locale")

    @property
    def created_at(self) -> str | None:
        return str_attr(self, "created_at")

    @property
    def updated_at(self) -> str | None:
        return str_attr(self, "updated_at")

    @property
    def deadline_at(self) -> str | None:
        return str_attr(self, "deadline_at")

    @property
    def auto_close(self) -> bool | None:
        return bool_attr(self, "auto_close")

    @property
    def remind_interval(self) -> int | None:
        return int_attr(self, "remind_interval")

    @property
    def block_after_refusal(self) -> bool | None:
        return bool_attr(self, "block_after_refusal")

    @property
    def folder_id(self) -> str | None:
        return (self.relationships.get("folder") or {}).get("data", {}).get("id")  # type: ignore[no-any-return]

    @classmethod
    def filter(cls, **kwargs: Unpack[EnvelopeFilterParams]) -> QueryProxy[Envelope]:  # type: ignore[override]
        return super().filter(**kwargs)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        folder_id: str | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[EnvelopeCreateParams],
    ) -> Envelope:
        rels: dict[str, Any] | None = None
        if folder_id:
            rels = {"folder": {"data": {"type": "folders", "id": folder_id}}}
        return super().create(rels, options=options, **attrs)  # type: ignore[return-value]

    def update(  # type: ignore[override]
        self,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[EnvelopeUpdateParams],
    ) -> Envelope:
        super().update(relationships, options=options, **attrs)
        return self

    @classmethod
    def list_events(
        cls,
        envelope_id: str,
        **kwargs: Unpack[NotarialEventFilterParams],
    ) -> list[Event]:
        from ...json_api.query_builder import QueryBuilder
        from .event import Event

        params = QueryBuilder().filter(**kwargs).to_params() if kwargs else None
        return cls.nested_list(
            envelope_id,
            "events",
            as_class=Event,
            params=params,
        )  # type: ignore[return-value]

    @classmethod
    def list_documents(cls, envelope_id: str) -> list[Document]:
        from .document import Document

        return cls.nested_list(envelope_id, "documents", as_class=Document)  # type: ignore[return-value]

    @classmethod
    def list_signers(cls, envelope_id: str) -> list[Signer]:
        from .signer import Signer

        return cls.nested_list(envelope_id, "signers", as_class=Signer)  # type: ignore[return-value]

    @classmethod
    def list_requirements(cls, envelope_id: str, **filters: Any) -> list[Requirement]:
        from ...json_api.query_builder import QueryBuilder
        from .requirement import Requirement

        params = QueryBuilder().filter(**filters).to_params() if filters else None
        return cls.nested_list(envelope_id, "requirements", as_class=Requirement, params=params)  # type: ignore[return-value]

    @classmethod
    def list_signature_watchers(cls, envelope_id: str) -> list[SignatureWatcher]:
        from .signature_watcher import SignatureWatcher

        return cls.nested_list(envelope_id, "signature_watchers", as_class=SignatureWatcher)  # type: ignore[return-value]

    @classmethod
    def activate(cls, envelope_id: str) -> Envelope:
        from ...json_api.serializer import serialize_create

        client = cls._get_client()
        path = f"/envelopes/{envelope_id}/activate"
        response = client.post(path, serialize_create("envelopes", {}))
        instances, _ = cls._parse_response(response)
        return instances[0]  # type: ignore[return-value]

    def notify(self, message: str, subject: str | None = None) -> None:
        from ...json_api.serializer import serialize_create

        client = self._get_client()
        attrs: dict[str, Any] = {"message": message}
        if subject is not None:
            attrs["subject"] = subject
        client.post(f"/envelopes/{self.id}/notifications", serialize_create("notifications", attrs))
