import json

import pytest

from clicksign.api_error import ApiError, parse_api_error_objects, parse_api_errors
from clicksign.error_handler import handle
from clicksign.errors import ValidationError


def test_parse_api_errors_multiple_entries():
    body = {
        "errors": [
            {
                "detail": "Name is blank",
                "code": "blank",
                "source": {"pointer": "/data/attributes/name"},
            },
            {
                "detail": "Email is invalid",
                "code": "invalid",
                "source": {"pointer": "/data/attributes/email"},
            },
        ]
    }
    parsed = parse_api_errors(json.dumps(body))
    assert len(parsed) == 2
    assert parsed[0]["detail"] == "Name is blank"
    assert parsed[1]["code"] == "invalid"


def test_parse_api_error_objects():
    body = {
        "errors": [
            {
                "detail": "Name is blank",
                "code": "blank",
                "source": {"pointer": "/data/attributes/name", "parameter": "name"},
            }
        ]
    }
    errors = parse_api_error_objects(json.dumps(body))
    assert len(errors) == 1
    assert isinstance(errors[0], ApiError)
    assert errors[0].pointer == "/data/attributes/name"
    assert errors[0].parameter == "name"


def test_validation_error_exposes_all_errors():
    body = {
        "errors": [
            {
                "detail": "Name is blank",
                "code": "blank",
                "source": {"pointer": "/data/attributes/name"},
            },
            {
                "detail": "Email is invalid",
                "code": "invalid",
                "source": {"pointer": "/data/attributes/email"},
            },
        ]
    }
    with pytest.raises(ValidationError, match="Name is blank") as excinfo:
        handle(422, json.dumps(body), {})

    err = excinfo.value
    assert len(err.errors) == 2
    assert err.message == "Name is blank"
    assert err.error_code == "blank"
    assert err.source_pointer == "/data/attributes/name"
    assert err.api_errors[1].pointer == "/data/attributes/email"


def test_validation_error_without_structured_errors():
    with pytest.raises(ValidationError, match="HTTP 422") as excinfo:
        handle(422, "", {})

    err = excinfo.value
    assert err.errors == []
    assert err.error_code is None
    assert err.source_pointer is None


def test_form_field_mapping_from_api_errors():
    body = {
        "errors": [
            {
                "detail": "Name is blank",
                "source": {"pointer": "/data/attributes/name"},
            },
            {
                "detail": "Email is invalid",
                "source": {"pointer": "/data/attributes/email"},
            },
        ]
    }
    try:
        handle(422, json.dumps(body), {})
    except ValidationError as err:
        field_errors = {
            (api_error.parameter or api_error.pointer or "base"): api_error.detail
            for api_error in err.api_errors
        }

    assert field_errors["/data/attributes/name"] == "Name is blank"
    assert field_errors["/data/attributes/email"] == "Email is invalid"
