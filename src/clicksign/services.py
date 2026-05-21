from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from .client import Client
from .client_scope import client_scope
from .configuration import _ENVIRONMENTS, DEFAULT_MAX_RETRIES
from .json_api.bulk_operations_client import BulkOperationsClient


class Services:
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        environment: str | None = None,
        open_timeout: float = 2.0,
        read_timeout: float = 10.0,
        write_timeout: float = 10.0,
        max_retries: int = DEFAULT_MAX_RETRIES,
        *,
        http_client: Any = None,
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

        self._api_key = api_key
        self._base_url = base_url or _ENVIRONMENTS["production"]
        self._open_timeout = open_timeout
        self._read_timeout = read_timeout
        self._write_timeout = write_timeout
        self._max_retries = max_retries
        self._http_client = http_client
        self._proxy = proxy
        self._verify_ssl_certs = verify_ssl_certs
        self._app_info = app_info
        self._enable_telemetry = enable_telemetry
        self._telemetry_url = telemetry_url

    @contextmanager
    def use(self) -> Generator[Client, None, None]:
        from . import _config, instrumentation
        from .provider_telemetry import ProviderTelemetry

        if self._enable_telemetry is None:
            resolved_enable = _config.enable_telemetry
            resolved_telemetry_url = (
                self._telemetry_url if self._telemetry_url is not None else _config.telemetry_url
            )
        else:
            resolved_enable = self._enable_telemetry
            resolved_telemetry_url = self._telemetry_url
        provider_telemetry = ProviderTelemetry.from_base_url(
            self._base_url,
            enabled=resolved_enable,
            telemetry_url=resolved_telemetry_url,
        )

        client = Client(
            api_key=self._api_key,
            base_url=self._base_url,
            open_timeout=self._open_timeout,
            read_timeout=self._read_timeout,
            write_timeout=self._write_timeout,
            max_retries=self._max_retries,
            instrumentation=instrumentation,
            logger=_config.logger,
            http_client=self._http_client,
            proxy=self._proxy,
            verify_ssl_certs=self._verify_ssl_certs,
            app_info=self._app_info,
            provider_telemetry=provider_telemetry,
        )
        bulk_client = BulkOperationsClient(
            api_key=self._api_key,
            base_url=self._base_url,
            open_timeout=self._open_timeout,
            read_timeout=self._read_timeout,
            write_timeout=self._write_timeout,
            max_retries=self._max_retries,
            instrumentation=instrumentation,
            logger=_config.logger,
            http_client=self._http_client,
            proxy=self._proxy,
            verify_ssl_certs=self._verify_ssl_certs,
            app_info=self._app_info,
            provider_telemetry=provider_telemetry,
        )
        with client_scope(client, bulk_client):
            yield client
