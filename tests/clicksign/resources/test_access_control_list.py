import pytest

from clicksign.errors import ValidationError
from clicksign.resources.access_control_list import AccessControlList
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
FOLDER_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
GROUP_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"


def acl_data(id=UUID, **attrs):
    return {"id": id, "type": "access_control_lists", "attributes": {**attrs}, "relationships": {}}


def test_resource_type():
    assert AccessControlList.resource_type == "access_control_lists"


def test_endpoint():
    assert AccessControlList.endpoint == "/access_control_lists"


def test_create():
    with mock_urlopen(make_response(201, {"data": acl_data()})):
        result = AccessControlList.create(folder_id=FOLDER_ID, group_id=GROUP_ID)
    assert result.id == UUID


def test_create_sends_relationships():
    captured: dict[str, object] = {}
    with mock_urlopen(make_response(201, {"data": acl_data()}), capture=captured):
        AccessControlList.create(folder_id=FOLDER_ID, group_id=GROUP_ID)

    rels = captured["body"]["data"]["relationships"]  # type: ignore[index]
    assert rels["folder"]["data"]["id"] == FOLDER_ID
    assert rels["group"]["data"]["id"] == GROUP_ID


def test_destroy():
    with mock_urlopen(make_response(204, None)):
        AccessControlList.destroy(folder_id=FOLDER_ID, group_id=GROUP_ID)


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Not authorized"}]})):
        with pytest.raises(ValidationError):
            AccessControlList.create(folder_id=FOLDER_ID, group_id=GROUP_ID)
