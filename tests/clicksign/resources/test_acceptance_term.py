import pytest

from clicksign.errors import NotFoundError, ValidationError
from clicksign.resources.acceptance_term.whatsapp import Whatsapp
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def wa_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "acceptance_term_whatsapps",
        "attributes": {
            "sender_phone": "11999990000",
            "signer_phone": "11888880000",
            "status": "pending",
            **attrs,
        },
        "relationships": {},
    }


def test_resource_type():
    assert Whatsapp.resource_type == "acceptance_term_whatsapps"


def test_endpoint():
    assert Whatsapp.endpoint == "/acceptance_term/whatsapps"


def test_list():
    with mock_urlopen(make_response(200, {"data": [wa_data()]})):
        items = Whatsapp.list()
    assert len(items) == 1


def test_retrieve():
    with mock_urlopen(make_response(200, {"data": wa_data()})):
        w = Whatsapp.retrieve(UUID)
    assert w.id == UUID


def test_create():
    with mock_urlopen(make_response(201, {"data": wa_data()})):
        w = Whatsapp.create(sender_phone="11999990000", signer_phone="11888880000")
    assert w.id == UUID


def test_update():
    w = Whatsapp(
        {
            "id": UUID,
            "type": "acceptance_term_whatsapps",
            "attributes": {"status": "pending"},
            "relationships": {},
        }
    )
    with mock_urlopen(make_response(200, {"data": wa_data(status="sent")})):
        w.update(status="sent")
    assert w.status == "sent"


def test_filter_status():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        Whatsapp.filter(status="pending").to_list()


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Phone invalid"}]})):
        with pytest.raises(ValidationError):
            Whatsapp.create(sender_phone="bad")


def test_retrieve_404():
    with mock_urlopen(make_http_error(404, {"errors": [{"detail": "Not found"}]})):
        with pytest.raises(NotFoundError):
            Whatsapp.retrieve(UUID)
