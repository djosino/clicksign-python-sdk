from clicksign.json_api.operations import BulkRequirementOperations

SIG_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
DOC_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
REQ_ID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"


def test_to_payload_empty():
    ops = BulkRequirementOperations()
    assert ops.to_payload() == {"atomic:operations": []}


def test_add_agree():
    ops = BulkRequirementOperations()
    ops.add_agree(signer_id=SIG_ID, document_id=DOC_ID, role="sign")
    payload = ops.to_payload()
    assert len(payload["atomic:operations"]) == 1
    op = payload["atomic:operations"][0]
    assert op["op"] == "add"
    assert op["data"]["attributes"] == {"action": "agree", "role": "sign"}
    assert op["data"]["relationships"]["signer"]["data"]["id"] == SIG_ID
    assert op["data"]["relationships"]["document"]["data"]["id"] == DOC_ID


def test_add_provide_evidence():
    ops = BulkRequirementOperations()
    ops.add_provide_evidence(signer_id=SIG_ID, document_id=DOC_ID, auth="email")
    op = ops.to_payload()["atomic:operations"][0]
    assert op["data"]["attributes"] == {"action": "provide_evidence", "auth": "email"}


def test_add_rubricate_minimal():
    ops = BulkRequirementOperations()
    ops.add_rubricate(signer_id=SIG_ID, document_id=DOC_ID)
    attrs = ops.to_payload()["atomic:operations"][0]["data"]["attributes"]
    assert attrs == {"action": "rubricate"}


def test_add_rubricate_with_optional_attrs():
    ops = BulkRequirementOperations()
    ops.add_rubricate(
        signer_id=SIG_ID,
        document_id=DOC_ID,
        pages="1-3",
        rubric_field="signature",
        kind="initial",
    )
    attrs = ops.to_payload()["atomic:operations"][0]["data"]["attributes"]
    assert attrs == {
        "action": "rubricate",
        "pages": "1-3",
        "rubric_field": "signature",
        "kind": "initial",
    }


def test_remove():
    ops = BulkRequirementOperations()
    ops.remove(requirement_id=REQ_ID)
    op = ops.to_payload()["atomic:operations"][0]
    assert op == {"op": "remove", "ref": {"type": "requirements", "id": REQ_ID}}


def test_multiple_operations_order():
    ops = BulkRequirementOperations()
    ops.add_agree(signer_id=SIG_ID, document_id=DOC_ID, role="sign")
    ops.add_provide_evidence(signer_id=SIG_ID, document_id=DOC_ID, auth="email")
    ops.remove(requirement_id=REQ_ID)
    names = [o["op"] for o in ops.to_payload()["atomic:operations"]]
    assert names == ["add", "add", "remove"]
