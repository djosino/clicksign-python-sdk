from typing import Any

import pytest

from clicksign import ClicksignClient, RequestOptions
from clicksign._http.headers import CORRELATION_ID_HEADER, correlation_id
from clicksign.client import Client
from clicksign.instrumentation import Instrumentation
from clicksign.request_options import (
    merge_headers,
    normalize_options,
    resolve_max_retries,
    resolve_timeouts,
)
from clicksign.resources.notarial.envelope import Envelope
from tests.support.fake_http_client import FakeHTTPClient, http_response
from tests.support.http_mock import make_response, mock_urlopen
from tests.support.json_api_fixtures import UUID, collection, envelope_response

BASE = "http://test.clicksign.com/api/v3"


def test_correlation_id_helper():
    assert correlation_id("req-1") == {CORRELATION_ID_HEADER: "req-1"}
    with pytest.raises(ValueError):
        correlation_id("")


def test_correlation_id_merged_in_request():
    fake = FakeHTTPClient(http_response(200, envelope_response()))
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
    client.get(
        f"/envelopes/{UUID}",
        options=RequestOptions(headers=correlation_id("trace-abc")),
    )
    assert fake.calls[0]["headers"][CORRELATION_ID_HEADER] == "trace-abc"


def test_request_options_dataclass():
    opts = RequestOptions(api_key="override", headers={"X-Trace": "1"})
    assert opts.api_key == "override"
    assert opts.headers == {"X-Trace": "1"}


def test_normalize_options_accepts_dict():
    opts = normalize_options({"api_key": "k", "read_timeout": 30.0})
    assert opts is not None
    assert opts.api_key == "k"
    assert opts.read_timeout == 30.0


def test_merge_headers_overrides_authorization():
    base = {"Authorization": "default", "Accept": "application/json"}
    merged = merge_headers(base, RequestOptions(api_key="override", headers={"X-Trace": "abc"}))
    assert merged["Authorization"] == "override"
    assert merged["Accept"] == "application/json"
    assert merged["X-Trace"] == "abc"


def test_resolve_max_retries_partial_override():
    assert resolve_max_retries(3, None) == 3
    assert resolve_max_retries(3, RequestOptions(max_retries=0)) == 0
    assert resolve_max_retries(0, RequestOptions(max_retries=2)) == 2


def test_resolve_max_retries_negative_raises():
    with pytest.raises(ValueError, match="max_retries must be >= 0"):
        resolve_max_retries(3, RequestOptions(max_retries=-1))


def test_resolve_timeouts_partial_override():
    open_t, read_t, write_t = resolve_timeouts(2.0, 10.0, 10.0, RequestOptions(read_timeout=30.0))
    assert open_t == 2.0
    assert read_t == 30.0
    assert write_t == 10.0


def test_client_get_with_api_key_override():
    fake = FakeHTTPClient(http_response(200, {"data": []}))
    client = Client(
        api_key="default-key",
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=fake,
    )
    client.get("/envelopes", options={"api_key": "tenant-key"})
    assert fake.calls[0]["headers"]["Authorization"] == "tenant-key"


def test_client_get_with_max_retries_override():
    from clicksign.errors import ServerError
    from tests.support.fake_http_client import http_error

    fake = FakeHTTPClient(http_error(503, '{"errors":[{"detail":"busy"}]}'))
    client = Client(
        api_key="default-key",
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=3,
        instrumentation=Instrumentation(),
        http_client=fake,
    )
    with pytest.raises(ServerError, match="busy"):
        client.get("/envelopes", options={"max_retries": 0})
    assert len(fake.calls) == 1


def test_client_get_with_extra_headers_and_timeout():
    fake = FakeHTTPClient(http_response(200, {"data": []}))
    client = Client(
        api_key="default-key",
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=fake,
    )
    client.get(
        "/envelopes",
        options=RequestOptions(headers={"X-Correlation-Id": "req-1"}, read_timeout=99.0),
    )
    assert fake.calls[0]["headers"]["X-Correlation-Id"] == "req-1"
    assert fake.calls[0]["read_timeout"] == 99.0


def test_two_api_keys_same_process_via_resource_options():
    captured_a: dict[str, Any] = {}
    captured_b: dict[str, Any] = {}
    with mock_urlopen(make_response(200, envelope_response()), capture=captured_a):
        Envelope.retrieve(UUID, options={"api_key": "key-a"})
    with mock_urlopen(make_response(200, envelope_response()), capture=captured_b):
        Envelope.retrieve(UUID, options={"api_key": "key-b"})

    assert captured_a["headers"]["Authorization"] == "key-a"
    assert captured_b["headers"]["Authorization"] == "key-b"


def test_query_proxy_to_list_with_options():
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, collection("envelopes")), capture=captured):
        Envelope.filter(status="draft").to_list(options={"api_key": "proxy-key"})

    assert captured["headers"]["Authorization"] == "proxy-key"


def test_clicksign_client_retrieve_with_options():
    client = ClicksignClient(api_key="default-key", base_url=BASE)
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(200, envelope_response()), capture=captured):
        client.notarial.envelopes.retrieve(UUID, options={"api_key": "tenant-key"})

    assert captured["headers"]["Authorization"] == "tenant-key"


def test_create_with_options():
    captured: dict[str, Any] = {}
    with mock_urlopen(make_response(201, envelope_response()), capture=captured):
        Envelope.create(name="Test", options={"headers": {"X-Request-Id": "create-1"}})

    assert captured["headers"]["X-Request-Id"] == "create-1"


def test_invalid_options_dict_raises():
    with pytest.raises(TypeError):
        normalize_options({"unknown_field": "x"})  # type: ignore[arg-type]
