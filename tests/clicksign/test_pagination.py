import pytest

from clicksign.json_api.parser import ParsedResponse
from clicksign.pagination import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    has_next_page,
    merge_page_params,
    resolve_page_size,
)
from clicksign.resources.notarial.envelope import Envelope
from tests.support.http_mock import make_response, mock_urlopen


def test_resolve_page_size_default():
    assert resolve_page_size(None) == DEFAULT_PAGE_SIZE


def test_resolve_page_size_rejects_too_large():
    with pytest.raises(ValueError, match=str(MAX_PAGE_SIZE)):
        resolve_page_size(MAX_PAGE_SIZE + 1)


def test_merge_page_params():
    assert merge_page_params({"filter[status]": "draft"}, page=2, per=50) == {
        "filter[status]": "draft",
        "page[number]": "2",
        "page[size]": "50",
    }


def test_has_next_page_links_next_null():
    parsed = ParsedResponse(links={"next": None})
    assert has_next_page(parsed, 20, 20) is False


def test_has_next_page_links_next_url():
    parsed = ParsedResponse(links={"next": "https://api.example/page2"})
    assert has_next_page(parsed, 20, 20) is True


def test_has_next_page_heuristic_short_page():
    parsed = ParsedResponse(links={})
    assert has_next_page(parsed, 5, 20) is False


def test_has_next_page_heuristic_full_page():
    parsed = ParsedResponse(links={})
    assert has_next_page(parsed, 20, 20) is True


def test_query_proxy_last_response_each_page_during_iteration():
    responses = [
        make_response(
            200,
            {
                "data": [{"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}}],
                "links": {"next": "http://next"},
            },
            headers={"X-Request-Id": "page-1"},
        ),
        make_response(
            200,
            {
                "data": [{"id": "2", "type": "envelopes", "attributes": {}, "relationships": {}}],
                "links": {"next": None},
            },
            headers={"X-Request-Id": "page-2"},
        ),
    ]
    proxy = Envelope.filter()
    request_ids: list[str | None] = []
    with mock_urlopen(*responses):
        for _ in proxy:
            request_ids.append(proxy.last_response.request_id if proxy.last_response else None)
    assert request_ids == ["page-1", "page-2"]
    assert [m.request_id for m in proxy.page_responses] == ["page-1", "page-2"]


def test_query_proxy_on_page_callback():
    pages: list[tuple[int, int]] = []

    def capture(page: int, meta, items) -> None:
        pages.append((page, len(items)))

    with mock_urlopen(
        make_response(
            200,
            {
                "data": [{"id": "1", "type": "envelopes", "attributes": {}, "relationships": {}}],
                "links": {"next": None},
            },
        )
    ):
        Envelope.filter().on_page(capture).to_list()

    assert pages == [(1, 1)]
