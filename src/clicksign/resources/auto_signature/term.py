from __future__ import annotations

from typing import Any

from ...resource import Resource


class Term(Resource):
    resource_type = "auto_signature_terms"
    endpoint = "/auto_signature/terms"

    @classmethod
    def list(cls) -> list[Term]:  # type: ignore[override]
        raise NotImplementedError("AutoSignature::Term does not support list")

    @classmethod
    def retrieve(cls, resource_id: str) -> Term:
        raise NotImplementedError("AutoSignature::Term does not support retrieve")

    def update(self, **attrs: Any) -> Term:  # type: ignore[override]
        raise NotImplementedError("AutoSignature::Term does not support update")

    def delete(self) -> None:
        raise NotImplementedError("AutoSignature::Term does not support delete")
