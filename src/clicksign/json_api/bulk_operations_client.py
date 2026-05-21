from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..http_executor import execute_http_request
from ..http_transport import HTTPClient, default_http_client
from ..instrumentation import Instrumentation
from ..request_headers import default_request_headers
from ..request_instrumentation import RequestInstrumentation
from ..request_options import (
    RequestOptions,
    merge_headers,
    normalize_options,
    resolve_max_retries,
    resolve_timeouts,
)
from ..response_metadata import ResponseMetadata

if TYPE_CHECKING:
    from ..app_info import AppInfo
    from ..provider_telemetry import ProviderTelemetry


@dataclass
class AtomicResult:
    index: int
    op: str
    data: dict[str, Any] | None
    errors: list[Any]
    raw: dict[str, Any]

    @property
    def success(self) -> bool:
        return not bool(self.errors)


class BulkResponse:
    def __init__(self, results: list[AtomicResult]) -> None:
        self._results = results

    def success(self) -> bool:
        return all(r.success for r in self._results)

    @property
    def requirements(self) -> list[Any]:
        from ..resources.notarial.requirement import Requirement

        result = []
        for r in self._results:
            if r.success and r.data:
                inst = Requirement.__new__(Requirement)
                inst._data = {
                    "id": r.data.get("id"),
                    "type": r.data.get("type"),
                    "attributes": r.data.get("attributes") or {},
                    "relationships": r.data.get("relationships") or {},
                }
                result.append(inst)
        return result

    @property
    def failures(self) -> list[AtomicResult]:
        return [r for r in self._results if not r.success]


def _parse_bulk_response(body_text: str) -> BulkResponse:
    try:
        body = json.loads(body_text)
    except (json.JSONDecodeError, ValueError):
        return BulkResponse([])

    results_data = body.get("atomic:results") or []
    results = []
    for i, slot in enumerate(results_data):
        results.append(
            AtomicResult(
                index=i,
                op=slot.get("op", ""),
                data=slot.get("data"),
                errors=slot.get("errors") or [],
                raw=slot,
            )
        )
    return BulkResponse(results)


class BulkOperationsClient(RequestInstrumentation):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        open_timeout: float,
        read_timeout: float,
        write_timeout: float,
        max_retries: int,
        instrumentation: Instrumentation,
        logger: Any = None,
        *,
        http_client: HTTPClient | None = None,
        proxy: str | None = None,
        verify_ssl_certs: bool = True,
        app_info: AppInfo | None = None,
        enable_telemetry: bool | None = None,
        telemetry_url: str | None = None,
        provider_telemetry: ProviderTelemetry | None = None,
    ) -> None:
        if http_client is not None and (proxy is not None or verify_ssl_certs is not True):
            raise ValueError(
                "Cannot specify proxy or verify_ssl_certs when passing a custom http_client. "
                "Configure these on the http_client instead."
            )

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._open_timeout = open_timeout
        self._read_timeout = read_timeout
        self._write_timeout = write_timeout
        self._max_retries = max_retries
        self._instrumentation = instrumentation
        self._logger = logger
        self._app_info = app_info
        self._http_client = http_client or default_http_client(
            proxy=proxy,
            verify_ssl_certs=verify_ssl_certs,
        )
        self._last_response: ResponseMetadata | None = None
        if provider_telemetry is not None:
            self._provider_telemetry = provider_telemetry
        else:
            from ..provider_telemetry import ProviderTelemetry as ProviderTelemetryCls

            if enable_telemetry is None:
                from .. import _config

                resolved_enable = _config.enable_telemetry
                resolved_url = telemetry_url if telemetry_url is not None else _config.telemetry_url
            else:
                resolved_enable = enable_telemetry
                resolved_url = telemetry_url
            self._provider_telemetry = ProviderTelemetryCls.from_base_url(
                base_url,
                enabled=resolved_enable,
                telemetry_url=resolved_url,
            )

    @property
    def http_client(self) -> HTTPClient:
        return self._http_client

    @property
    def last_response(self) -> ResponseMetadata | None:
        return self._last_response

    def _headers(self) -> dict[str, str]:
        return default_request_headers(self._api_key, self._app_info)

    def post(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> BulkResponse:
        opts = normalize_options(options)
        url = self._base_url + path
        body_bytes = json.dumps(payload).encode("utf-8")
        open_timeout, read_timeout, write_timeout = resolve_timeouts(
            self._open_timeout,
            self._read_timeout,
            self._write_timeout,
            opts,
        )

        def on_success(body: str, _status: int, _headers: dict[str, str]) -> BulkResponse:
            return _parse_bulk_response(body)

        max_retries = resolve_max_retries(self._max_retries, opts)

        result = execute_http_request(
            http_client=self._http_client,
            method="POST",
            url=url,
            path=path,
            headers=merge_headers(self._headers(), opts),
            body=body_bytes,
            open_timeout=open_timeout,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            max_retries=max_retries,
            instrumentation=self._instrumentation,
            logger=self._logger,
            publish=self,
            retry_http_errors=False,
            on_success=on_success,
            provider_telemetry=self._provider_telemetry,
        )
        self._last_response = result.metadata
        return result.data
