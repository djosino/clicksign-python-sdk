import json

import pytest

from clicksign.client import Client
from clicksign.instrumentation import Instrumentation
from clicksign.raw_response import RawResponse
from clicksign.resources.notarial.envelope import Envelope
from tests.support.fake_http_client import FakeHTTPClient, http_error, http_response
from tests.support.json_api_fixtures import UUID, collection, envelope_response

BASE = "http://test.clicksign.com/api/v3"


def make_client(fake: FakeHTTPClient) -> Client:
    return Client(
        api_key="test-key",
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=fake,
    )


def test_raw_request_get_arbitrary_path():
    body = {"data": {"beta": True}}
    fake = FakeHTTPClient(http_response(200, body, headers={"X-Request-Id": "raw-1"}))
    client = make_client(fake)

    response = client.raw_request("get", "/beta/feature")

    assert isinstance(response, RawResponse)
    assert response.status == 200
    assert response.body == body
    assert response.request_id == "raw-1"
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["url"] == f"{BASE}/beta/feature"


def test_raw_request_post_with_body_and_extra_headers():
    fake = FakeHTTPClient(http_response(201, {"ok": True}))
    client = make_client(fake)

    response = client.raw_request(
        "post",
        "/beta/feature",
        body={"hello": "world"},
        headers={"X-Custom": "1"},
    )

    assert response.status == 201
    assert response.body == {"ok": True}
    sent = json.loads(fake.calls[0]["body"])
    assert sent == {"hello": "world"}
    assert fake.calls[0]["headers"]["X-Custom"] == "1"
    assert fake.calls[0]["headers"]["Authorization"] == "test-key"


def test_raw_request_respects_retry_and_raises_on_error():
    fake = FakeHTTPClient(http_error(404, {"errors": [{"detail": "missing"}]}))
    client = make_client(fake)

    from clicksign.errors import NotFoundError

    with pytest.raises(NotFoundError):
        client.raw_request("get", "/missing")


def test_deserialize_single_resource():
    fake = FakeHTTPClient(http_response(200, envelope_response(), headers={"X-Request-Id": "d1"}))
    client = make_client(fake)

    raw = client.raw_request("get", f"/envelopes/{UUID}")
    envelope = Client.deserialize(raw, Envelope)

    assert envelope.id == UUID
    assert envelope.last_response is not None
    assert envelope.last_response.request_id == "d1"


def test_deserialize_collection():
    fake = FakeHTTPClient(http_response(200, collection("envelopes")))
    client = make_client(fake)

    raw = client.raw_request("get", "/envelopes")
    items = Client.deserialize(raw, Envelope)

    assert isinstance(items, list)
    assert len(items) == 1


def test_deserialize_from_dict_body():
    envelope = Client.deserialize(envelope_response(), Envelope)
    assert envelope.id == UUID
    assert envelope.last_response is None


def test_raw_request_publishes_instrumentation():
    fake = FakeHTTPClient(http_response(200, {"ok": True}))
    inst = Instrumentation()
    events: list[dict[str, object]] = []
    inst.on_request(lambda payload: events.append(payload))

    client = Client(
        api_key="test-key",
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=inst,
        http_client=fake,
    )
    client.raw_request("get", "/beta/feature")

    assert events
    assert events[0]["path"] == "/beta/feature"
    assert events[0]["status"] == 200
