import threading
from typing import Any

import pytest

import clicksign
from clicksign.clicksign_client import ClicksignClient
from clicksign.json_api.bulk_operations_client import BulkResponse
from clicksign.raw_response import RawResponse
from clicksign.resources.notarial.envelope import Envelope
from tests.support.http_mock import make_response, mock_urlopen
from tests.support.json_api_fixtures import UUID, collection, envelope_response

BASE = "http://test.clicksign.com/api/v3"
ENV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
SIG_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
DOC_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"

BULK_BODY = {
    "atomic:results": [
        {
            "op": "add",
            "data": {
                "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
                "type": "requirements",
                "attributes": {"action": "agree"},
                "relationships": {},
            },
        }
    ]
}


@pytest.fixture
def client() -> ClicksignClient:
    return ClicksignClient(api_key="tenant-a", base_url=BASE)


def test_exported_from_package():
    assert clicksign.ClicksignClient is ClicksignClient


def test_list_envelopes(client: ClicksignClient):
    with mock_urlopen(make_response(200, collection("envelopes"))):
        items = client.notarial.envelopes.list()
    assert len(items) == 1
    assert items[0].id == UUID


def test_envelopes_alias(client: ClicksignClient):
    assert client.envelopes is client.notarial.envelopes


def test_filter_chain(client: ClicksignClient):
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, collection("envelopes")), capture=captured):
        item = (
            client.notarial.envelopes.filter(status="draft")
            .page(2)
            .per(10)
            .order("created_at")
            .first()
        )
    assert item is not None
    assert captured["url"].endswith("/envelopes") or "/envelopes?" in captured["url"]
    params = captured["url"].split("?", 1)[1]
    assert "filter%5Bstatus%5D=draft" in params or "filter[status]=draft" in params
    assert "page%5Bnumber%5D=2" in params or "page[number]=2" in params
    assert "page%5Bsize%5D=10" in params or "page[size]=10" in params
    assert "sort=created_at" in params


def test_retrieve_and_update(client: ClicksignClient):
    draft = envelope_response()
    draft["data"]["attributes"]["status"] = "draft"
    running = envelope_response()
    running["data"]["attributes"]["status"] = "running"
    with mock_urlopen(
        make_response(200, draft),
        make_response(200, running),
    ):
        envelope = client.notarial.envelopes.retrieve(UUID)
        envelope.update(status="running")
    assert envelope.status == "running"


def test_custom_classmethod(client: ClicksignClient):
    body = envelope_response()
    body["data"]["attributes"]["status"] = "running"
    with mock_urlopen(make_response(200, body)):
        envelope = client.notarial.envelopes.activate(UUID)
    assert envelope.status == "running"


def test_multi_instance_uses_own_api_key():
    client_a = ClicksignClient(api_key="key-a", base_url=BASE)
    client_b = ClicksignClient(api_key="key-b", base_url=BASE)
    captured_a: dict[str, Any] = {}
    captured_b: dict[str, Any] = {}

    with mock_urlopen(make_response(200, collection("envelopes")), capture=captured_a):
        client_a.notarial.envelopes.list()
    with mock_urlopen(make_response(200, collection("envelopes")), capture=captured_b):
        client_b.notarial.envelopes.list()

    assert captured_a["headers"]["Authorization"] == "key-a"
    assert captured_b["headers"]["Authorization"] == "key-b"


def test_use_sets_thread_local(client: ClicksignClient):
    with client.use():
        thread = threading.current_thread()
        assert thread.__dict__.get("_clicksign_client") is client.http
        assert thread.__dict__.get("_clicksign_bulk_client") is client.bulk


def test_use_restores_thread_local(client: ClicksignClient):
    with client.use():
        pass
    thread = threading.current_thread()
    assert thread.__dict__.get("_clicksign_client") is None
    assert thread.__dict__.get("_clicksign_bulk_client") is None


def test_bulk_requirement_via_client(client: ClicksignClient):
    with mock_urlopen(make_response(200, BULK_BODY)):
        result = client.notarial.bulk_requirements.create(
            ENV_ID,
            block=lambda ops: ops.add_agree(signer_id=SIG_ID, document_id=DOC_ID, role="sign"),
        )
    assert isinstance(result, BulkResponse)
    assert result.success()


def test_unknown_environment_raises():
    with pytest.raises(ValueError, match="Unknown environment"):
        ClicksignClient(api_key="key", environment="staging")


def test_last_response_after_resource_call(client: ClicksignClient):
    headers = {"X-Request-Id": "facade-1"}
    with mock_urlopen(make_response(200, collection("envelopes"), headers=headers)):
        client.notarial.envelopes.list()
    assert client.last_response is not None
    assert client.last_response.status == 200
    assert client.last_response.request_id == "facade-1"


def test_bulk_last_response_after_bulk_call(client: ClicksignClient):
    with mock_urlopen(make_response(200, BULK_BODY, headers={"X-Request-Id": "bulk-1"})):
        client.notarial.bulk_requirements.create(
            ENV_ID,
            block=lambda ops: ops.add_agree(signer_id=SIG_ID, document_id=DOC_ID, role="sign"),
        )
    assert client.bulk_last_response is not None
    assert client.bulk_last_response.request_id == "bulk-1"


def test_raw_request_on_facade(client: ClicksignClient):
    headers = {"X-Request-Id": "raw-f"}
    with mock_urlopen(make_response(200, {"data": {"beta": True}}, headers=headers)):
        response = client.raw_request("get", "/beta/feature")
    assert isinstance(response, RawResponse)
    assert response.status == 200
    assert response.body == {"data": {"beta": True}}
    assert client.last_response is not None
    assert client.last_response.request_id == "raw-f"


def test_deserialize_on_facade(client: ClicksignClient):
    with mock_urlopen(make_response(200, envelope_response())):
        raw = client.raw_request("get", f"/envelopes/{UUID}")
        envelope = client.deserialize(raw, Envelope)
    assert envelope.id == UUID
    assert envelope.last_response is not None
