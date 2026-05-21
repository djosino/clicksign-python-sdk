import pytest

from clicksign.errors import ValidationError
from clicksign.resources.envelope_bulk_creation import EnvelopeBulkCreation
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def ebc_data(id=UUID, **attrs):
    return {
        "id": id,
        "type": "envelope_bulk_creations",
        "attributes": {"job_id": "job-1", "enqueued_at": "2026-01-01T00:00:00Z", **attrs},
        "relationships": {},
    }


def test_resource_type():
    assert EnvelopeBulkCreation.resource_type == "envelope_bulk_creations"


def test_endpoint():
    assert EnvelopeBulkCreation.endpoint == "/envelope_bulk_creations"


def test_create():
    with mock_urlopen(make_response(201, {"data": ebc_data()})):
        result = EnvelopeBulkCreation.create(template_id="t1")
    assert result.id == UUID
    assert result.job_id == "job-1"


def test_create_422():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Template not found"}]})):
        with pytest.raises(ValidationError):
            EnvelopeBulkCreation.create(template_id="bad")


def test_list_raises():
    with pytest.raises(NotImplementedError):
        EnvelopeBulkCreation.list()


def test_retrieve_raises():
    with pytest.raises(NotImplementedError):
        EnvelopeBulkCreation.retrieve(UUID)
