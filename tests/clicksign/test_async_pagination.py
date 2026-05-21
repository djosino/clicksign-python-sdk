import pytest

from clicksign._async.clicksign_client import AsyncClicksignClient
from tests.support.fake_async_http_client import FakeAsyncHTTPClient
from tests.support.fake_http_client import http_response
from tests.support.json_api_fixtures import UUID, UUID2

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
async def test_async_pagination_tracks_page_responses(
    client: AsyncClicksignClient, fake: FakeAsyncHTTPClient
):
    page1 = {
        "data": [{"id": UUID, "type": "envelopes", "attributes": {}, "relationships": {}}],
        "links": {"next": "http://next"},
    }
    page2 = {
        "data": [{"id": UUID2, "type": "envelopes", "attributes": {}, "relationships": {}}],
        "links": {"next": None},
    }
    fake._queue = [
        http_response(200, page1, headers={"X-Request-Id": "async-p1"}),
        http_response(200, page2, headers={"X-Request-Id": "async-p2"}),
    ]
    proxy = client.notarial.envelopes.filter().per(1)
    ids: list[str] = []
    async for envelope in proxy:
        ids.append(envelope.id)
        assert proxy.last_response is not None
        assert proxy.last_response.request_id in ("async-p1", "async-p2")
    assert ids == [UUID, UUID2]
    assert [m.request_id for m in proxy.page_responses] == ["async-p1", "async-p2"]


@pytest.mark.asyncio
async def test_delete_and_reload_async(client: AsyncClicksignClient, fake: FakeAsyncHTTPClient):
    from tests.support.json_api_fixtures import envelope_response

    env_body = envelope_response()
    env_body["data"]["attributes"]["name"] = "Reloaded"
    fake._queue = [
        http_response(200, envelope_response()),
        http_response(200, env_body),
        http_response(204, None),
    ]
    envelope = await client.notarial.envelopes.retrieve(UUID)
    await envelope.reload_async()
    assert envelope.name == "Reloaded"
    await envelope.delete_async()
    assert len(fake.calls) == 3
    assert fake.calls[-1]["method"] == "DELETE"
