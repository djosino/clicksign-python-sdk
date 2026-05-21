from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from .bound_resource import BoundResource
from .client import Client
from .client_scope import client_scope
from .configuration import _ENVIRONMENTS, DEFAULT_MAX_RETRIES
from .http_transport import HTTPClient
from .instrumentation import Instrumentation
from .json_api.bulk_operations_client import BulkOperationsClient
from .raw_response import RawResponse
from .request_options import RequestOptions
from .resource import Resource
from .response_metadata import ResponseMetadata


class NotarialNamespace:
    def __init__(self, client: ClicksignClient) -> None:
        from .resources.notarial.bulk_requirement import BulkRequirement
        from .resources.notarial.document import Document
        from .resources.notarial.envelope import Envelope
        from .resources.notarial.event import Event
        from .resources.notarial.requirement import Requirement
        from .resources.notarial.signature_watcher import SignatureWatcher
        from .resources.notarial.signer import Signer

        self.envelopes = BoundResource(client, Envelope)
        self.documents = BoundResource(client, Document)
        self.signers = BoundResource(client, Signer)
        self.requirements = BoundResource(client, Requirement)
        self.bulk_requirements = BoundResource(client, BulkRequirement)
        self.signature_watchers = BoundResource(client, SignatureWatcher)
        self.events = BoundResource(client, Event)


class AutoSignatureNamespace:
    def __init__(self, client: ClicksignClient) -> None:
        from .resources.auto_signature.term import Term

        self.terms = BoundResource(client, Term)


class AcceptanceTermNamespace:
    def __init__(self, client: ClicksignClient) -> None:
        from .resources.acceptance_term.whatsapp import Whatsapp

        self.whatsapps = BoundResource(client, Whatsapp)


class ClicksignClient:
    """High-level entry point for the Clicksign API.

    Resource namespaces (``notarial.envelopes``, ``webhooks``, …) share this client's
    HTTP settings. Use :meth:`raw_request` and :meth:`deserialize` for unmapped endpoints.
    ``last_response`` reflects the most recent HTTP call on the main client; use
    :attr:`bulk_last_response` after bulk operations.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        environment: str | None = None,
        open_timeout: float = 2.0,
        read_timeout: float = 10.0,
        write_timeout: float = 10.0,
        max_retries: int = DEFAULT_MAX_RETRIES,
        logger: Any = None,
        instrumentation: Instrumentation | None = None,
        http_client: HTTPClient | None = None,
        proxy: str | None = None,
        verify_ssl_certs: bool = True,
        app_info: Any = None,
        enable_telemetry: bool | None = None,
        telemetry_url: str | None = None,
    ) -> None:
        if environment is not None:
            if environment not in _ENVIRONMENTS:
                raise ValueError(
                    f"Unknown environment: {environment!r}. Must be 'production' or 'sandbox'."
                )
            base_url = _ENVIRONMENTS[environment]

        if instrumentation is None:
            from clicksign import instrumentation as global_instrumentation

            resolved_instrumentation = global_instrumentation
        else:
            resolved_instrumentation = instrumentation

        self._instrumentation = resolved_instrumentation
        resolved_base_url = base_url or _ENVIRONMENTS["production"]

        from .provider_telemetry import ProviderTelemetry

        if enable_telemetry is None:
            from . import _config

            resolved_enable = _config.enable_telemetry
            resolved_telemetry_url = (
                telemetry_url if telemetry_url is not None else _config.telemetry_url
            )
        else:
            resolved_enable = enable_telemetry
            resolved_telemetry_url = telemetry_url
        provider_telemetry = ProviderTelemetry.from_base_url(
            resolved_base_url,
            enabled=resolved_enable,
            telemetry_url=resolved_telemetry_url,
        )

        self._client = Client(
            api_key=api_key,
            base_url=resolved_base_url,
            open_timeout=open_timeout,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            max_retries=max_retries,
            instrumentation=self._instrumentation,
            logger=logger,
            http_client=http_client,
            proxy=proxy,
            verify_ssl_certs=verify_ssl_certs,
            app_info=app_info,
            provider_telemetry=provider_telemetry,
        )
        self._bulk_client = BulkOperationsClient(
            api_key=api_key,
            base_url=resolved_base_url,
            open_timeout=open_timeout,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            max_retries=max_retries,
            instrumentation=self._instrumentation,
            logger=logger,
            http_client=http_client,
            proxy=proxy,
            verify_ssl_certs=verify_ssl_certs,
            app_info=app_info,
            provider_telemetry=provider_telemetry,
        )

        self.notarial = NotarialNamespace(self)
        self.auto_signature = AutoSignatureNamespace(self)
        self.acceptance_term = AcceptanceTermNamespace(self)

        from .resources.access_control_list import AccessControlList
        from .resources.envelope_bulk_creation import EnvelopeBulkCreation
        from .resources.event import Event
        from .resources.folder import Folder
        from .resources.group import Group
        from .resources.membership import Membership
        from .resources.template import Template
        from .resources.template_field import TemplateField
        from .resources.user import User
        from .resources.webhook import Webhook

        self.webhooks = BoundResource(self, Webhook)
        self.users = BoundResource(self, User)
        self.memberships = BoundResource(self, Membership)
        self.groups = BoundResource(self, Group)
        self.templates = BoundResource(self, Template)
        self.template_fields = BoundResource(self, TemplateField)
        self.folders = BoundResource(self, Folder)
        self.envelope_bulk_creations = BoundResource(self, EnvelopeBulkCreation)
        self.access_control_lists = BoundResource(self, AccessControlList)
        self.events = BoundResource(self, Event)

    @property
    def http(self) -> Client:
        """Low-level HTTP client (same as used by resource namespaces)."""
        return self._client

    @property
    def bulk(self) -> BulkOperationsClient:
        """Client for atomic bulk requirement operations."""
        return self._bulk_client

    @property
    def last_response(self) -> ResponseMetadata | None:
        """Metadata from the last HTTP call on the main client."""
        return self._client.last_response

    @property
    def bulk_last_response(self) -> ResponseMetadata | None:
        """Metadata from the last bulk HTTP call."""
        return self._bulk_client.last_response

    @property
    def envelopes(self) -> BoundResource:
        return self.notarial.envelopes

    def raw_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> RawResponse:
        """HTTP call to an arbitrary path (beta or unmapped endpoints)."""
        return self._client.raw_request(
            method,
            path,
            params=params,
            body=body,
            headers=headers,
            options=options,
        )

    @staticmethod
    def deserialize(
        response: RawResponse | dict[str, Any],
        resource_class: type[Resource],
    ) -> Resource | list[Resource]:
        """Parse a JSON:API body (or :class:`RawResponse`) into resource instance(s)."""
        return Client.deserialize(response, resource_class)

    @contextmanager
    def use(self) -> Generator[ClicksignClient, None, None]:
        with client_scope(self._client, self._bulk_client):
            yield self
