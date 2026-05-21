from __future__ import annotations

import json
import urllib.parse
from typing import TYPE_CHECKING, Any

from .._http.headers import default_request_headers
from .._http.transport import AsyncHTTPClient, default_async_http_client
from ..instrumentation import Instrumentation
from ..raw_response import RawResponse
from ..request_instrumentation import RequestInstrumentation
from ..request_options import (
    RequestOptions,
    merge_headers,
    normalize_options,
    resolve_max_retries,
    resolve_timeouts,
)
from ..response_metadata import ResponseMetadata
from .http_executor import execute_async_http_request

if TYPE_CHECKING:
    from ..app_info import AppInfo
    from ..provider_telemetry import ProviderTelemetry
    from ..resource import Resource


class AsyncClient(RequestInstrumentation):
    """Async HTTP client for the Clicksign API (requires ``httpx``; see ``clicksign[async]``)."""

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
        http_client: AsyncHTTPClient | None = None,
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
        self._http_client = http_client or default_async_http_client(
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
    def http_client(self) -> AsyncHTTPClient:
        return self._http_client

    @property
    def last_response(self) -> ResponseMetadata | None:
        return self._last_response

    def _headers(self) -> dict[str, str]:
        return default_request_headers(self._api_key, self._app_info)

    async def get(
        self,
        path: str,
        params: dict[str, str] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> Any:
        return await self._request("GET", path, params=params, options=options)

    async def post(
        self,
        path: str,
        body: dict[str, Any],
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> Any:
        return await self._request("POST", path, body=body, options=options)

    async def patch(
        self,
        path: str,
        body: dict[str, Any],
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> Any:
        return await self._request("PATCH", path, body=body, options=options)

    async def delete(
        self,
        path: str,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> None:
        return await self._request("DELETE", path, options=options)  # type: ignore[no-any-return]

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
        opts = normalize_options(options)
        merged_headers = merge_headers(self._headers(), opts)
        if headers:
            merged_headers.update(headers)

        result = await self._request(
            method.upper(),
            path,
            params=params,
            body=body,
            options=opts,
            headers=merged_headers,
        )
        assert self._last_response is not None
        return RawResponse(
            status=self._last_response.status,
            headers=self._last_response.headers,
            body=result,
            metadata=self._last_response,
        )

    @staticmethod
    def deserialize(
        response: RawResponse | dict[str, Any],
        resource_class: type[Resource],
    ) -> Resource | list[Resource]:
        from ..client import Client

        return Client.deserialize(response, resource_class)

    async def aclose(self) -> None:
        await self._http_client.aclose()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def _build_url(self, path: str, params: dict[str, str] | None) -> str:
        url = self._base_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        opts = normalize_options(options)
        url = self._build_url(path, params)
        body_bytes = json.dumps(body).encode("utf-8") if body is not None else None
        open_timeout, read_timeout, write_timeout = resolve_timeouts(
            self._open_timeout,
            self._read_timeout,
            self._write_timeout,
            opts,
        )
        request_headers = headers if headers is not None else merge_headers(self._headers(), opts)
        max_retries = resolve_max_retries(self._max_retries, opts)

        result = await execute_async_http_request(
            http_client=self._http_client,
            method=method,
            url=url,
            path=path,
            headers=request_headers,
            body=body_bytes,
            open_timeout=open_timeout,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            max_retries=max_retries,
            instrumentation=self._instrumentation,
            logger=self._logger,
            publish=self,
            retry_http_errors=True,
            provider_telemetry=self._provider_telemetry,
        )
        self._last_response = result.metadata
        return result.data
