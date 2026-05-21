import pytest

from clicksign.errors import NotFoundError
from clicksign.resources.user import User
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def user_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "users",
        "attributes": {"name": "Alice", "email": "alice@example.com", **attrs},
        "relationships": {},
    }


def test_resource_type():
    assert User.resource_type == "users"


def test_endpoint():
    assert User.endpoint == "/users"


def test_list():
    with mock_urlopen(make_response(200, {"data": [user_data()]})):
        items = User.list()
    assert len(items) == 1
    assert items[0].name == "Alice"


def test_retrieve():
    with mock_urlopen(make_response(200, {"data": user_data()})):
        u = User.retrieve(UUID)
    assert u.id == UUID


def test_create():
    with mock_urlopen(make_response(201, {"data": user_data()})):
        u = User.create(name="Alice", email="alice@example.com")
    assert u.id == UUID


def test_me():
    with mock_urlopen(make_response(200, {"data": user_data()})):
        u = User.me()
    assert u.id == UUID


def test_filter():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        User.filter(email="alice@example.com").to_list()


def test_retrieve_404():
    with mock_urlopen(make_http_error(404, {"errors": [{"detail": "Not found"}]})):
        with pytest.raises(NotFoundError):
            User.retrieve(UUID)
