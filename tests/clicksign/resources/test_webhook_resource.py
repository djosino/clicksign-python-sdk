import pytest

from clicksign.errors import NotFoundError, ValidationError
from clicksign.resources.webhook import Webhook
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def wh_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "webhooks",
        "attributes": {"endpoint": "https://example.com/wh", "status": "active", **attrs},
        "relationships": {},
    }


def test_resource_type():
    assert Webhook.resource_type == "webhooks"


def test_endpoint():
    assert Webhook.endpoint == "/webhooks"


def test_list():
    with mock_urlopen(make_response(200, {"data": [wh_data()]})):
        items = Webhook.list()
    assert len(items) == 1


def test_retrieve():
    with mock_urlopen(make_response(200, {"data": wh_data()})):
        wh = Webhook.retrieve(UUID)
    assert wh.id == UUID


def test_create():
    with mock_urlopen(make_response(201, {"data": wh_data()})):
        wh = Webhook.create(endpoint="https://example.com/wh", events=["envelope.completed"])
    assert wh.id == UUID


def test_update():
    wh = Webhook(
        {"id": UUID, "type": "webhooks", "attributes": {"status": "inactive"}, "relationships": {}}
    )
    with mock_urlopen(make_response(200, {"data": wh_data(status="active")})):
        wh.update(status="active")
    assert wh.status == "active"


def test_delete():
    wh = Webhook({"id": UUID, "type": "webhooks", "attributes": {}, "relationships": {}})
    with mock_urlopen(make_response(204, None)):
        wh.delete()


def test_filter_status():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        Webhook.filter(status="active").to_list()


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Endpoint invalid"}]})):
        with pytest.raises(ValidationError):
            Webhook.create(endpoint="bad")


def test_retrieve_404():
    with mock_urlopen(make_http_error(404, {"errors": [{"detail": "Not found"}]})):
        with pytest.raises(NotFoundError):
            Webhook.retrieve(UUID)
