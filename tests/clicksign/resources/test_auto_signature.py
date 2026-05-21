import pytest

from clicksign.errors import ValidationError
from clicksign.resources.auto_signature.term import Term
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def term_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "auto_signature_terms",
        "attributes": {"name": "Maria Silva", **attrs},
        "relationships": {},
    }


def test_resource_type():
    assert Term.resource_type == "auto_signature_terms"


def test_endpoint():
    assert Term.endpoint == "/auto_signature/terms"


def test_create():
    with mock_urlopen(make_response(201, {"data": term_data()})):
        t = Term.create(name="Maria Silva", email="maria@example.com")
    assert t.id == UUID
    assert t.name == "Maria Silva"


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Email blank"}]})):
        with pytest.raises(ValidationError):
            Term.create(name="X", email="")
