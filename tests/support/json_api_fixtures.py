"""Shared JSON:API response fixtures for tests."""

from __future__ import annotations

from typing import Any

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
UUID2 = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UUID3 = "cccccccc-cccc-cccc-cccc-cccccccccccc"


def single(resource_type: str, id: str = UUID, **attrs: Any) -> dict[str, Any]:
    return {
        "data": {
            "id": id,
            "type": resource_type,
            "attributes": attrs,
            "relationships": {},
        }
    }


def collection(resource_type: str, items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if items is None:
        items = [{"id": UUID, "attributes": {}, "relationships": {}}]
    return {
        "data": [
            {
                "id": item.get("id", UUID),
                "type": resource_type,
                "attributes": item.get("attributes", {}),
                "relationships": item.get("relationships", {}),
            }
            for item in items
        ],
        "links": {},
    }


def envelope_response(id: str = UUID, **attrs: Any) -> dict[str, Any]:
    return single("envelopes", id, name="Test Envelope", status="draft", **attrs)


def document_response(id: str = UUID, **attrs: Any) -> dict[str, Any]:
    return single("documents", id, filename="test.pdf", status="draft", **attrs)


def signer_response(id: str = UUID, **attrs: Any) -> dict[str, Any]:
    return single("signers", id, name="Test Signer", email="test@example.com", **attrs)


def requirement_response(id: str = UUID, **attrs: Any) -> dict[str, Any]:
    return single("requirements", id, action="agree", role="sign", **attrs)


def error_response(detail: str = "Error message") -> dict[str, Any]:
    return {"errors": [{"detail": detail}]}
