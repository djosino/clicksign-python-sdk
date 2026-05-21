import pytest

from clicksign._async.clicksign_client import AsyncClicksignClient
from tests.support.fake_async_http_client import FakeAsyncHTTPClient
from tests.support.fake_http_client import http_response
from tests.support.json_api_fixtures import UUID, UUID2, collection

BASE = "http://test.clicksign.com/api/v3"


@pytest.fixture
def fake() -> FakeAsyncHTTPClient:
    return FakeAsyncHTTPClient()


@pytest.fixture
def client(fake: FakeAsyncHTTPClient) -> AsyncClicksignClient:
    return AsyncClicksignClient(api_key="key", base_url=BASE, max_retries=0, http_client=fake)


@pytest.mark.asyncio
async def test_async_bound_filter_chain_first(
    client: AsyncClicksignClient, fake: FakeAsyncHTTPClient
):
    fake._queue = [http_response(200, collection("envelopes"))]
    item = await (
        client.notarial.envelopes.filter(status="draft")
        .page(2)
        .per(15)
        .order("name")
        .first()
    )
    assert item is not None
    url = fake.calls[0]["url"]
    assert "filter%5Bstatus%5D=draft" in url or "filter[status]=draft" in url
    assert "page%5Bnumber%5D=2" in url or "page[number]=2" in url
    assert "sort=name" in url


@pytest.mark.asyncio
async def test_async_bound_with_includes_fields_first(
    client: AsyncClicksignClient, fake: FakeAsyncHTTPClient
):
    fake._queue = [http_response(200, collection("envelopes"))]
    item = await client.envelopes.with_includes("folder").fields(envelopes=["name"]).first()
    assert item is not None
    url = fake.calls[0]["url"]
    assert "include=folder" in url


@pytest.mark.asyncio
async def test_async_bound_count(client: AsyncClicksignClient, fake: FakeAsyncHTTPClient):
    body = collection("envelopes", items=[{"id": UUID}, {"id": UUID2}])
    fake._queue = [http_response(200, body)]
    count = await client.envelopes.filter(status="draft").count()
    assert count == 2


@pytest.mark.asyncio
async def test_async_bound_page_per_entry_points(
    client: AsyncClicksignClient, fake: FakeAsyncHTTPClient
):
    fake._queue = [http_response(200, collection("envelopes"))]
    await client.envelopes.page(1).per(5).to_list()
    url = fake.calls[0]["url"]
    assert "page%5Bsize%5D=5" in url or "page[size]=5" in url


@pytest.mark.asyncio
async def test_async_bound_last_and_page_responses(
    client: AsyncClicksignClient, fake: FakeAsyncHTTPClient
):
    fake._queue = [http_response(200, collection("envelopes"))]
    proxy = client.envelopes.filter(status="draft")
    last = await proxy.last()
    assert last is not None
    assert proxy.page_responses
