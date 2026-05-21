import asyncio

import pytest

from clicksign.async_bridge import AsyncClientSyncShim
from clicksign.async_client import AsyncClient
from clicksign.instrumentation import Instrumentation
from tests.support.fake_async_http_client import FakeAsyncHTTPClient
from tests.support.fake_http_client import http_response

BASE = "http://test.clicksign.com/api/v3"
KEY = "test-key"


def _async_client(fake: FakeAsyncHTTPClient) -> AsyncClient:
    return AsyncClient(
        api_key=KEY,
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=fake,
    )


def test_shim_get_when_loop_not_running():
    fake = FakeAsyncHTTPClient(http_response(200, {"data": []}))
    loop = asyncio.new_event_loop()
    try:
        shim = AsyncClientSyncShim(_async_client(fake), loop)
        result = shim.get("/envelopes")
        assert result == {"data": []}
        assert shim.last_response is not None
        assert shim.last_response.status == 200
    finally:
        loop.close()


@pytest.mark.asyncio
async def test_shim_get_when_loop_running():
    fake = FakeAsyncHTTPClient(http_response(200, {"data": [{"id": "1"}]}))
    loop = asyncio.get_running_loop()
    shim = AsyncClientSyncShim(_async_client(fake), loop)
    result = shim.get("/envelopes")
    assert result["data"][0]["id"] == "1"
