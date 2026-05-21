import pytest

from clicksign.errors import NotFoundError, ValidationError
from clicksign.resources.notarial.document import Document
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ENV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def doc_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "documents",
        "attributes": {"filename": "test.pdf", "status": "draft", **attrs},
        "relationships": {},
    }


def test_resource_type():
    assert Document.resource_type == "documents"


def test_endpoint():
    assert Document.endpoint == "/documents"


def test_list_for_envelope():
    with mock_urlopen(make_response(200, {"data": [doc_data()]})):
        items = Document.list_for_envelope(ENV_ID)
    assert len(items) == 1
    assert items[0].filename == "test.pdf"


def test_create_nested_under_envelope():
    with mock_urlopen(make_response(201, {"data": doc_data()})):
        doc = Document.create(
            ENV_ID, filename="test.pdf", content_base64="data:application/pdf;base64,abc"
        )
    assert doc.id == UUID
    assert doc._parent_id == ENV_ID


def test_retrieve_with_envelope_id():
    with mock_urlopen(make_response(200, {"data": doc_data()})):
        doc = Document.retrieve(UUID, envelope_id=ENV_ID)
    assert doc.id == UUID
    assert doc._parent_id == ENV_ID


def test_update_uses_parent_path():
    doc = Document(
        {
            "id": UUID,
            "type": "documents",
            "attributes": {"filename": "old.pdf"},
            "relationships": {},
        }
    )
    doc._base_path = f"/envelopes/{ENV_ID}/documents"
    with mock_urlopen(make_response(200, {"data": doc_data(filename="new.pdf")})):
        doc.update(filename="new.pdf")
    assert doc.filename == "new.pdf"


def test_delete():
    doc = Document({"id": UUID, "type": "documents", "attributes": {}, "relationships": {}})
    doc._base_path = f"/envelopes/{ENV_ID}/documents"
    with mock_urlopen(make_response(204, None)):
        doc.delete()


def test_filter_with_status():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        Document.filter(status="draft").to_list()


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Filename blank"}]})):
        with pytest.raises(ValidationError, match="Filename blank"):
            Document.create(ENV_ID, filename="")


def test_retrieve_404():
    with mock_urlopen(make_http_error(404, {"errors": [{"detail": "Not found"}]})):
        with pytest.raises(NotFoundError):
            Document.retrieve(UUID, envelope_id=ENV_ID)
