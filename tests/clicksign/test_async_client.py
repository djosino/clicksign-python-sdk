import json

import pytest

from clicksign._async.client import AsyncClient
from clicksign.instrumentation import Instrumentation
from tests.support.fake_async_http_client import FakeAsyncHTTPClient
from tests.support.fake_http_client import http_response

BASE = "http://test.clicksign.com/api/v3"
KEY = "test-key"


def make_client(
    max_retries: int = 0,
    http_client: FakeAsyncHTTPClient | None = None,
) -> AsyncClient:
    return AsyncClient(
        api_key=KEY,
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=max_retries,
        instrumentation=Instrumentation(),
        http_client=http_client or FakeAsyncHTTPClient(),
    )


@pytest.mark.asyncio
async def test_get_sends_correct_headers():
    fake = FakeAsyncHTTPClient(http_response(200, {"data": []}))
    await make_client(http_client=fake).get("/envelopes")
    assert fake.calls[0]["headers"]["Authorization"] == KEY


@pytest.mark.asyncio
async def test_post_sends_body_as_json():
    body = {"data": {"id": "1", "type": "e", "attributes": {}, "relationships": {}}}
    fake = FakeAsyncHTTPClient(http_response(201, body))
    await make_client(http_client=fake).post(
        "/envelopes", {"data": {"type": "envelopes", "attributes": {"name": "X"}}}
    )
    body = json.loads(fake.calls[0]["body"])
    assert body["data"]["attributes"]["name"] == "X"


@pytest.mark.asyncio
async def test_raw_request_returns_raw_response():
    fake = FakeAsyncHTTPClient(http_response(200, {"data": {"id": "1", "type": "envelopes"}}))
    client = make_client(http_client=fake)
    raw = await client.raw_request("GET", "/envelopes/1")
    assert raw.status == 200
    assert raw.body["data"]["id"] == "1"
    assert client.last_response is not None
    assert client.last_response.status == 200


@pytest.mark.asyncio
async def test_retries_on_timeout():
    fake = FakeAsyncHTTPClient(
        TimeoutError("timed out"),
        http_response(200, {"data": []}),
    )
    client = make_client(max_retries=1, http_client=fake)
    await client.get("/envelopes")
    assert len(fake.calls) == 2


@pytest.mark.asyncio
async def test_aclose_calls_http_client():
    fake = FakeAsyncHTTPClient(http_response(200, {"data": []}))
    client = make_client(http_client=fake)
    await client.aclose()
    async with make_client(http_client=FakeAsyncHTTPClient()) as ctx:
        assert ctx is not None
