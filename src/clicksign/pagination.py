from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .json_api.parser import ParsedResponse

# Clicksign JSON:API examples use page[size]=50; default collection page is often 25.
# The SDK default matches historical behavior (20) when per() is not set.
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50
DOCUMENTED_API_DEFAULT_PAGE_SIZE = 25


def resolve_page_size(per: int | None) -> int:
    if per is None:
        return DEFAULT_PAGE_SIZE
    if per < 1:
        raise ValueError(f"page size must be >= 1, got {per}")
    if per > MAX_PAGE_SIZE:
        raise ValueError(
            f"page size must be <= {MAX_PAGE_SIZE} (Clicksign API limit documented in pagination guide), "
            f"got {per}"
        )
    return per


def merge_page_params(
    base_params: dict[str, str],
    *,
    page: int,
    per: int,
) -> dict[str, str]:
    return {**base_params, "page[number]": str(page), "page[size]": str(per)}


def has_next_page(parsed: ParsedResponse, item_count: int, per: int) -> bool:
    """Whether auto-pagination should request another page.

    When ``links.next`` is present in the response, it takes priority: a null or empty
    ``next`` means the last page (no extra request even if the page is full).

    When ``links`` omits ``next``, stop when ``item_count < per`` (legacy heuristic).
    A full page without ``links.next`` triggers one more request (may return empty).
    """
    if "next" in parsed.links:
        next_link = parsed.links.get("next")
        if next_link is None:
            return False
        if isinstance(next_link, str) and not next_link.strip():
            return False
        return True
    return item_count >= per
