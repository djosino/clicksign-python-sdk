from __future__ import annotations

from typing import Any

from ..resource import Resource


class EnvelopeBulkCreation(Resource):
    resource_type = "envelope_bulk_creations"
    endpoint = "/envelope_bulk_creations"

    @classmethod
    def create(cls, **attrs: Any) -> EnvelopeBulkCreation:  # type: ignore[override]
        return super().create(**attrs)  # type: ignore[return-value]

    @classmethod
    def list(cls) -> list[EnvelopeBulkCreation]:  # type: ignore[override]
        raise NotImplementedError("EnvelopeBulkCreation does not support list")

    @classmethod
    def retrieve(cls, resource_id: str) -> EnvelopeBulkCreation:
        raise NotImplementedError("EnvelopeBulkCreation does not support retrieve")

    def update(self, **attrs: Any) -> EnvelopeBulkCreation:  # type: ignore[override]
        raise NotImplementedError("EnvelopeBulkCreation does not support update")

    def delete(self) -> None:
        raise NotImplementedError("EnvelopeBulkCreation does not support delete")
