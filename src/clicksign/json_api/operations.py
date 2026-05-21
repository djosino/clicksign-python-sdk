from __future__ import annotations

from typing import Any


class BulkRequirementOperations:
    def __init__(self) -> None:
        self._ops: list[dict[str, Any]] = []

    def add_agree(self, *, signer_id: str, document_id: str, role: str) -> None:
        self._ops.append(
            {
                "op": "add",
                "data": {
                    "type": "requirements",
                    "attributes": {"action": "agree", "role": role},
                    "relationships": {
                        "signer": {"data": {"type": "signers", "id": signer_id}},
                        "document": {"data": {"type": "documents", "id": document_id}},
                    },
                },
            }
        )

    def add_provide_evidence(self, *, signer_id: str, document_id: str, auth: str) -> None:
        self._ops.append(
            {
                "op": "add",
                "data": {
                    "type": "requirements",
                    "attributes": {"action": "provide_evidence", "auth": auth},
                    "relationships": {
                        "signer": {"data": {"type": "signers", "id": signer_id}},
                        "document": {"data": {"type": "documents", "id": document_id}},
                    },
                },
            }
        )

    def add_rubricate(
        self,
        *,
        signer_id: str,
        document_id: str,
        pages: str | None = None,
        rubric_field: str | None = None,
        kind: str | None = None,
    ) -> None:
        attrs: dict[str, Any] = {"action": "rubricate"}
        if pages is not None:
            attrs["pages"] = pages
        if rubric_field is not None:
            attrs["rubric_field"] = rubric_field
        if kind is not None:
            attrs["kind"] = kind
        self._ops.append(
            {
                "op": "add",
                "data": {
                    "type": "requirements",
                    "attributes": attrs,
                    "relationships": {
                        "signer": {"data": {"type": "signers", "id": signer_id}},
                        "document": {"data": {"type": "documents", "id": document_id}},
                    },
                },
            }
        )

    def remove(self, *, requirement_id: str) -> None:
        self._ops.append(
            {
                "op": "remove",
                "ref": {"type": "requirements", "id": requirement_id},
            }
        )

    def to_payload(self) -> dict[str, Any]:
        return {"atomic:operations": self._ops}
