import pytest

from clicksign.errors import ValidationError
from clicksign.resources.membership import Membership
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
USER_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def mem_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "memberships",
        "attributes": {"role": "admin", **attrs},
        "relationships": {"user": {"data": {"type": "users", "id": USER_ID}}},
    }


def test_resource_type():
    assert Membership.resource_type == "memberships"


def test_endpoint():
    assert Membership.endpoint == "/memberships"


def test_list():
    with mock_urlopen(make_response(200, {"data": [mem_data()]})):
        items = Membership.list()
    assert len(items) == 1


def test_create():
    with mock_urlopen(make_response(201, {"data": mem_data()})):
        m = Membership.create(role="admin")
    assert m.id == UUID


def test_update():
    m = Membership(
        {"id": UUID, "type": "memberships", "attributes": {"role": "member"}, "relationships": {}}
    )
    with mock_urlopen(make_response(200, {"data": mem_data(role="admin")})):
        m.update(role="admin")
    assert m.role == "admin"


def test_delete():
    m = Membership({"id": UUID, "type": "memberships", "attributes": {}, "relationships": {}})
    with mock_urlopen(make_response(204, None)):
        m.delete()


def test_filter():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        Membership.filter(**{"user.id": USER_ID}).to_list()


def test_filter_for_user():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        Membership.filter_for_user(USER_ID, role="admin").to_list()


def test_user_id_from_relationships():
    m = Membership(mem_data())
    assert m.user_id == USER_ID


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Role invalid"}]})):
        with pytest.raises(ValidationError):
            Membership.create(role="god")
