from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..resource import Resource

_REGISTRY: dict[str, type[Resource]] | None = None


def get_resource_class(resource_type: str) -> type[Resource]:
    from ..resource import Resource

    return _load_registry().get(resource_type, Resource)


def _load_registry() -> dict[str, type[Resource]]:
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY

    from ..resources.acceptance_term.whatsapp import Whatsapp
    from ..resources.access_control_list import AccessControlList
    from ..resources.auto_signature.term import Term
    from ..resources.envelope_bulk_creation import EnvelopeBulkCreation
    from ..resources.event import Event
    from ..resources.folder import Folder
    from ..resources.group import Group
    from ..resources.membership import Membership
    from ..resources.notarial.document import Document
    from ..resources.notarial.envelope import Envelope
    from ..resources.notarial.event import Event as NotarialEvent
    from ..resources.notarial.requirement import Requirement
    from ..resources.notarial.signature_watcher import SignatureWatcher
    from ..resources.notarial.signer import Signer
    from ..resources.template import Template
    from ..resources.template_field import TemplateField
    from ..resources.user import User
    from ..resources.webhook import Webhook

    classes: list[type[Resource]] = [
        Folder,
        Envelope,
        Document,
        Signer,
        Requirement,
        SignatureWatcher,
        Event,
        NotarialEvent,
        Webhook,
        User,
        Membership,
        Group,
        Template,
        TemplateField,
        EnvelopeBulkCreation,
        AccessControlList,
        Whatsapp,
        Term,
    ]

    registry: dict[str, type[Resource]] = {}
    for cls in classes:
        if cls.resource_type:
            registry[cls.resource_type] = cls
    _REGISTRY = registry
    return _REGISTRY
