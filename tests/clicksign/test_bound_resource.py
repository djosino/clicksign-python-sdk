from typing import Any

import pytest

from clicksign.clicksign_client import ClicksignClient
from tests.support.http_mock import make_response, mock_urlopen
from tests.support.json_api_fixtures import UUID, UUID2, collection

BASE = "http://test.clicksign.com/api/v3"


@pytest.fixture
def client() -> ClicksignClient:
    return ClicksignClient(api_key="key", base_url=BASE)


def test_bound_query_proxy_with_includes_and_fields(client: ClicksignClient):
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, collection("envelopes")), capture=captured):
        client.envelopes.with_includes("folder").fields(envelopes=["name"]).to_list()
    url = captured["url"]
    assert "include=folder" in url
    assert "fields%5Benvelopes%5D" in url or "fields[envelopes]" in url


def test_bound_query_proxy_count(client: ClicksignClient):
    body = collection("envelopes", items=[{"id": UUID}, {"id": UUID2}])
    with mock_urlopen(make_response(200, body)):
        count = client.envelopes.filter(status="draft").count()
    assert count == 2


def test_bound_query_proxy_last(client: ClicksignClient):
    items = [
        {"id": "11111111-1111-1111-1111-111111111111", "attributes": {"name": "A"}},
        {"id": UUID, "attributes": {"name": "B"}},
    ]
    with mock_urlopen(make_response(200, collection("envelopes", items=items))):
        last = client.envelopes.filter(status="draft").last()
    assert last is not None
    assert last.id == UUID


def test_bound_query_proxy_iteration(client: ClicksignClient):
    with mock_urlopen(make_response(200, collection("envelopes"))):
        ids = [e.id for e in client.envelopes.filter(status="draft")]
    assert len(ids) == 1


def test_bound_resource_order_entry_point(client: ClicksignClient):
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, collection("envelopes")), capture=captured):
        client.envelopes.order("-created_at").first()
    assert "sort=-created_at" in captured["url"] or "sort%3D-created_at" in captured["url"]


def test_bound_resource_page_per_entry_points(client: ClicksignClient):
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, collection("envelopes")), capture=captured):
        client.envelopes.page(3).per(25).first()
    params = captured["url"].split("?", 1)[1]
    assert "page%5Bnumber%5D=3" in params or "page[number]=3" in params
    assert "page%5Bsize%5D=25" in params or "page[size]=25" in params


def test_bound_classmethod_activate(client: ClicksignClient):
    from tests.support.json_api_fixtures import envelope_response

    body = envelope_response()
    body["data"]["attributes"]["status"] = "running"
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, body), capture=captured):
        client.notarial.envelopes.activate(UUID)
    assert captured["method"] == "POST"
    assert captured["url"].endswith(f"/envelopes/{UUID}/activate")


def test_bound_on_page_callback(client: ClicksignClient):
    pages: list[int] = []

    def on_page(page: int, _meta: object, _items: object) -> None:
        pages.append(page)

    body = collection("envelopes")
    body["links"] = {"next": None}
    with mock_urlopen(make_response(200, body)):
        client.envelopes.filter(status="draft").on_page(on_page).to_list()
    assert pages == [1]
