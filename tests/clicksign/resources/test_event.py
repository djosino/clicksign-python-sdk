from clicksign.resources.event import Event
from clicksign.resources.notarial.event import Event as NotarialEvent
from tests.support.http_mock import make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ENV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


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


def test_root_event_resource_type():
    assert Event.resource_type == "events"


def test_notarial_event_resource_type():
    assert NotarialEvent.resource_type == "events"


def test_list_events_via_envelope():
    from clicksign.resources.notarial.envelope import Envelope

    with mock_urlopen(make_response(200, {"data": [event_data()]})):
        events = Envelope.list_events(ENV_ID)

    assert len(events) == 1
    assert events[0].name == "envelope.activated"
