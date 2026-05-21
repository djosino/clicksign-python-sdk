import pytest

from clicksign.resource import QueryProxy, Resource, _infer_resource_type
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

BASE = "http://test.clicksign.com/api/v3"


# ── _infer_resource_type ───────────────────────────────────────────────────


def test_infer_snake_plural():
    class Envelope(Resource):
        pass

    assert _infer_resource_type(Envelope) == "envelopes"


def test_infer_camel_case():
    class SignatureWatcher(Resource):
        pass

    assert _infer_resource_type(SignatureWatcher) == "signature_watchers"


def test_infer_anonymous_class_safe():
    cls = type("", (Resource,), {})
    result = _infer_resource_type(cls)
    assert isinstance(result, str)


def test_explicit_resource_type_overrides():
    class MyResource(Resource):
        resource_type = "custom_type"

    assert MyResource._get_resource_type() == "custom_type"


def test_explicit_endpoint_overrides():
    class MyResource(Resource):
        endpoint = "/custom/path"

    assert MyResource._get_endpoint() == "/custom/path"


def test_endpoint_defaults_to_resource_type():
    class Envelope(Resource):
        pass

    assert Envelope._get_endpoint() == "/envelopes"


# ── attribute access ──────────────────────────────────────────────────────


def test_dynamic_attribute_access():
    r = Resource(
        {"id": "1", "type": "envelopes", "attributes": {"name": "Test"}, "relationships": {}}
    )
    assert r.name == "Test"


def test_getitem_access():
    r = Resource(
        {"id": "1", "type": "envelopes", "attributes": {"status": "draft"}, "relationships": {}}
    )
    assert r["status"] == "draft"


