from __future__ import annotations

import json
import platform
import queue
import re
import threading
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .app_info import get_app_info
from .version import __version__

_UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def normalize_telemetry_path(path: str) -> str:
    return _UUID_PATTERN.sub("{id}", path)


def default_telemetry_url(base_url: str) -> str:
    parsed = urllib.parse.urlparse(base_url.rstrip("/"))
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return f"{origin}/sdk/telemetry/v1/events"


@dataclass(frozen=True)
class TelemetryEvent:
    method: str
    path: str
    status: int | None
    duration_ms: float
    attempt: int

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "sdk": "clicksign-python",
            "sdk_version": __version__,
            "python_version": platform.python_version(),
            "method": self.method,
            "path": normalize_telemetry_path(self.path),
            "status": self.status,
            "duration_ms": round(self.duration_ms, 2),
            "attempt": self.attempt,
        }
        app_info = get_app_info()
        if app_info is not None:
            payload["app_name"] = app_info.name
            payload["app_version"] = app_info.version
        return payload


SendFn = Callable[[str, dict[str, Any]], None]


class ProviderTelemetry:
    """Best-effort, fire-and-forget telemetry to the API provider (opt-in)."""

    def __init__(
        self,
        *,
        enabled: bool,
        telemetry_url: str,
        send_fn: SendFn | None = None,
        max_queue_size: int = 1000,
    ) -> None:
        self._enabled = enabled
        self._telemetry_url = telemetry_url
        self._send_fn = send_fn or self._default_send
        self._queue: queue.Queue[TelemetryEvent | None] = queue.Queue(maxsize=max_queue_size)
        self._worker: threading.Thread | None = None
        if enabled:
            self._start_worker()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @classmethod
    def from_base_url(
        cls,
        base_url: str,
        *,
        enabled: bool,
        telemetry_url: str | None = None,
        send_fn: SendFn | None = None,
    ) -> ProviderTelemetry:
        return cls(
            enabled=enabled,
            telemetry_url=telemetry_url or default_telemetry_url(base_url),
            send_fn=send_fn,
        )

    def record(
        self,
        *,
        method: str,
        path: str,
        status: int | None,
        duration_ms: float,
        attempt: int,
    ) -> None:
        if not self._enabled:
            return
        event = TelemetryEvent(
            method=method.lower(),
            path=path,
            status=status,
            duration_ms=duration_ms,
            attempt=attempt,
        )
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            return

    def flush(self, timeout: float = 1.0) -> None:
        if not self._enabled:
            return
        self._queue.join()

    def close(self) -> None:
        if self._worker is None:
            return
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        self._worker.join(timeout=1.0)
        self._worker = None

    def _start_worker(self) -> None:
        self._worker = threading.Thread(
            target=self._worker_loop,
            name="clicksign-telemetry",
            daemon=True,
        )
        self._worker.start()

    def _worker_loop(self) -> None:
        while True:
            event = self._queue.get()
            try:
                if event is None:
                    return
                self._send_fn(self._telemetry_url, event.to_payload())
            except Exception:
                pass
            finally:
                self._queue.task_done()

    @staticmethod
    def _default_send(url: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"clicksign-python-telemetry/{__version__}",
            },
        )
        with urllib.request.urlopen(request, timeout=1.0) as response:
            response.read()
