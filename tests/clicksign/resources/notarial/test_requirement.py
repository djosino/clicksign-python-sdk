from typing import Any

import pytest

from clicksign.errors import NotFoundError, ValidationError
from clicksign.resources.notarial.requirement import Requirement
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ENV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
DOC_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
SIG_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"


def req_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "requirements",
        "attributes": {"action": "agree", "role": "sign", **attrs},
        "relationships": {
            "envelope": {"data": {"type": "envelopes", "id": ENV_ID}},
            "document": {"data": {"type": "documents", "id": DOC_ID}},
            "signer": {"data": {"type": "signers", "id": SIG_ID}},
        },
    }


def test_resource_type():
    assert Requirement.resource_type == "requirements"


def test_endpoint():
    assert Requirement.endpoint == "/requirements"


def test_create_with_envelope_id():
    rels = {
        "document": {"data": {"type": "documents", "id": DOC_ID}},
        "signer": {"data": {"type": "signers", "id": SIG_ID}},
    }
    with mock_urlopen(make_response(201, {"data": req_data()})):
        r = Requirement.create(ENV_ID, relationships=rels, action="agree", role="sign")
    assert r.id == UUID
    assert r._parent_id == ENV_ID


def test_retrieve_with_envelope_id():
    with mock_urlopen(make_response(200, {"data": req_data()})):
        r = Requirement.retrieve(UUID, envelope_id=ENV_ID)
    assert r.id == UUID


def test_update_requirement():
    r = Requirement(
        {"id": UUID, "type": "requirements", "attributes": {"action": "agree"}, "relationships": {}}
    )
    r._base_path = f"/envelopes/{ENV_ID}/requirements"
    with mock_urlopen(make_response(200, {"data": req_data(role="approve")})):
        r.update(role="approve")
    assert r.role == "approve"


def test_delete_requirement():
    r = Requirement({"id": UUID, "type": "requirements", "attributes": {}, "relationships": {}})
    r._base_path = f"/envelopes/{ENV_ID}/requirements"
    with mock_urlopen(make_response(204, None)):
        r.delete()


def test_filter():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        Requirement.filter(action="agree").to_list()


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Action invalid"}]})):
        with pytest.raises(ValidationError, match="Action invalid"):
            Requirement.create(ENV_ID, action="bad")


def test_retrieve_404():
    with mock_urlopen(make_http_error(404, {"errors": [{"detail": "Not found"}]})):
        with pytest.raises(NotFoundError):
            Requirement.retrieve(UUID, envelope_id=ENV_ID)


def test_relationship_accessors():
    r = Requirement(req_data())
    assert r.envelope_id == ENV_ID
    assert r.document_id == DOC_ID
    assert r.signer_id == SIG_ID


def test_create_with_signer_id_and_document_id():
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(201, {"data": req_data()}), capture=captured):
        r = Requirement.create(
            ENV_ID, signer_id=SIG_ID, document_id=DOC_ID, action="agree", role="sign"
        )
    assert r.id == UUID
    assert r._parent_id == ENV_ID
    rels = captured["body"]["data"]["relationships"]
    assert rels["signer"]["data"]["id"] == SIG_ID
    assert rels["document"]["data"]["id"] == DOC_ID


def test_list_for_document():
    payload = {"data": [req_data()], "links": {}}
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, payload), capture=captured):
        results = Requirement.list_for_document(DOC_ID)
    assert len(results) == 1
    assert results[0].id == UUID
    assert f"/documents/{DOC_ID}/relationships/requirements" in captured["url"]


def test_list_for_signer():
    payload = {"data": [req_data()], "links": {}}
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, payload), capture=captured):
        results = Requirement.list_for_signer(SIG_ID)
    assert len(results) == 1
    assert results[0].id == UUID
    assert f"/signers/{SIG_ID}/relationships/requirements" in captured["url"]


def test_list_for_document_with_filters():
    payload = {"data": [], "links": {}}
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, payload), capture=captured):
        Requirement.list_for_document(DOC_ID, action="agree")
    url = captured["url"]
    assert "filter%5Baction%5D=agree" in url or "filter[action]=agree" in url


def test_list_for_signer_with_filters():
    payload = {"data": [], "links": {}}
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, payload), capture=captured):
        Requirement.list_for_signer(SIG_ID, action="agree")
    url = captured["url"]
    assert "filter%5Baction%5D=agree" in url or "filter[action]=agree" in url
