import pytest

from clicksign.errors import ValidationError
from clicksign.resources.notarial.signature_watcher import SignatureWatcher
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ENV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def sw_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "signature_watchers",
        "attributes": {"email": "watch@example.com", **attrs},
        "relationships": {},
    }


def test_resource_type():
    assert SignatureWatcher.resource_type == "signature_watchers"


def test_endpoint():
    assert SignatureWatcher.endpoint == "/signature_watchers"


def test_list_for_envelope():
    with mock_urlopen(make_response(200, {"data": [sw_data()]})):
        items = SignatureWatcher.list_for_envelope(ENV_ID)
    assert len(items) == 1
    assert items[0].email == "watch@example.com"


def test_create():
    with mock_urlopen(make_response(201, {"data": sw_data()})):
        sw = SignatureWatcher.create(ENV_ID, email="watch@example.com")
    assert sw.id == UUID
    assert sw._parent_id == ENV_ID


def test_retrieve_with_envelope_id():
    with mock_urlopen(make_response(200, {"data": sw_data()})):
        sw = SignatureWatcher.retrieve(UUID, envelope_id=ENV_ID)
    assert sw.id == UUID


def test_delete():
    sw = SignatureWatcher(
        {"id": UUID, "type": "signature_watchers", "attributes": {}, "relationships": {}}
    )
    sw._base_path = f"/envelopes/{ENV_ID}/signature_watchers"
    with mock_urlopen(make_response(204, None)):
        sw.delete()


def test_filter():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        SignatureWatcher.filter(kind="watching").to_list()


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Email blank"}]})):
        with pytest.raises(ValidationError):
            SignatureWatcher.create(ENV_ID, email="")
