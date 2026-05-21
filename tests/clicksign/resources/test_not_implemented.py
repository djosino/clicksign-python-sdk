"""Verify NotImplementedError is raised for unsupported routes per resource."""

import pytest

from clicksign.resources.acceptance_term.whatsapp import Whatsapp
from clicksign.resources.auto_signature.term import Term
from clicksign.resources.envelope_bulk_creation import EnvelopeBulkCreation
from clicksign.resources.folder import Folder
from clicksign.resources.notarial.signature_watcher import SignatureWatcher
from clicksign.resources.notarial.signer import Signer
from clicksign.resources.template_field import TemplateField
from clicksign.resources.user import User

UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _inst(cls):
    return cls({"id": UUID, "type": "x", "attributes": {}, "relationships": {}})


# ── Signer: no update ─────────────────────────────────────────────────────


def test_signer_update_raises():
    with pytest.raises(NotImplementedError):
        _inst(Signer).update(name="X")


# ── SignatureWatcher: no update ───────────────────────────────────────────


def test_signature_watcher_update_raises():
    with pytest.raises(NotImplementedError):
        _inst(SignatureWatcher).update(email="x@x.com")


# ── Folder: no update, no delete ─────────────────────────────────────────


def test_folder_update_raises():
    with pytest.raises(NotImplementedError):
        _inst(Folder).update(name="X")


def test_folder_delete_raises():
    with pytest.raises(NotImplementedError):
        _inst(Folder).delete()


# ── User: no update, no delete ───────────────────────────────────────────


def test_user_update_raises():
    with pytest.raises(NotImplementedError):
        _inst(User).update(name="X")


def test_user_delete_raises():
    with pytest.raises(NotImplementedError):
        _inst(User).delete()


# ── TemplateField: only list ─────────────────────────────────────────────


def test_template_field_retrieve_raises():
    with pytest.raises(NotImplementedError):
        TemplateField.retrieve(UUID)


def test_template_field_create_raises():
    with pytest.raises(NotImplementedError):
        TemplateField.create(name="X")


def test_template_field_update_raises():
    with pytest.raises(NotImplementedError):
        _inst(TemplateField).update(name="X")


def test_template_field_delete_raises():
    with pytest.raises(NotImplementedError):
        _inst(TemplateField).delete()


# ── EnvelopeBulkCreation: only create ───────────────────────────────────


def test_envelope_bulk_creation_list_raises():
    with pytest.raises(NotImplementedError):
        EnvelopeBulkCreation.list()


def test_envelope_bulk_creation_retrieve_raises():
    with pytest.raises(NotImplementedError):
        EnvelopeBulkCreation.retrieve(UUID)


def test_envelope_bulk_creation_update_raises():
    with pytest.raises(NotImplementedError):
        _inst(EnvelopeBulkCreation).update(name="X")


def test_envelope_bulk_creation_delete_raises():
    with pytest.raises(NotImplementedError):
        _inst(EnvelopeBulkCreation).delete()


# ── AutoSignature::Term: only create ────────────────────────────────────


def test_term_list_raises():
    with pytest.raises(NotImplementedError):
        Term.list()


def test_term_retrieve_raises():
    with pytest.raises(NotImplementedError):
        Term.retrieve(UUID)


def test_term_update_raises():
    with pytest.raises(NotImplementedError):
        _inst(Term).update(name="X")


def test_term_delete_raises():
    with pytest.raises(NotImplementedError):
        _inst(Term).delete()


# ── AcceptanceTerm::Whatsapp: no delete ─────────────────────────────────


def test_whatsapp_delete_raises():
    with pytest.raises(NotImplementedError):
        _inst(Whatsapp).delete()
