from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from typing import Any

from . import errors, retry_backoff
from .error_handler import handle as handle_error
from .http_transport import AsyncHTTPClient, HTTPConnectionError, HTTPStatusError
from .instrumentation import Instrumentation
from .log import log_error, log_http_exchange, log_retry
from .request_instrumentation import RequestInstrumentation
from .response_metadata import HttpResult, build_response_metadata


async def execute_async_http_request(
    *,
    http_client: AsyncHTTPClient,
    method: str,
    url: str,
    path: str,
    headers: dict[str, str],
    body: bytes | None,
    open_timeout: float,
    read_timeout: float,
    write_timeout: float,
    max_retries: int,
    instrumentation: Instrumentation,
    logger: Any,
    publish: RequestInstrumentation,
    retry_http_errors: bool = True,
    on_success: Callable[[str, int, dict[str, str]], Any] | None = None,
    provider_telemetry: Any | None = None,
) -> HttpResult:
    method_lower = method.lower()
    last_error: errors.ClicksignError | None = None

    def _record_telemetry(status: int | None, duration_ms: float, attempt: int) -> None:
        if provider_telemetry is not None:
            provider_telemetry.record(
                method=method_lower,
                path=path,
                status=status,
                duration_ms=duration_ms,
                attempt=attempt,
            )

    for attempt in range(1, max_retries + 2):
        start = time.monotonic()
        status: int | None = None
        try:
            response = await http_client.request(
                method,
                url,
                headers=headers,
                body=body,
                open_timeout=open_timeout,
                read_timeout=read_timeout,
                write_timeout=write_timeout,
            )
            status = response.status
            duration_ms = (time.monotonic() - start) * 1000
            metadata = build_response_metadata(status, response.headers, duration_ms)

            publish._publish_request(
                {
                    "method": method_lower,
                    "path": path,
                    "status": status,
                    "attempt": attempt,
                    "duration_ms": duration_ms,
                },
                instrumentation,
                logger,
            )
            log_http_exchange(
                method=method_lower,
                path=path,
                attempt=attempt,
                status=status,
                duration_ms=duration_ms,
                request_headers=headers,
                request_body=body,
                response_headers=response.headers,
                response_body=response.body,
            )
            _record_telemetry(status, duration_ms, attempt)

            handle_error(status, response.body, response.headers)

            if on_success is not None:
                data = on_success(response.body, status, response.headers)
            elif not response.body or not response.body.strip():
                data = None
            else:
                data = json.loads(response.body)

            return HttpResult(data=data, metadata=metadata)

        except HTTPStatusError as exc:
            duration_ms = (time.monotonic() - start) * 1000
            status = exc.status
            response_body = exc.body
            resp_headers = exc.headers

            publish._publish_request(
                {
                    "method": method_lower,
                    "path": path,
                    "status": status,
                    "attempt": attempt,
                    "duration_ms": duration_ms,
                },
                instrumentation,
                logger,
            )
            log_http_exchange(
                method=method_lower,
                path=path,
                attempt=attempt,
                status=status,
                duration_ms=duration_ms,
                request_headers=headers,
                request_body=body,
                response_headers=resp_headers,
                response_body=response_body,
            )
            _record_telemetry(status, duration_ms, attempt)

            try:
                handle_error(status, response_body, resp_headers)
            except errors.ClicksignError as err:
                publish._publish_error(
                    {
                        "method": method_lower,
                        "path": path,
                        "status": status,
                        "error": err,
                        "duration_ms": duration_ms,
                    },
                    instrumentation,
                    logger,
                )
                if retry_http_errors and err.retryable and attempt <= max_retries:
                    wait = retry_backoff.retry_delay(attempt, resp_headers)
                    publish._publish_retry(
                        {
                            "method": method_lower,
                            "path": path,
                            "attempt": attempt,
                            "max_retries": max_retries,
                            "error": err,
                            "wait_ms": int(wait * 1000),
                        },
                        instrumentation,
                        logger,
                    )
                    log_retry(
                        method=method_lower,
                        path=path,
                        attempt=attempt,
                        max_retries=max_retries,
                        wait_ms=int(wait * 1000),
                        error=err,
                    )
                    await asyncio.sleep(wait)
                    last_error = err
                    continue
                log_error(
                    method=method_lower,
                    path=path,
                    status=status,
                    duration_ms=duration_ms,
                    error=err,
                )
                raise

        except (HTTPConnectionError, TimeoutError, OSError) as exc:
            duration_ms = (time.monotonic() - start) * 1000
            timeout_err = errors.TimeoutError(str(exc))

            publish._publish_request(
                {
                    "method": method_lower,
                    "path": path,
                    "status": None,
                    "attempt": attempt,
                    "duration_ms": duration_ms,
                },
                instrumentation,
                logger,
            )
            log_http_exchange(
                method=method_lower,
                path=path,
                attempt=attempt,
                status=None,
                duration_ms=duration_ms,
                request_headers=headers,
                request_body=body,
            )
            _record_telemetry(None, duration_ms, attempt)
            publish._publish_error(
                {
                    "method": method_lower,
                    "path": path,
                    "status": None,
                    "error": timeout_err,
                    "duration_ms": duration_ms,
                },
                instrumentation,
                logger,
            )

            if attempt <= max_retries:
                wait = retry_backoff.delay(attempt)
                publish._publish_retry(
                    {
                        "method": method_lower,
                        "path": path,
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "error": timeout_err,
                        "wait_ms": int(wait * 1000),
                    },
                    instrumentation,
                    logger,
                )
                log_retry(
                    method=method_lower,
                    path=path,
                    attempt=attempt,
                    max_retries=max_retries,
                    wait_ms=int(wait * 1000),
                    error=timeout_err,
                )
                await asyncio.sleep(wait)
                last_error = timeout_err
                continue
            log_error(
                method=method_lower,
                path=path,
                status=None,
                duration_ms=duration_ms,
                error=timeout_err,
            )
            raise timeout_err from exc

    raise last_error  # type: ignore[misc]
