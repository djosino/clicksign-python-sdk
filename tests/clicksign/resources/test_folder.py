import pytest

from clicksign.errors import NotFoundError, ValidationError
from clicksign.resources.folder import Folder
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
PARENT_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def folder_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "folders",
        "attributes": {"name": "Contracts", "path": "/Contracts", "in_root": True, **attrs},
        "relationships": {},
    }


def test_resource_type():
    assert Folder.resource_type == "folders"


def test_endpoint():
    assert Folder.endpoint == "/folders"


def test_list():
    with mock_urlopen(make_response(200, {"data": [folder_data()]})):
        items = Folder.list()
    assert len(items) == 1
    assert items[0].name == "Contracts"


def test_retrieve():
    with mock_urlopen(make_response(200, {"data": folder_data()})):
        f = Folder.retrieve(UUID)
    assert f.id == UUID


def test_create():
    with mock_urlopen(make_response(201, {"data": folder_data()})):
        f = Folder.create(name="Contracts")
    assert f.name == "Contracts"


def test_filter_in_root():
    with mock_urlopen(make_response(200, {"data": [], "links": {}})):
        Folder.filter(in_root=True).to_list()


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Name blank"}]})):
        with pytest.raises(ValidationError):
            Folder.create(name="")


def test_retrieve_404():
    with mock_urlopen(make_http_error(404, {"errors": [{"detail": "Not found"}]})):
        with pytest.raises(NotFoundError):
            Folder.retrieve(UUID)


def test_parent_folder_id():
    data = folder_data()
    data["relationships"] = {"folder": {"data": {"type": "folders", "id": PARENT_ID}}}
    f = Folder(data)
    assert f.parent_folder_id == PARENT_ID
