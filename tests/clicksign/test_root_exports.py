import clicksign


def test_root_exports_notarial_resources():
    assert clicksign.Envelope is not None
    assert clicksign.Document is not None
    assert clicksign.Signer is not None
    assert clicksign.Requirement is not None
    assert clicksign.BulkRequirement is not None
    assert clicksign.SignatureWatcher is not None


def test_root_exports_admin_resources():
    assert clicksign.Webhook is not None
    assert clicksign.Folder is not None


def test_envelope_resource_type():
    assert clicksign.Envelope.resource_type == "envelopes"
