import pytest

from clicksign.json_api.query_builder import QueryBuilder
from clicksign.pagination import MAX_PAGE_SIZE


def test_filter_key_value():
    qb = QueryBuilder().filter(status="running")
    assert qb.to_params() == {"filter[status]": "running"}


def test_filter_false_included():
    qb = QueryBuilder().filter(in_root=False)
    assert qb.to_params() == {"filter[in_root]": "false"}


def test_filter_true_included():
    qb = QueryBuilder().filter(active=True)
    assert qb.to_params()["filter[active]"] == "true"


def test_order_ascending():
    qb = QueryBuilder().order("name")
    assert qb.to_params() == {"sort": "name"}


def test_order_descending():
    qb = QueryBuilder().order("-created")
    assert qb.to_params() == {"sort": "-created"}


def test_page():
    qb = QueryBuilder().page(2)
    assert qb.to_params() == {"page[number]": "2"}


def test_per():
    qb = QueryBuilder().per(50)
    assert qb.to_params() == {"page[size]": "50"}


def test_per_rejects_above_max():
    with pytest.raises(ValueError, match=str(MAX_PAGE_SIZE)):
        QueryBuilder().per(MAX_PAGE_SIZE + 1)


def test_with_includes_single():
    qb = QueryBuilder().with_includes("folder")
    assert qb.to_params() == {"include": "folder"}


def test_with_includes_multiple():
    qb = QueryBuilder().with_includes("a", "b")
    assert qb.to_params() == {"include": "a,b"}


def test_fields():
    qb = QueryBuilder().fields(envelopes=["name", "status"])
    assert qb.to_params() == {"fields[envelopes]": "name,status"}


def test_all_methods_chainable():
    qb = (
        QueryBuilder()
        .filter(status="draft")
        .order("-created")
        .page(1)
        .per(20)
        .with_includes("folder")
        .fields(envelopes=["name"])
    )
    params = qb.to_params()
    assert "filter[status]" in params
    assert "sort" in params
    assert "page[number]" in params
    assert "page[size]" in params
    assert "include" in params
    assert "fields[envelopes]" in params


def test_with_includes_empty_raises():
    with pytest.raises(ValueError, match="at least one"):
        QueryBuilder().with_includes()


def test_with_includes_non_string_raises():
    with pytest.raises(ValueError, match="must be str"):
        QueryBuilder().with_includes(123)  # type: ignore[arg-type]
