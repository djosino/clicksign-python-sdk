import pytest

from clicksign.errors import NotFoundError, ValidationError
from clicksign.resources.group import Group
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def group_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "groups",
        "attributes": {"name": "Admins", **attrs},
        "relationships": {},
    }


def test_resource_type():
    assert Group.resource_type == "groups"


def test_endpoint():
    assert Group.endpoint == "/groups"


def test_list():
    with mock_urlopen(make_response(200, {"data": [group_data()]})):
        items = Group.list()
    assert len(items) == 1
    assert items[0].name == "Admins"


def test_retrieve():
    with mock_urlopen(make_response(200, {"data": group_data()})):
        g = Group.retrieve(UUID)
    assert g.id == UUID


def test_create():
    with mock_urlopen(make_response(201, {"data": group_data()})):
        g = Group.create(name="Admins")
    assert g.name == "Admins"


def test_update():
    g = Group({"id": UUID, "type": "groups", "attributes": {"name": "Old"}, "relationships": {}})
    with mock_urlopen(make_response(200, {"data": group_data(name="New")})):
        g.update(name="New")
    assert g.name == "New"


def test_delete():
    g = Group({"id": UUID, "type": "groups", "attributes": {}, "relationships": {}})
    with mock_urlopen(make_response(204, None)):
        g.delete()


def test_filter():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        Group.filter(name="Admins").to_list()


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Name blank"}]})):
        with pytest.raises(ValidationError):
            Group.create(name="")


def test_retrieve_404():
    with mock_urlopen(make_http_error(404, {"errors": [{"detail": "Not found"}]})):
        with pytest.raises(NotFoundError):
            Group.retrieve(UUID)
