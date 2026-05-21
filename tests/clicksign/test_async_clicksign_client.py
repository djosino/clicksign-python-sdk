import pytest

from clicksign.async_clicksign_client import AsyncClicksignClient
from clicksign.resources.notarial.envelope import Envelope
from tests.support.fake_async_http_client import FakeAsyncHTTPClient
from tests.support.fake_http_client import http_response
from tests.support.json_api_fixtures import UUID, collection, envelope_response

BASE = "http://test.clicksign.com/api/v3"


@pytest.fixture
def fake() -> FakeAsyncHTTPClient:
    return FakeAsyncHTTPClient()


@pytest.fixture
def client(fake: FakeAsyncHTTPClient) -> AsyncClicksignClient:
    return AsyncClicksignClient(
        api_key="test-key",
        base_url=BASE,
        max_retries=0,
        http_client=fake,
    )


@pytest.mark.asyncio
async def test_list_envelopes(client: AsyncClicksignClient, fake: FakeAsyncHTTPClient):
    fake._queue = [http_response(200, collection("envelopes"))]
    items = await client.notarial.envelopes.list()
    assert len(items) == 1
    assert items[0].id == UUID


@pytest.mark.asyncio
async def test_filter_async_iteration(client: AsyncClicksignClient, fake: FakeAsyncHTTPClient):
    body = collection("envelopes")
    body["data"].append(
        {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "type": "envelopes",
            "attributes": {"name": "Second"},
            "relationships": {},
        }
    )
    body["links"] = {"next": None}
    fake._queue = [http_response(200, body)]
    collected = []
    async for item in client.notarial.envelopes.filter(status="draft").per(10):
        collected.append(item)
    assert len(collected) == 2
    url = fake.calls[0]["url"]
    assert "filter%5Bstatus%5D=draft" in url or "filter[status]=draft" in url


@pytest.mark.asyncio
async def test_update_async(client: AsyncClicksignClient, fake: FakeAsyncHTTPClient):
    draft = envelope_response()
    draft["data"]["attributes"]["status"] = "draft"
    running = envelope_response()
    running["data"]["attributes"]["status"] = "running"
    fake._queue = [http_response(200, draft), http_response(200, running)]
    envelope = await client.notarial.envelopes.retrieve(UUID)
    await envelope.update_async(status="running")
    assert envelope.status == "running"


@pytest.mark.asyncio
async def test_activate_classmethod(client: AsyncClicksignClient, fake: FakeAsyncHTTPClient):
    body = envelope_response()
    body["data"]["attributes"]["status"] = "running"
    fake._queue = [http_response(200, body)]
    envelope = await client.notarial.envelopes.activate(UUID)
    assert envelope.status == "running"
    assert fake.calls[0]["method"] == "POST"
    assert "/activate" in fake.calls[0]["url"]


@pytest.mark.asyncio
async def test_raw_request_and_deserialize(client: AsyncClicksignClient, fake: FakeAsyncHTTPClient):
    fake._queue = [http_response(200, envelope_response())]
    raw = await client.raw_request("GET", f"/envelopes/{UUID}")
    envelope = client.deserialize(raw, Envelope)
    assert envelope.id == UUID


@pytest.mark.asyncio
async def test_last_response(client: AsyncClicksignClient, fake: FakeAsyncHTTPClient):
    fake._queue = [http_response(200, collection("envelopes"))]
    await client.notarial.envelopes.list()
    assert client.last_response is not None
    assert client.last_response.status == 200
