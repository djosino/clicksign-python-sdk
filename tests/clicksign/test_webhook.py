import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import pytest

from clicksign.errors import WebhookPayloadError, WebhookSignatureError
from clicksign.webhook import (
    compute_signature,
    construct_event,
    verify_signature,
    verify_signature_or_raise,
)

SECRET = "my-secret"

SAMPLE_PAYLOAD = {
    "event": {
        "name": "acceptance_term_sent",
        "data": {
            "user": {"email": "john@example.com", "name": "John Admin"},
            "account": {"key": "a63c9e1a-de14-4434-b448-ec8601d2186b"},
        },
        "occurred_at": "2022-07-26T16:24:04.879-03:00",
    },
    "acceptance": {"key": "a8a19bb3-3154-48b9-9ac7-a6eb4826a0be", "status": "sent"},
}

LEGACY_PAYLOAD = b'{"event":"envelope.completed"}'


def _sign(payload: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _payload_bytes(payload: dict | None = None) -> bytes:
    return json.dumps(payload or SAMPLE_PAYLOAD, separators=(",", ":")).encode("utf-8")


def test_valid_signature_returns_true():
    payload = _payload_bytes()
    sig = _sign(payload, SECRET)
    assert verify_signature(payload, sig, SECRET) is True


def test_invalid_signature_returns_false():
    assert verify_signature(_payload_bytes(), "sha256=badhash", SECRET) is False


def test_empty_payload_validates():
    sig = _sign(b"", SECRET)
    assert verify_signature(b"", sig, SECRET) is True


def test_verify_or_raise_valid():
    payload = _payload_bytes()
    sig = _sign(payload, SECRET)
    verify_signature_or_raise(payload, sig, SECRET)


def test_verify_or_raise_invalid():
    with pytest.raises(WebhookSignatureError):
        verify_signature_or_raise(_payload_bytes(), "sha256=bad", SECRET)


def test_compute_signature_matches_verify():
    payload = _payload_bytes()
    sig = compute_signature(payload, SECRET)
    assert verify_signature(payload, sig, SECRET) is True


def test_construct_event_valid_payload():
    payload = _payload_bytes()
    sig = compute_signature(payload, SECRET)

    event = construct_event(payload, sig, SECRET)

    assert event.type == "acceptance_term_sent"
    assert event.name == "acceptance_term_sent"
    assert event.data["user"]["email"] == "john@example.com"
    assert event.id is None
    assert event.occurred_at is not None
    assert event.payload["acceptance"]["status"] == "sent"
    assert event.get("acceptance")["key"] == "a8a19bb3-3154-48b9-9ac7-a6eb4826a0be"


def test_construct_event_accepts_string_payload():
    payload = _payload_bytes().decode("utf-8")
    sig = compute_signature(payload, SECRET)

    event = construct_event(payload, sig, SECRET)

    assert event.type == "acceptance_term_sent"


def test_construct_event_invalid_signature():
    payload = _payload_bytes()
    with pytest.raises(WebhookSignatureError):
        construct_event(payload, "sha256=bad", SECRET)


def test_construct_event_tampered_payload():
    payload = _payload_bytes()
    sig = compute_signature(payload, SECRET)
    tampered = payload.replace(b"sent", b"hacked")

    with pytest.raises(WebhookSignatureError):
        construct_event(tampered, sig, SECRET)


def test_construct_event_invalid_json():
    payload = b"not-json"
    sig = compute_signature(payload, SECRET)

    with pytest.raises(WebhookPayloadError, match="not valid JSON"):
        construct_event(payload, sig, SECRET)


def test_construct_event_missing_event_object():
    payload = json.dumps({"acceptance": {}}).encode("utf-8")
    sig = compute_signature(payload, SECRET)

    with pytest.raises(WebhookPayloadError, match="missing 'event' object"):
        construct_event(payload, sig, SECRET)


def test_construct_event_missing_event_name():
    payload = json.dumps({"event": {"data": {}}}).encode("utf-8")
    sig = compute_signature(payload, SECRET)

    with pytest.raises(WebhookPayloadError, match="missing event name"):
        construct_event(payload, sig, SECRET)


def test_construct_event_with_id():
    payload_dict = {
        **SAMPLE_PAYLOAD,
        "event": {
            **SAMPLE_PAYLOAD["event"],
            "id": "evt-123",
        },
    }
    payload = _payload_bytes(payload_dict)
    sig = compute_signature(payload, SECRET)

    event = construct_event(payload, sig, SECRET)

    assert event.id == "evt-123"


def test_construct_event_tolerance_rejects_stale_event():
    stale = datetime.now(timezone.utc) - timedelta(hours=2)
    payload_dict = {
        **SAMPLE_PAYLOAD,
        "event": {
            **SAMPLE_PAYLOAD["event"],
            "occurred_at": stale.isoformat(),
        },
    }
    payload = _payload_bytes(payload_dict)
    sig = compute_signature(payload, SECRET)

    with pytest.raises(WebhookPayloadError, match="tolerance"):
        construct_event(payload, sig, SECRET, tolerance=300)


def test_construct_event_tolerance_allows_recent_event():
    recent = datetime.now(timezone.utc) - timedelta(seconds=30)
    payload_dict = {
        **SAMPLE_PAYLOAD,
        "event": {
            **SAMPLE_PAYLOAD["event"],
            "occurred_at": recent.isoformat(),
        },
    }
    payload = _payload_bytes(payload_dict)
    sig = compute_signature(payload, SECRET)

    event = construct_event(payload, sig, SECRET, tolerance=300)

    assert event.type == "acceptance_term_sent"


def test_legacy_flat_payload_still_verifies_signature():
    sig = _sign(LEGACY_PAYLOAD, SECRET)
    assert verify_signature(LEGACY_PAYLOAD, sig, SECRET) is True

    with pytest.raises(WebhookPayloadError, match="missing 'event' object"):
        construct_event(LEGACY_PAYLOAD, sig, SECRET)


def test_construct_event_missing_occurred_at_does_not_raise():
    """occurred_at is optional — missing value yields occurred_at=None."""
    payload_dict = {
        **SAMPLE_PAYLOAD,
        "event": {k: v for k, v in SAMPLE_PAYLOAD["event"].items() if k != "occurred_at"},
    }
    payload = _payload_bytes(payload_dict)
    sig = compute_signature(payload, SECRET)
    event = construct_event(payload, sig, SECRET)
    assert event.occurred_at is None


def test_construct_event_malformed_occurred_at_does_not_raise():
    """Unparseable occurred_at yields occurred_at=None rather than raising."""
    payload_dict = {
        **SAMPLE_PAYLOAD,
        "event": {**SAMPLE_PAYLOAD["event"], "occurred_at": "not-a-date"},
    }
    payload = _payload_bytes(payload_dict)
    sig = compute_signature(payload, SECRET)
    event = construct_event(payload, sig, SECRET)
    assert event.occurred_at is None


def test_construct_event_occurred_at_utc_z_suffix():
    """occurred_at with Z suffix is parsed as UTC."""
    payload_dict = {
        **SAMPLE_PAYLOAD,
        "event": {**SAMPLE_PAYLOAD["event"], "occurred_at": "2024-01-15T12:00:00Z"},
    }
    payload = _payload_bytes(payload_dict)
    sig = compute_signature(payload, SECRET)
    event = construct_event(payload, sig, SECRET)
    assert event.occurred_at is not None
    assert event.occurred_at.tzinfo is not None


def test_construct_event_tolerance_missing_occurred_at_skips_check():
    """Tolerance check is skipped when occurred_at is absent — no error raised."""
    payload_dict = {
        **SAMPLE_PAYLOAD,
        "event": {k: v for k, v in SAMPLE_PAYLOAD["event"].items() if k != "occurred_at"},
    }
    payload = _payload_bytes(payload_dict)
    sig = compute_signature(payload, SECRET)
    event = construct_event(payload, sig, SECRET, tolerance=300)
    assert event.occurred_at is None