def test_unknown_attribute_raises_attribute_error():
    r = Resource({"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}})
    with pytest.raises(AttributeError):
        _ = r.nonexistent


def test_id_accessible():
    r = Resource({"id": "abc", "type": "envelopes", "attributes": {}, "relationships": {}})
    assert r.id == "abc"


def test_relationships_accessible():
    rels = {"folder": {"data": {"type": "folders", "id": "f1"}}}
    r = Resource({"id": "1", "type": "envelopes", "attributes": {}, "relationships": rels})
    assert r.relationships == rels


def test_base_path_defaults_to_endpoint():
    class MyRes(Resource):
        endpoint = "/myres"

    r = MyRes({"id": "1", "attributes": {}, "relationships": {}})
    assert r.base_path == "/myres"


def test_list_raises_when_given_args():
    class Envelope(Resource):
        resource_type = "envelopes"
        endpoint = "/envelopes"

    with pytest.raises(TypeError):
        Envelope.list("extra_arg")  # type: ignore[call-arg]


# ── Resource class for tests ──────────────────────────────────────────────


class Envelope(Resource):
    resource_type = "envelopes"
    endpoint = "/envelopes"


# ── CRUD ─────────────────────────────────────────────────────────────────


def test_list_returns_instances():
    with mock_urlopen(
        make_response(
            200,
            {
                "data": [
                    {
                        "id": "1",
                        "type": "envelopes",
                        "attributes": {"name": "E1"},
                        "relationships": {},
                    }
                ]
            },
        )
    ):
        items = Envelope.list()
    assert len(items) == 1
    assert items[0].name == "E1"


def test_retrieve_returns_instance():
    with mock_urlopen(
        make_response(
            200,
            {
                "data": {
                    "id": "1",
                    "type": "envelopes",
                    "attributes": {"name": "E1"},
                    "relationships": {},
                }
            },
        )
    ):
        e = Envelope.retrieve("1")
    assert e.id == "1"
    assert e.name == "E1"


def test_create_returns_instance():
    with mock_urlopen(
        make_response(
            201,
            {
                "data": {
                    "id": "new-1",
                    "type": "envelopes",
                    "attributes": {"name": "New"},
                    "relationships": {},
                }
            },
        )
    ):
        e = Envelope.create(name="New")
    assert e.id == "new-1"
    assert e.name == "New"


def test_update_sends_patch_returns_self():
    with mock_urlopen(
        make_response(
            200,
            {
                "data": {
                    "id": "1",
                    "type": "envelopes",
                    "attributes": {"name": "Updated"},
                    "relationships": {},
                }
            },
        )
    ):
        e = Envelope(
            {"id": "1", "type": "envelopes", "attributes": {"name": "Old"}, "relationships": {}}
        )
        result = e.update(name="Updated")
    assert result is e
    assert e.name == "Updated"


def test_delete_sends_delete_returns_none():
    with mock_urlopen(make_response(204, None)):
        e = Envelope({"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}})
        result = e.delete()
    assert result is None


def test_reload_refreshes_data():
    with mock_urlopen(
        make_response(
            200,
            {
                "data": {
                    "id": "1",
                    "type": "envelopes",
                    "attributes": {"status": "running"},
                    "relationships": {},
                }
            },
        )
    ):
        e = Envelope(
            {"id": "1", "type": "envelopes", "attributes": {"status": "draft"}, "relationships": {}}
        )
        e.reload()
    assert e.status == "running"


# ── QueryProxy ────────────────────────────────────────────────────────────


def test_filter_returns_query_proxy():
    proxy = Envelope.filter(status="draft")
    assert isinstance(proxy, QueryProxy)


def test_query_proxy_all_chain_methods_return_proxy():
    proxy = Envelope.filter(status="draft")
    assert isinstance(proxy.order("-created"), QueryProxy)
    assert isinstance(proxy.page(1), QueryProxy)
    assert isinstance(proxy.per(20), QueryProxy)
    assert isinstance(proxy.with_includes("folder"), QueryProxy)
    assert isinstance(proxy.fields(envelopes=["name"]), QueryProxy)


def test_query_proxy_to_list():
    with mock_urlopen(
        make_response(
            200,
            {
                "data": [{"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}}],
                "links": {"next": None},
            },
        )
    ):
        items = Envelope.filter(status="draft").to_list()
    assert len(items) == 1


def test_query_proxy_first():
    with mock_urlopen(
        make_response(
            200,
            {
                "data": [{"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}}],
                "links": {"next": None},
            },
        )
    ):
        item = Envelope.filter().first()
    assert item is not None
    assert item.id == "1"


def test_query_proxy_last():
    with mock_urlopen(
        make_response(
            200,
            {
                "data": [{"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}}],
                "links": {"next": None},
            },
        )
    ):
        item = Envelope.filter().last()
    assert item.id == "1"


def test_query_proxy_count():
    with mock_urlopen(
        make_response(
            200,
            {
                "data": [{"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}}],
                "links": {"next": None},
            },
        )
    ):
        count = Envelope.filter().count()
    assert count == 1


def test_query_proxy_iterable():
    with mock_urlopen(
        make_response(
            200,
            {
                "data": [{"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}}],
                "links": {"next": None},
            },
        )
    ):
        ids = [e.id for e in Envelope.filter()]
    assert ids == ["1"]


def test_with_includes_validates_empty():
    with pytest.raises(ValueError):
        Envelope.with_includes()


def test_with_includes_validates_non_string():
    with pytest.raises(ValueError):
        Envelope.with_includes(123)  # type: ignore[arg-type]


def test_auto_pagination_stops_on_links_next_null():
    with mock_urlopen(
        make_response(
            200,
            {
                "data": [{"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}}],
                "links": {"next": None},
            },
        )
    ):
        items = Envelope.filter().to_list()
    assert len(items) == 1


def test_auto_pagination_multiple_pages():
    responses = [
        make_response(
            200,
            {
                "data": [
                    {"id": str(i), "type": "envelopes", "attributes": {}, "relationships": {}}
                    for i in range(20)
                ],
                "links": {"next": "http://next"},
            },
        ),
        make_response(
            200,
            {
                "data": [{"id": "99", "type": "envelopes", "attributes": {}, "relationships": {}}],
                "links": {"next": None},
            },
        ),
    ]
    with mock_urlopen(*responses):
        items = Envelope.filter().per(20).to_list()
    assert len(items) == 21


def test_auto_pagination_heuristic_fallback():
    with mock_urlopen(
        make_response(
            200,
            {
                "data": [
                    {"id": str(i), "type": "envelopes", "attributes": {}, "relationships": {}}
                    for i in range(5)
                ]
            },
        )
    ):
        items = Envelope.filter().per(20).to_list()
    assert len(items) == 5


def test_auto_pagination_heuristic_extra_request_when_exactly_full():
    """When links absent and page count == per, makes one extra request."""
    full_page = [
        {"id": str(i), "type": "envelopes", "attributes": {}, "relationships": {}} for i in range(5)
    ]
    with mock_urlopen(
        make_response(200, {"data": full_page}),
        make_response(200, {"data": []}),
    ):
        items = Envelope.filter().per(5).to_list()
    assert len(items) == 5


def test_auto_pagination_raises_on_api_error():
    from clicksign.errors import ServerError

    with mock_urlopen(
        make_response(
            200,
            {
                "data": [{"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}}],
                "links": {"next": "http://next"},
            },
        ),
        make_http_error(500, b""),
    ):
        with pytest.raises(ServerError):
            Envelope.filter().per(1).to_list()
