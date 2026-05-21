from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ...resource import QueryProxy, Resource
from ...types import SignerCreateParams, SignerFilterParams
from ...types._attrs import bool_attr, str_attr


class Signer(Resource):
    resource_type = "signers"
    endpoint = "/signers"

    @property
    def name(self) -> str | None:
        return str_attr(self, "name")

    @property
    def email(self) -> str | None:
        return str_attr(self, "email")

    @property
    def phone_number(self) -> str | None:
        return str_attr(self, "phone_number")

    @property
    def documentation(self) -> str | None:
        return str_attr(self, "documentation")

    @property
    def birthday(self) -> str | None:
        return str_attr(self, "birthday")

    @property
    def has_documentation(self) -> bool | None:
        return bool_attr(self, "has_documentation")

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
    def filter(cls, **kwargs: Unpack[SignerFilterParams]) -> QueryProxy[Signer]:  # type: ignore[override]
        return super().filter(**kwargs)

    @classmethod
    def list_for_envelope(cls, envelope_id: str) -> list[Signer]:
        client = cls._get_client()
        path = f"/envelopes/{envelope_id}/signers"
        response = client.get(path)
        instances, _ = cls._parse_response(response)
        for inst in instances:
            inst._base_path = path
            inst._parent_id = envelope_id
        return instances  # type: ignore[return-value]

    @classmethod
    def create(cls, envelope_id: str, **attrs: Unpack[SignerCreateParams]) -> Signer:  # type: ignore[override]
        from ...json_api.serializer import serialize_create

        client = cls._get_client()
        path = f"/envelopes/{envelope_id}/signers"
        body = serialize_create(cls._get_resource_type(), dict(attrs))
        response = client.post(path, body)
        instances, _ = cls._parse_response(response)
        inst = instances[0]
        inst._base_path = path
        inst._parent_id = envelope_id
        return inst  # type: ignore[return-value]

    def update(self, **attrs: object) -> Signer:  # type: ignore[override]
        raise NotImplementedError("Signer does not support update")

    def notify(self, message: str, subject: str | None = None) -> None:
        from ...json_api.serializer import serialize_create

        client = self._get_client()
        attrs: dict[str, str | None] = {"message": message}
        if subject is not None:
            attrs["subject"] = subject
        parent_id = getattr(self, "_parent_id", None)
        if parent_id:
            client.post(
                f"/envelopes/{parent_id}/signers/{self.id}/notifications",
                serialize_create("notifications", attrs),
            )
        else:
            client.post(
                f"/signers/{self.id}/notifications", serialize_create("notifications", attrs)
            )
