import json
from unittest.mock import patch

import pytest

from clicksign._http.transport import UrllibHTTPClient
from clicksign.errors import AuthenticationError, ServerError, TimeoutError, ValidationError
from clicksign.instrumentation import Instrumentation
from clicksign.json_api.bulk_operations_client import (
    BulkOperationsClient,
    BulkResponse,
)
from tests.support.fake_http_client import (
    FakeHTTPClient,
    connection_error,
    http_error,
    http_response,
)

BASE = "http://test.clicksign.com/api/v3"
KEY = "test-key"


def make_client(
    max_retries: int = 0,
    inst: Instrumentation | None = None,
    http_client: FakeHTTPClient | None = None,
) -> BulkOperationsClient:
    return BulkOperationsClient(
        api_key=KEY,
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=5.0,
        max_retries=max_retries,
        instrumentation=inst or Instrumentation(),
        http_client=http_client or FakeHTTPClient(),
    )


PAYLOAD = {
    "atomic:operations": [
        {"op": "add", "data": {"type": "requirements", "attributes": {}, "relationships": {}}}
    ]
}
RESULTS_BODY = {
    "atomic:results": [
        {
            "op": "add",
            "data": {
                "id": "r1",
                "type": "requirements",
                "attributes": {"action": "agree"},
                "relationships": {},
            },
        }
    ]
}


def test_sends_correct_headers():
    fake = FakeHTTPClient(http_response(200, RESULTS_BODY))
    make_client(http_client=fake).post("/envelopes/e1/bulk_requirements", PAYLOAD)
    assert fake.calls[0]["headers"]["Authorization"] == KEY
    assert fake.calls[0]["headers"]["Content-Type"] == "application/vnd.api+json"
    assert fake.calls[0]["headers"]["Accept"] == "application/vnd.api+json"


def test_post_body_is_json():
    fake = FakeHTTPClient(http_response(200, RESULTS_BODY))
    make_client(http_client=fake).post("/envelopes/e1/bulk_requirements", PAYLOAD)
    body = json.loads(fake.calls[0]["body"])
    assert "atomic:operations" in body


def test_returns_bulk_response_when_atomic_results_present():
    fake = FakeHTTPClient(http_response(200, RESULTS_BODY))
    result = make_client(http_client=fake).post("/envelopes/e1/bulk_requirements", PAYLOAD)
    assert isinstance(result, BulkResponse)
    assert result.success()


def test_top_level_errors_raises_exception():
    fake = FakeHTTPClient(http_error(422, {"errors": [{"detail": "Envelope not in draft"}]}))
    with pytest.raises(ValidationError, match="Envelope not in draft"):
        make_client(http_client=fake).post("/envelopes/e1/bulk_requirements", PAYLOAD)


def test_422_raises_validation_error():
    fake = FakeHTTPClient(http_error(422, {"errors": [{"detail": "bad"}]}))
    with pytest.raises(ValidationError):
        make_client(http_client=fake).post("/envelopes/e1/bulk_requirements", PAYLOAD)


def test_500_raises_server_error():
    fake = FakeHTTPClient(http_error(500, ""))
    with pytest.raises(ServerError):
        make_client(http_client=fake).post("/envelopes/e1/bulk_requirements", PAYLOAD)


def test_401_raises_authentication_error():
    fake = FakeHTTPClient(http_error(401, ""))
    with pytest.raises(AuthenticationError):
        make_client(http_client=fake).post("/envelopes/e1/bulk_requirements", PAYLOAD)


def test_invalid_json_body_does_not_raise_decode_error():
    fake = FakeHTTPClient(http_response(200, "not json"))
    result = make_client(http_client=fake).post("/envelopes/e1/bulk_requirements", PAYLOAD)
    assert isinstance(result, BulkResponse)


def test_retries_on_timeout_succeeds():
    fake = FakeHTTPClient(connection_error("timeout"), http_response(200, RESULTS_BODY))
    with patch("clicksign.retry_backoff.delay", return_value=0):
        result = make_client(max_retries=1, http_client=fake).post(
            "/envelopes/e1/bulk_requirements", PAYLOAD
        )
    assert result.success()


def test_does_not_retry_on_server_error():
    fake = FakeHTTPClient(http_error(500, ""))
    with pytest.raises(ServerError):
        client = make_client(max_retries=2, http_client=fake)
        client.post("/envelopes/e1/bulk_requirements", PAYLOAD)
    assert len(fake.calls) == 1


def test_raises_after_exhausting_max_retries():
    fake = FakeHTTPClient(
        connection_error("t1"),
        connection_error("t2"),
        connection_error("t3"),
    )
    with patch("clicksign.retry_backoff.delay", return_value=0):
        with pytest.raises(TimeoutError):
            make_client(max_retries=2, http_client=fake).post(
                "/envelopes/e1/bulk_requirements", PAYLOAD
            )


def test_slot_with_errors_is_failure():
    body = {
        "atomic:results": [
            {"op": "add", "errors": [{"detail": "Signer not found"}]},
        ]
    }
    fake = FakeHTTPClient(http_response(200, body))
    result = make_client(http_client=fake).post("/envelopes/e1/bulk_requirements", PAYLOAD)
    assert not result.success()
    assert len(result.failures) == 1
    assert result.failures[0].errors[0]["detail"] == "Signer not found"


def test_publishes_request_event():
    events: list = []
    inst = Instrumentation()
    inst.on_request(lambda e: events.append(e))
    fake = FakeHTTPClient(http_response(200, RESULTS_BODY))
    make_client(inst=inst, http_client=fake).post("/envelopes/e1/bulk_requirements", PAYLOAD)
    assert len(events) == 1
    assert events[0]["method"] == "post"


def test_publishes_error_event():
    error_events: list = []
    inst = Instrumentation()
    inst.on_error(lambda e: error_events.append(e))
    fake = FakeHTTPClient(http_error(500, ""))
    with pytest.raises(ServerError):
        make_client(inst=inst, http_client=fake).post("/envelopes/e1/bulk_requirements", PAYLOAD)
    assert len(error_events) == 1


def test_uses_injected_http_client():
    fake = FakeHTTPClient(http_response(200, RESULTS_BODY))
    client = make_client(http_client=fake)
    assert client.http_client is fake


def test_default_http_client_is_urllib():
    client = BulkOperationsClient(
        api_key=KEY,
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=5.0,
        max_retries=0,
        instrumentation=Instrumentation(),
    )
    assert isinstance(client.http_client, UrllibHTTPClient)
