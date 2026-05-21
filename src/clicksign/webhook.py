from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .errors import WebhookPayloadError, WebhookSignatureError


def compute_signature(payload: bytes | str, secret: str) -> str:
    """Return the ``Content-HMAC`` header value for a webhook body."""
    payload_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
    digest = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = compute_signature(payload, secret)
    return hmac.compare_digest(expected, signature)


def verify_signature_or_raise(payload: bytes, signature: str, secret: str) -> None:
    if not verify_signature(payload, signature, secret):
        raise WebhookSignatureError("Invalid webhook signature")


@dataclass(frozen=True)
class WebhookEvent:
    """Parsed Clicksign webhook callback."""

    type: str
    data: dict[str, Any]
    id: str | None
    occurred_at: datetime | None
    payload: dict[str, Any]

    @property
    def name(self) -> str:
        return self.type

    def __getitem__(self, key: str) -> Any:
        return self.payload[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.payload.get(key, default)


def construct_event(
    payload: bytes | str,
    signature: str,
    secret: str,
    *,
    tolerance: int | None = None,
) -> WebhookEvent:
    """Verify HMAC signature and parse a webhook payload in one step.

    Clicksign signs the raw request body with HMAC-SHA256 and
    sends the digest in the ``Content-HMAC`` header as ``sha256=<hex>``.
    When ``tolerance`` is set, ``event.occurred_at`` in the JSON body is
    checked for replay (the signature header does not embed a timestamp).
    """
    payload_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
    verify_signature_or_raise(payload_bytes, signature, secret)

    try:
        parsed = json.loads(payload_bytes)
    except json.JSONDecodeError as exc:
        raise WebhookPayloadError("Invalid webhook payload: not valid JSON") from exc

    if not isinstance(parsed, dict):
        raise WebhookPayloadError("Invalid webhook payload: root must be a JSON object")

    event = parsed.get("event")
    if not isinstance(event, dict):
        raise WebhookPayloadError("Invalid webhook payload: missing 'event' object")

    name = event.get("name")
    if not isinstance(name, str) or not name:
        raise WebhookPayloadError("Invalid webhook payload: missing event name")

    event_data = event.get("data")
    if event_data is None:
        event_data = {}
    if not isinstance(event_data, dict):
        raise WebhookPayloadError("Invalid webhook payload: event.data must be an object")

    event_id = event.get("id")
    if event_id is not None and not isinstance(event_id, str):
        event_id = str(event_id)

    occurred_at = _parse_occurred_at(event.get("occurred_at"))
    if tolerance is not None and occurred_at is not None:
        age = (datetime.now(timezone.utc) - occurred_at).total_seconds()
        if age > tolerance or age < -tolerance:
            raise WebhookPayloadError(
                "Invalid webhook payload: event timestamp outside tolerance window"
            )

    return WebhookEvent(
        type=name,
        data=dict(event_data),
        id=event_id,
        occurred_at=occurred_at,
        payload=parsed,
    )


def _parse_occurred_at(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
