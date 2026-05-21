import pytest

from clicksign.errors import ValidationError
from clicksign.json_api.bulk_operations_client import BulkResponse
from clicksign.resources.notarial.bulk_requirement import BulkRequirement
from tests.support.http_mock import make_http_error, make_response, mock_urlopen

ENV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
SIG_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
DOC_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
REQ_ID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"

RESULTS_BODY = {
    "atomic:results": [
        {
            "op": "add",
            "data": {
                "id": REQ_ID,
                "type": "requirements",
                "attributes": {"action": "agree"},
                "relationships": {},
            },
        }
    ]
}


def test_create_returns_bulk_response():
    with mock_urlopen(make_response(200, RESULTS_BODY)):
        result = BulkRequirement.create(
            ENV_ID,
            block=lambda ops: ops.add_agree(signer_id=SIG_ID, document_id=DOC_ID, role="sign"),
        )
    assert isinstance(result, BulkResponse)
    assert result.success()


def test_create_without_block_raises():
    with pytest.raises(TypeError, match="block"):
        BulkRequirement.create(ENV_ID)


def test_block_can_add_multiple_operations():
    captured_payload: dict[str, object] = {}
    with mock_urlopen(make_response(200, RESULTS_BODY), capture=captured_payload):
        BulkRequirement.create(
            ENV_ID,
            block=lambda ops: (
                ops.add_agree(signer_id=SIG_ID, document_id=DOC_ID, role="sign"),
                ops.add_provide_evidence(signer_id=SIG_ID, document_id=DOC_ID, auth="email"),
            ),
        )

    ops = captured_payload["body"]["atomic:operations"]  # type: ignore[index]
    assert len(ops) == 2
    assert ops[0]["data"]["attributes"]["action"] == "agree"
    assert ops[1]["data"]["attributes"]["action"] == "provide_evidence"


def test_block_remove_operation():
    captured_payload: dict[str, object] = {}
    with mock_urlopen(make_response(200, {"atomic:results": []}), capture=captured_payload):
        BulkRequirement.create(ENV_ID, block=lambda ops: ops.remove(requirement_id=REQ_ID))

    ops = captured_payload["body"]["atomic:operations"]  # type: ignore[index]
    assert ops[0]["op"] == "remove"
    assert ops[0]["ref"]["id"] == REQ_ID


def test_create_top_level_errors_raises():
    with mock_urlopen(make_http_error(422, {"errors": [{"detail": "Envelope not in draft"}]})):
        with pytest.raises(ValidationError):
            BulkRequirement.create(
                ENV_ID,
                block=lambda ops: ops.add_agree(signer_id=SIG_ID, document_id=DOC_ID, role="sign"),
            )


def test_partial_failure_no_exception():
    body = {
        "atomic:results": [
            {"op": "add", "errors": [{"detail": "Signer not found"}]},
        ]
    }
    with mock_urlopen(make_response(200, body)):
        result = BulkRequirement.create(
            ENV_ID,
            block=lambda ops: ops.add_agree(signer_id=SIG_ID, document_id=DOC_ID, role="sign"),
        )
    assert not result.success()
    assert len(result.failures) == 1
