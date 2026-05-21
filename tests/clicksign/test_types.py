from clicksign import Envelope
from clicksign.types import EnvelopeCreateParams, EnvelopeUpdateParams


def test_envelope_typed_attributes():
    envelope = Envelope(
        {
            "id": "env-1",
            "type": "envelopes",
            "attributes": {"name": "Contract", "status": "draft", "locale": "pt-BR"},
            "relationships": {},
        }
    )
    assert envelope.name == "Contract"
    assert envelope.status == "draft"
    assert envelope.locale == "pt-BR"


def test_envelope_create_params_typed_dict():
    params: EnvelopeCreateParams = {"name": "Contract", "locale": "pt-BR"}
    assert params["name"] == "Contract"


def test_envelope_update_params_typed_dict():
    params: EnvelopeUpdateParams = {"status": "running"}
    assert params["status"] == "running"


def test_filter_returns_typed_proxy():
    proxy = Envelope.filter(status="draft")
    assert proxy.__class__.__name__ == "QueryProxy"
