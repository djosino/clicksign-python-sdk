from clicksign.json_api.included import IncludedIndex
from clicksign.resources.folder import Folder
from clicksign.resources.notarial.envelope import Envelope
from tests.support.http_mock import make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
FOLDER_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff"


def envelope_with_folder_response():
    return {
        "data": [
            {
                "id": UUID,
                "type": "envelopes",
                "attributes": {"name": "Contract"},
                "relationships": {
                    "folder": {"data": {"type": "folders", "id": FOLDER_ID}},
                },
            }
        ],
        "included": [
            {
                "id": FOLDER_ID,
                "type": "folders",
                "attributes": {"name": "Legal"},
                "relationships": {},
            }
        ],
    }


def test_included_index_lookup():
    index = IncludedIndex.from_included(
        [{"id": FOLDER_ID, "type": "folders", "attributes": {"name": "Legal"}, "relationships": {}}]
    )
    item = index.get("folders", FOLDER_ID)
    assert item is not None
    assert item["attributes"]["name"] == "Legal"


def test_retrieve_resolves_included_folder():
    with mock_urlopen(make_response(200, envelope_with_folder_response())):
        envelope = Envelope.retrieve(UUID)

    folder = envelope.folder
    assert isinstance(folder, Folder)
    assert folder.id == FOLDER_ID
    assert folder.name == "Legal"


def test_list_with_includes_resolves_folder():
    captured: dict[str, object] = {}
    with mock_urlopen(
        make_response(200, envelope_with_folder_response()),
        capture=captured,  # type: ignore[arg-type]
    ):
        items = Envelope.with_includes("folder").to_list()

    url = str(captured.get("url", ""))
    assert "include=folder" in url or "include%3Dfolder" in url
    assert len(items) == 1
    assert items[0].folder.name == "Legal"


def test_included_resources_lists_all_sideloaded():
    with mock_urlopen(make_response(200, envelope_with_folder_response())):
        envelope = Envelope.retrieve(UUID)

    included = envelope.included_resources
    assert len(included) == 1
    assert included[0].id == FOLDER_ID


def test_missing_included_returns_none_for_relationship():
    body = {
        "data": {
            "id": UUID,
            "type": "envelopes",
            "attributes": {"name": "Contract"},
            "relationships": {
                "folder": {"data": {"type": "folders", "id": FOLDER_ID}},
            },
        },
        "included": [],
    }
    with mock_urlopen(make_response(200, body)):
        envelope = Envelope.retrieve(UUID)

    assert envelope.folder is None


def test_to_many_relationship_resolves_list():
    body = {
        "data": {
            "id": UUID,
            "type": "envelopes",
            "attributes": {"name": "Contract"},
            "relationships": {
                "documents": {
                    "data": [
                        {"type": "documents", "id": "doc-1"},
                        {"type": "documents", "id": "doc-2"},
                    ]
                }
            },
        },
        "included": [
            {
                "id": "doc-1",
                "type": "documents",
                "attributes": {"filename": "a.pdf"},
                "relationships": {},
            },
            {
                "id": "doc-2",
                "type": "documents",
                "attributes": {"filename": "b.pdf"},
                "relationships": {},
            },
        ],
    }
    with mock_urlopen(make_response(200, body)):
        envelope = Envelope.retrieve(UUID)

    documents = envelope.documents
    assert len(documents) == 2
    assert documents[0].filename == "a.pdf"
    assert documents[1].filename == "b.pdf"


def test_unknown_included_type_falls_back_to_resource():
    body = {
        "data": {
            "id": UUID,
            "type": "envelopes",
            "attributes": {"name": "Contract"},
            "relationships": {
                "custom": {"data": {"type": "beta_things", "id": "beta-1"}},
            },
        },
        "included": [
            {
                "id": "beta-1",
                "type": "beta_things",
                "attributes": {"label": "Beta"},
                "relationships": {},
            }
        ],
    }
    with mock_urlopen(make_response(200, body)):
        envelope = Envelope.retrieve(UUID)

    beta = envelope.custom
    assert beta is not None
    assert beta["label"] == "Beta"
