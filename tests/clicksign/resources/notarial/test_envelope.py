from typing import Any

import pytest

from clicksign.errors import NotFoundError, ValidationError
from clicksign.resources.notarial.envelope import Envelope
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ENV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def envelope_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "envelopes",
        "attributes": {"name": "Test", "status": "draft", **attrs},
        "relationships": {},
    }


# ── resource configuration ────────────────────────────────────────────────


def test_resource_type():
    assert Envelope.resource_type == "envelopes"


def test_endpoint():
    assert Envelope.endpoint == "/envelopes"


# ── CRUD ─────────────────────────────────────────────────────────────────


def test_list():
    with mock_urlopen(make_response(200, {"data": [envelope_data()]})):
        items = Envelope.list()
    assert len(items) == 1
    assert items[0].name == "Test"


def test_retrieve():
    with mock_urlopen(make_response(200, {"data": envelope_data()})):
        e = Envelope.retrieve(UUID)
    assert e.id == UUID


def test_create():
    with mock_urlopen(make_response(201, {"data": envelope_data()})):
        e = Envelope.create(name="Test")
    assert e.id == UUID


def test_create_with_folder_relationship():
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(201, {"data": envelope_data()}), capture=captured):
        Envelope.create(folder_id="f1", name="Test")

    assert captured["body"]["data"]["relationships"]["folder"]["data"]["id"] == "f1"


def test_update():
    with mock_urlopen(make_response(200, {"data": envelope_data(status="running")})):
        e = Envelope(
            {
                "id": UUID,
                "type": "envelopes",
                "attributes": {"status": "draft"},
                "relationships": {},
            }
        )
        e.update(status="running")
    assert e.status == "running"


def test_delete():
    with mock_urlopen(make_response(204, None)):
        e = Envelope({"id": UUID, "type": "envelopes", "attributes": {}, "relationships": {}})
        e.delete()


# ── filter ────────────────────────────────────────────────────────────────


def test_filter_with_status():
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, {"data": [], "links": {}}), capture=captured):
        Envelope.filter(status="draft").to_list()

    assert (
        "filter%5Bstatus%5D=draft" in captured["url"] or "filter[status]=draft" in captured["url"]
    )


# ── error paths ───────────────────────────────────────────────────────────


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Name blank"}]})):
        with pytest.raises(ValidationError, match="Name blank"):
            Envelope.create(name="")


def test_retrieve_404():
    with mock_urlopen(make_http_error(404, {"errors": [{"detail": "Not found"}]})):
        with pytest.raises(NotFoundError):
            Envelope.retrieve(UUID)


# ── relationship accessors ────────────────────────────────────────────────


def test_folder_id_from_relationships():
    e = Envelope(
        {
            "id": UUID,
            "type": "envelopes",
            "attributes": {},
            "relationships": {"folder": {"data": {"type": "folders", "id": "f-1"}}},
        }
    )
    assert e.folder_id == "f-1"


def test_folder_id_none_when_absent():
    e = Envelope({"id": UUID, "type": "envelopes", "attributes": {}, "relationships": {}})
    assert e.folder_id is None


# ── nested list / activate / notify ───────────────────────────────────────


def test_list_documents():
    captured: dict[str, Any] = {}
    doc = {"id": "d1", "type": "documents", "attributes": {}, "relationships": {}}
    with mock_urlopen(make_response(200, {"data": [doc]}), capture=captured):
        items = Envelope.list_documents(ENV_ID)
    assert len(items) == 1
    assert f"/envelopes/{ENV_ID}/documents" in captured["url"]


def test_list_signers():
    with mock_urlopen(make_response(200, {"data": []})):
        Envelope.list_signers(ENV_ID)


def test_list_requirements_with_filter():
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, {"data": []}), capture=captured):
        Envelope.list_requirements(ENV_ID, document_id="d1")
    url = captured["url"]
    assert "filter%5Bdocument_id%5D=d1" in url or "filter[document_id]=d1" in url


def test_list_signature_watchers():
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, {"data": []}), capture=captured):
        Envelope.list_signature_watchers(ENV_ID)
    assert f"/envelopes/{ENV_ID}/signature_watchers" in captured["url"]


def test_activate_classmethod():
    with mock_urlopen(make_response(200, {"data": envelope_data(status="running")})):
        e = Envelope.activate(ENV_ID)
    assert e.status == "running"


def test_notify_with_message_and_subject():
    captured: dict[str, Any] = {}
    e = Envelope(envelope_data())
    with mock_urlopen(make_response(204, None), capture=captured):
        e.notify(message="Hello", subject="Subject")
    assert captured["method"] == "POST"
    assert captured["url"].endswith(f"/envelopes/{UUID}/notifications")
    assert captured["body"]["data"]["attributes"]["message"] == "Hello"
    assert captured["body"]["data"]["attributes"]["subject"] == "Subject"
