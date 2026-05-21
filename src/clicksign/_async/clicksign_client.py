from __future__ import annotations

from typing import Any

from .._http.transport import AsyncHTTPClient
from ..configuration import _ENVIRONMENTS, DEFAULT_MAX_RETRIES
from ..instrumentation import Instrumentation
from ..raw_response import RawResponse
from ..request_options import RequestOptions
from ..resource import Resource
from ..response_metadata import ResponseMetadata
from .bound_resource import AsyncBoundResource
from .client import AsyncClient


class AsyncNotarialNamespace:
    def __init__(self, client: AsyncClicksignClient) -> None:
        from ..resources.notarial.bulk_requirement import BulkRequirement
        from ..resources.notarial.document import Document
        from ..resources.notarial.envelope import Envelope
        from ..resources.notarial.requirement import Requirement
        from ..resources.notarial.signature_watcher import SignatureWatcher
        from ..resources.notarial.signer import Signer

        self.envelopes = AsyncBoundResource(client, Envelope)
        self.documents = AsyncBoundResource(client, Document)
        self.signers = AsyncBoundResource(client, Signer)
        self.requirements = AsyncBoundResource(client, Requirement)
        self.bulk_requirements = AsyncBoundResource(client, BulkRequirement)
        self.signature_watchers = AsyncBoundResource(client, SignatureWatcher)


class AsyncAutoSignatureNamespace:
    def __init__(self, client: AsyncClicksignClient) -> None:
        from ..resources.auto_signature.term import Term

        self.terms = AsyncBoundResource(client, Term)


class AsyncAcceptanceTermNamespace:
    def __init__(self, client: AsyncClicksignClient) -> None:
        from ..resources.acceptance_term.whatsapp import Whatsapp

        self.whatsapps = AsyncBoundResource(client, Whatsapp)


class AsyncClicksignClient:
    """Async entry point for the Clicksign API.

    Requires ``httpx`` (``pip install clicksign-python-sdk[async]``). The API itself is unchanged;
    this client runs concurrent HTTP I/O on the event loop.

    ``Services.use()`` is thread-local and is **not** compatible with asyncio — pass an
    explicit ``AsyncClicksignClient`` per application or coroutine scope instead.
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
        http_client: AsyncHTTPClient | None = None,
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

        resolved_base_url = base_url or _ENVIRONMENTS["production"]

        from ..provider_telemetry import ProviderTelemetry

        if enable_telemetry is None:
            from .. import _config

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

        self._client = AsyncClient(
            api_key=api_key,
            base_url=resolved_base_url,
            open_timeout=open_timeout,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            max_retries=max_retries,
            instrumentation=resolved_instrumentation,
            logger=logger,
            http_client=http_client,
            proxy=proxy,
            verify_ssl_certs=verify_ssl_certs,
            app_info=app_info,
            provider_telemetry=provider_telemetry,
        )

        self.notarial = AsyncNotarialNamespace(self)
        self.auto_signature = AsyncAutoSignatureNamespace(self)
        self.acceptance_term = AsyncAcceptanceTermNamespace(self)

        from ..resources.access_control_list import AccessControlList
        from ..resources.envelope_bulk_creation import EnvelopeBulkCreation
        from ..resources.folder import Folder
        from ..resources.group import Group
        from ..resources.membership import Membership
        from ..resources.template import Template
        from ..resources.template_field import TemplateField
        from ..resources.user import User
        from ..resources.webhook import Webhook

        self.webhooks = AsyncBoundResource(self, Webhook)
        self.users = AsyncBoundResource(self, User)
        self.memberships = AsyncBoundResource(self, Membership)
        self.groups = AsyncBoundResource(self, Group)
        self.templates = AsyncBoundResource(self, Template)
        self.template_fields = AsyncBoundResource(self, TemplateField)
        self.folders = AsyncBoundResource(self, Folder)
        self.envelope_bulk_creations = AsyncBoundResource(self, EnvelopeBulkCreation)
        self.access_control_lists = AsyncBoundResource(self, AccessControlList)

    @property
    def http(self) -> AsyncClient:
        return self._client

    @property
    def last_response(self) -> ResponseMetadata | None:
        return self._client.last_response

    @property
    def envelopes(self) -> AsyncBoundResource:
        return self.notarial.envelopes

    async def raw_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> RawResponse:
        return await self._client.raw_request(
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
        return AsyncClient.deserialize(response, resource_class)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncClicksignClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
