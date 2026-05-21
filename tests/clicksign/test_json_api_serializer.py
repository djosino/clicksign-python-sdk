from clicksign.json_api.serializer import serialize_create, serialize_update


def test_create_no_id():
    body = serialize_create("envelopes", {"name": "Test"})
    assert "id" not in body["data"]
    assert body["data"]["type"] == "envelopes"
    assert body["data"]["attributes"]["name"] == "Test"


def test_create_no_relationships_key_when_empty():
    body = serialize_create("envelopes", {"name": "Test"})
    assert "relationships" not in body["data"]


def test_create_no_relationships_key_when_none():
    body = serialize_create("envelopes", {"name": "Test"}, None)
    assert "relationships" not in body["data"]


def test_create_with_relationships():
    rels = {"folder": {"data": {"type": "folders", "id": "uuid-1"}}}
    body = serialize_create("envelopes", {"name": "Test"}, rels)
    assert body["data"]["relationships"] == rels


def test_update_includes_id():
    body = serialize_update("envelopes", "uuid-1", {"name": "Updated"})
    assert body["data"]["id"] == "uuid-1"
    assert body["data"]["type"] == "envelopes"
    assert body["data"]["attributes"]["name"] == "Updated"


def test_update_with_relationships():
    rels = {"folder": {"data": {"type": "folders", "id": "f1"}}}
    body = serialize_update("envelopes", "e1", {}, rels)
    assert body["data"]["relationships"] == rels


def test_none_attributes_passed_through():
    body = serialize_create("envelopes", {"name": None, "status": "draft"})
    assert body["data"]["attributes"]["name"] is None
