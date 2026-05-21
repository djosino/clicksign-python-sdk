import pytest

from clicksign.errors import ValidationError
from clicksign.resources.notarial.signer import Signer
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ENV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def signer_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "signers",
        "attributes": {"name": "Maria Silva", "email": "maria@example.com", **attrs},
        "relationships": {"envelope": {"data": {"type": "envelopes", "id": ENV_ID}}},
    }


def test_resource_type():
    assert Signer.resource_type == "signers"


def test_endpoint():
    assert Signer.endpoint == "/signers"


def test_list_for_envelope():
    with mock_urlopen(make_response(200, {"data": [signer_data()]})):
        items = Signer.list_for_envelope(ENV_ID)
    assert len(items) == 1
    assert items[0].name == "Maria Silva"


def test_create_nested_under_envelope():
    with mock_urlopen(make_response(201, {"data": signer_data()})):
        s = Signer.create(ENV_ID, name="Maria Silva", email="maria@example.com")
    assert s.id == UUID
    assert s._parent_id == ENV_ID


def test_delete():
    s = Signer({"id": UUID, "type": "signers", "attributes": {}, "relationships": {}})
    s._base_path = f"/envelopes/{ENV_ID}/signers"
    with mock_urlopen(make_response(204, None)):
        s.delete()


def test_filter():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        Signer.filter(name="Maria").to_list()


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Email blank"}]})):
        with pytest.raises(ValidationError, match="Email blank"):
            Signer.create(ENV_ID, name="X", email="")


def test_envelope_id_from_relationships():
    s = Signer(signer_data())
    assert s.envelope_id == ENV_ID
