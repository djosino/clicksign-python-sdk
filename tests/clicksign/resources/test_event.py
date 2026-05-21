from clicksign.resources.notarial.document import Document
from clicksign.resources.notarial.envelope import Envelope
from clicksign.resources.notarial.event import Event
from tests.support.http_mock import make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ENV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
DOC_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"


def event_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "events",
        "attributes": {
            "name": "envelope.activated",
            "data": {},
            "created": "2026-01-01T00:00:00Z",
            **attrs,
        },
        "relationships": {},
    }


def test_notarial_event_resource_type():
    assert Event.resource_type == "events"


def test_list_events_via_envelope():
    with mock_urlopen(make_response(200, {"data": [event_data()]})):
        events = Envelope.list_events(ENV_ID)

    assert len(events) == 1
    assert events[0].name == "envelope.activated"


def test_list_events_via_envelope_with_filter():
    captured: dict[str, object] = {}
    with mock_urlopen(make_response(200, {"data": []}), capture=captured):
        Envelope.list_events(ENV_ID, name="sign")

    assert f"/envelopes/{ENV_ID}/events" in captured["url"]
    assert "filter[name]=sign" in captured["url"] or "filter%5Bname%5D=sign" in captured["url"]


def test_list_events_via_document():
    with mock_urlopen(make_response(200, {"data": [event_data(name="read")]})):
        events = Document.list_events(DOC_ID, envelope_id=ENV_ID)

    assert len(events) == 1
    assert events[0].name == "read"


def test_create_for_document():
    captured: dict[str, object] = {}
    with mock_urlopen(make_response(201, {"data": event_data(name="read")}), capture=captured):
        event = Event.create_for_document(ENV_ID, DOC_ID, name="read")

    assert event.name == "read"
    assert captured["method"] == "POST"
    assert captured["url"].endswith(f"/envelopes/{ENV_ID}/documents/{DOC_ID}/events")
    assert captured["body"]["data"]["attributes"]["name"] == "read"
