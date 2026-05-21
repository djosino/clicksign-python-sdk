from __future__ import annotations

import logging
import os

LOGGER_NAME = "clicksign"
_MAX_BODY_LOG_CHARS = 4096

_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}

_SENSITIVE_HEADERS = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
    }
)

_log_level: str | None = None
_env_bootstrapped = False


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def get_log() -> str | None:
    return _log_level


def set_log(level: str | bool | None) -> None:
    """Enable SDK logging at ``debug``, ``info``, ``warn``/``warning``, or ``error``."""
    global _log_level
    if level is None or level is False:
        _log_level = None
    elif level is True:
        _log_level = "info"
    else:
        normalized = str(level).strip().lower()
        if normalized not in _LEVELS:
            raise ValueError(
                f"Invalid log level: {level!r}. "
                "Use 'debug', 'info', 'warn', 'warning', or 'error'."
            )
        _log_level = normalized
    _apply_logger_level()


def bootstrap_from_env() -> None:
    global _env_bootstrapped
    if _env_bootstrapped:
        return
    _env_bootstrapped = True
    env_value = os.environ.get("CLICKSIGN_LOG")
    if env_value:
        set_log(env_value)


def sanitize_headers(headers: dict[str, str] | None) -> dict[str, str]:
    if not headers:
        return {}
    sanitized: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in _SENSITIVE_HEADERS:
            sanitized[key] = "<redacted>"
        else:
            sanitized[key] = value
    return sanitized


def sanitize_body(body: bytes | str | None) -> str | None:
    if body is None:
        return None
    if isinstance(body, bytes):
        text = body.decode("utf-8", errors="replace")
    else:
        text = body
    if not text:
        return None
    if len(text) > _MAX_BODY_LOG_CHARS:
        return text[:_MAX_BODY_LOG_CHARS] + "...(truncated)"
    return text


def log_http_exchange(
    *,
    method: str,
    path: str,
    attempt: int,
    status: int | None,
    duration_ms: float,
    request_headers: dict[str, str] | None = None,
    request_body: bytes | None = None,
    response_headers: dict[str, str] | None = None,
    response_body: bytes | str | None = None,
) -> None:
    if not _should_log("info"):
        return

    logger = get_logger()
    summary = (
        f"request {method.upper()} {path} "
        f"status={status} attempt={attempt} duration_ms={duration_ms:.1f}"
    )

    if _should_log("debug"):
        parts = [
            summary,
            f"request_headers={sanitize_headers(request_headers)}",
        ]
        request_text = sanitize_body(request_body)
        if request_text is not None:
            parts.append(f"request_body={request_text}")
        if response_headers is not None:
            parts.append(f"response_headers={sanitize_headers(response_headers)}")
        response_text = sanitize_body(response_body)
        if response_text is not None:
            parts.append(f"response_body={response_text}")
        logger.debug(" ".join(parts))
        return

    logger.info(summary)


def log_retry(
    *,
    method: str,
    path: str,
    attempt: int,
    max_retries: int,
    wait_ms: int,
    error: Exception,
) -> None:
    if not _should_log("warn"):
        return
    get_logger().warning(
        "retry %s %s attempt=%s/%s wait_ms=%s error=%s: %s",
        method.upper(),
        path,
        attempt,
        max_retries,
        wait_ms,
        type(error).__name__,
        error,
    )


def log_error(
    *,
    method: str,
    path: str,
    status: int | None,
    duration_ms: float,
    error: Exception,
) -> None:
    if not _should_log("error"):
        return
    get_logger().error(
        "error %s %s status=%s duration_ms=%.1f error=%s: %s",
        method.upper(),
        path,
        status,
        duration_ms,
        type(error).__name__,
        error,
    )


def _should_log(min_level: str) -> bool:
    current = _log_level
    if current is None:
        return False
    return _LEVELS[min_level] >= _LEVELS[current]


def _apply_logger_level() -> None:
    logger = get_logger()
    if _log_level is None:
        logger.setLevel(logging.NOTSET)
        return

    logger.setLevel(_LEVELS[_log_level])
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.propagate = False
