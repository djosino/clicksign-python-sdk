from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ._async.clicksign_client import AsyncClicksignClient
from ._async.client import AsyncClient
from ._http.headers import CORRELATION_ID_HEADER, correlation_id
from ._http.transport import (
    AsyncHTTPClient,
    HTTPClient,
    HTTPConnectionError,
    HTTPResponse,
    HTTPStatusError,
    HttpxAsyncHTTPClient,
    HttpxHTTPClient,
    UrllibHTTPClient,
    default_async_http_client,
    default_http_client,
)
from .api_error import ApiError
from .app_info import AppInfo, clear_app_info, get_app_info
from .app_info import set_app_info as _set_app_info
from .clicksign_client import ClicksignClient
from .client import Client
from .configuration import Configuration
from .errors import (
    AuthenticationError,
    ClicksignError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
    WebhookPayloadError,
    WebhookSignatureError,
)
from .instrumentation import Instrumentation
from .json_api.included import IncludedIndex
from .json_api.parser import ParsedResponse
from .log import bootstrap_from_env, get_log, get_logger, set_log
from .raw_response import RawResponse
from .request_options import RequestOptions
from .resources.folder import Folder
from .resources.notarial.bulk_requirement import BulkRequirement
from .resources.notarial.document import Document
from .resources.notarial.envelope import Envelope
from .resources.notarial.requirement import Requirement
from .resources.notarial.signature_watcher import SignatureWatcher
from .resources.notarial.signer import Signer
from .resources.webhook import Webhook
from .response_metadata import ResponseMetadata
from .services import Services
from .version import __version__
from .webhook import WebhookEvent, compute_signature, construct_event, verify_signature

_config: Configuration = Configuration()
instrumentation: Instrumentation = Instrumentation()
_client: Any = None
_bulk_client: Any = None


def configure(**kwargs: Any) -> None:
    """Configure the global Clicksign client.

    Accepted kwargs mirror :class:`~clicksign.configuration.Configuration` attributes:
    ``api_key``, ``base_url``, ``environment``, ``open_timeout``, ``read_timeout``,
    ``write_timeout``, ``max_retries``, ``logger``, ``proxy``, ``verify_ssl_certs``,
    ``http_client``, ``enable_telemetry``, ``telemetry_url``, ``log``.
    Resets the cached global client so the next request picks up new settings.
    """
    global _config, _client, _bulk_client
    log_value = kwargs.pop("log", None)
    for key, value in kwargs.items():
        setattr(_config, key, value)
    if log_value is not None:
        _config.log_level = None if log_value is False else str(log_value)
        set_log(log_value)
    elif _config.log_level is not None:
        set_log(_config.log_level)
    _client = None
    _bulk_client = None


def get_enable_telemetry() -> bool:
    """Return whether provider telemetry is enabled for the global client."""
    return bool(_config.enable_telemetry)


def set_enable_telemetry(enabled: bool) -> None:
    """Enable or disable provider telemetry for the global client.

    Resets the cached global client so the change takes effect on the next request.
    """
    global _client, _bulk_client
    _config.enable_telemetry = enabled
    _client = None
    _bulk_client = None


def _global_client() -> Any:
    global _client
    if _client is None:
        from .client import Client

        _client = Client(
            api_key=_config.api_key or "",
            base_url=_config.base_url,
            open_timeout=_config.open_timeout,
            read_timeout=_config.read_timeout,
            write_timeout=_config.write_timeout,
            max_retries=_config.max_retries,
            instrumentation=instrumentation,
            logger=_config.logger,
            http_client=_config.http_client,
            proxy=_config.proxy,
            verify_ssl_certs=_config.verify_ssl_certs,
        )
    return _client


def _global_bulk_client() -> Any:
    global _bulk_client
    if _bulk_client is None:
        from .json_api.bulk_operations_client import BulkOperationsClient

        _bulk_client = BulkOperationsClient(
            api_key=_config.api_key or "",
            base_url=_config.base_url,
            open_timeout=_config.open_timeout,
            read_timeout=_config.read_timeout,
            write_timeout=_config.write_timeout,
            max_retries=_config.max_retries,
            instrumentation=instrumentation,
            logger=_config.logger,
            http_client=_config.http_client,
            proxy=_config.proxy,
            verify_ssl_certs=_config.verify_ssl_certs,
        )
    return _bulk_client


def set_app_info(name: str, version: str, url: str | None = None) -> None:
    """Identify the host application in the User-Agent header."""
    _set_app_info(name, version, url)


def on_request(callback: Callable[..., Any]) -> None:
    """Register a callback fired after every HTTP request (success or error).

    Callback receives a dict with keys: ``method``, ``path``, ``status``,
    ``attempt``, ``duration_ms``. Exceptions in the callback are swallowed.
    """
    instrumentation.on_request(callback)


def on_retry(callback: Callable[..., Any]) -> None:
    """Register a callback fired before each retry attempt.

    Callback receives a dict with keys: ``method``, ``path``, ``attempt``,
    ``max_retries``, ``error``, ``wait_ms``. Exceptions in the callback are swallowed.
    """
    instrumentation.on_retry(callback)


def on_error(callback: Callable[..., Any]) -> None:
    """Register a callback fired when a request raises a :class:`ClicksignError`.

    Callback receives a dict with keys: ``method``, ``path``, ``status``,
    ``error``, ``duration_ms``. Exceptions in the callback are swallowed.
    """
    instrumentation.on_error(callback)


# Module-level __getattr__/__setattr__ expose `clicksign.log` as a writable
# property without importing the internal _log_level at module load time.
# This avoids a circular-import between __init__ and log.py during bootstrap.
def __getattr__(name: str) -> Any:
    if name == "log":
        return get_log()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __setattr__(name: str, value: Any) -> None:
    if name == "log":
        set_log(value)
        return
    globals()[name] = value


bootstrap_from_env()


__all__ = [
    "configure",
    "set_app_info",
    "get_app_info",
    "get_enable_telemetry",
    "set_enable_telemetry",
    "AppInfo",
    "clear_app_info",
    "Client",
    "AsyncClient",
    "ClicksignClient",
    "AsyncClicksignClient",
    "Services",
    "RequestOptions",
    "correlation_id",
    "CORRELATION_ID_HEADER",
    "ResponseMetadata",
    "RawResponse",
    "ParsedResponse",
    "IncludedIndex",
    "on_request",
    "on_retry",
    "on_error",
    "get_log",
    "set_log",
    "get_logger",
    "log",
    "instrumentation",
    "__version__",
    "HTTPClient",
    "AsyncHTTPClient",
    "HTTPConnectionError",
    "HTTPResponse",
    "HTTPStatusError",
    "UrllibHTTPClient",
    "HttpxHTTPClient",
    "HttpxAsyncHTTPClient",
    "default_http_client",
    "default_async_http_client",
    "ClicksignError",
    "ApiError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "WebhookSignatureError",
    "WebhookPayloadError",
    "WebhookEvent",
    "construct_event",
    "compute_signature",
    "verify_signature",
    "Envelope",
    "Document",
    "Signer",
    "Requirement",
    "BulkRequirement",
    "SignatureWatcher",
    "Webhook",
    "Folder",
]
