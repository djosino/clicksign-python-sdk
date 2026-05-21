from clicksign.client import Client
from clicksign.instrumentation import Instrumentation
from clicksign.resources.notarial.envelope import Envelope
from clicksign.response_metadata import ResponseMetadata
from tests.support.fake_http_client import FakeHTTPClient, http_response
from tests.support.http_mock import make_response, mock_urlopen
from tests.support.json_api_fixtures import UUID, collection, envelope_response

BASE = "http://test.clicksign.com/api/v3"
HEADERS = {
    "X-Request-Id": "req-abc123",
    "X-RateLimit-Remaining": "42",
    "X-RateLimit-Reset": "1710000000",
}

ENVELOPE_STUB = {
    "id": UUID,
    "type": "envelopes",
    "attributes": {},
    "relationships": {},
}


def test_client_last_response_after_get():
    fake = FakeHTTPClient(http_response(200, {"data": []}, headers=HEADERS))
    client = Client(
        api_key="key",
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=fake,
    )
    client.get("/envelopes")

    assert client.last_response is not None
    assert isinstance(client.last_response, ResponseMetadata)
    assert client.last_response.status == 200
    assert client.last_response.request_id == "req-abc123"
    assert client.last_response.rate_limit_remaining == "42"
    assert client.last_response.rate_limit_reset == "1710000000"
    assert client.last_response.duration_ms >= 0


def test_retrieve_populates_resource_last_response():
    with mock_urlopen(make_response(200, envelope_response(), headers=HEADERS)):
        envelope = Envelope.retrieve(UUID)

    assert envelope.last_response is not None
    assert envelope.last_response.status == 200
    assert envelope.last_response.request_id == "req-abc123"


def test_list_populates_last_response_on_all_items():
    with mock_urlopen(make_response(200, collection("envelopes"), headers=HEADERS)):
        items = Envelope.list()

    assert len(items) == 1
    assert items[0].last_response is not None
    assert items[0].last_response.request_id == "req-abc123"


def test_query_proxy_last_response():
    with mock_urlopen(make_response(200, collection("envelopes"), headers=HEADERS)):
        proxy = Envelope.filter(status="draft")
        items = proxy.to_list()

    assert len(items) == 1
    assert proxy.last_response is not None
    assert proxy.last_response.request_id == "req-abc123"
    assert items[0].last_response is not None


def test_update_populates_last_response():
    headers = {"X-Request-Id": "req-updated"}
    with mock_urlopen(make_response(200, envelope_response(), headers=headers)):
        envelope = Envelope(ENVELOPE_STUB)
        envelope.update(name="Updated")

    assert envelope.last_response is not None
    assert envelope.last_response.request_id == "req-updated"


def test_delete_populates_last_response():
    with mock_urlopen(make_response(204, None, headers=HEADERS)):
        envelope = Envelope(ENVELOPE_STUB)
        envelope.delete()

    assert envelope.last_response is not None
    assert envelope.last_response.status == 204
