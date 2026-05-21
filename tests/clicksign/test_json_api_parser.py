from clicksign.json_api.parser import parse


def test_single_object_returns_one_item():
    body = {
        "data": {"id": "1", "type": "envelopes", "attributes": {"name": "A"}, "relationships": {}}
    }
    result = parse(body)
    assert len(result.items) == 1
    assert result.items[0]["id"] == "1"


def test_array_data_returns_all_items():
    body = {
        "data": [
            {"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}},
            {"id": "2", "type": "envelopes", "attributes": {}, "relationships": {}},
        ]
    }
    result = parse(body)
    assert len(result.items) == 2


def test_null_data_returns_empty():
    result = parse({"data": None})
    assert result.items == []


def test_missing_data_returns_empty():
    result = parse({})
    assert result.items == []


def test_included_parsed():
    body = {
        "data": {"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}},
        "included": [{"id": "f1", "type": "folders", "attributes": {}, "relationships": {}}],
    }
    result = parse(body)
    assert len(result.included) == 1
    assert result.included[0]["type"] == "folders"


def test_included_without_type_filtered_out():
    body = {
        "data": {"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}},
        "included": [
            {"id": "x", "attributes": {}},  # no type — API bug
            {"id": "f1", "type": "folders", "attributes": {}, "relationships": {}},
        ],
    }
    result = parse(body)
    assert len(result.included) == 1
    assert result.included[0]["id"] == "f1"


def test_missing_attributes_defaults_to_empty_dict():
    body = {"data": {"id": "1", "type": "envelopes"}}
    result = parse(body)
    assert result.items[0]["attributes"] == {}
    assert result.items[0]["relationships"] == {}


def test_links_and_meta_parsed():
    body = {
        "data": [],
        "links": {"next": "http://example.com/page2"},
        "meta": {"total": 5},
    }
    result = parse(body)
    assert result.links == {"next": "http://example.com/page2"}
    assert result.meta == {"total": 5}
