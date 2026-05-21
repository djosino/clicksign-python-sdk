from clicksign.resources.notarial.envelope import Envelope
from clicksign.types._attrs import bool_attr, dict_attr, int_attr, list_str_attr, str_attr

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _envelope(**attrs: object) -> Envelope:
    return Envelope(
        {
            "id": UUID,
            "type": "envelopes",
            "attributes": attrs,
            "relationships": {},
        }
    )


def test_str_attr_returns_string():
    assert str_attr(_envelope(name="X"), "name") == "X"


def test_str_attr_rejects_non_string():
    assert str_attr(_envelope(name=123), "name") is None


def test_bool_attr():
    assert bool_attr(_envelope(auto_close=True), "auto_close") is True
    assert bool_attr(_envelope(auto_close="yes"), "auto_close") is None


def test_int_attr():
    assert int_attr(_envelope(remind_interval=7), "remind_interval") == 7
    assert int_attr(_envelope(remind_interval=True), "remind_interval") is None


def test_list_str_attr():
    assert list_str_attr(_envelope(tags=["a", "b"]), "tags") == ["a", "b"]
    assert list_str_attr(_envelope(tags=["a", 2]), "tags") == ["a"]


def test_dict_attr():
    assert dict_attr(_envelope(meta={"k": "v"}), "meta") == {"k": "v"}
    assert dict_attr(_envelope(meta="x"), "meta") is None
