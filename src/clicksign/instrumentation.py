from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Instrumentation:
    def __init__(self) -> None:
        self._callbacks: dict[str, list[Callable[..., Any]]] = {
            "request": [],
            "retry": [],
            "error": [],
        }

    def on_request(self, callback: Callable[..., Any]) -> None:
        self._callbacks["request"].append(callback)

    def on_retry(self, callback: Callable[..., Any]) -> None:
        self._callbacks["retry"].append(callback)

    def on_error(self, callback: Callable[..., Any]) -> None:
        self._callbacks["error"].append(callback)

    def publish(self, event: str, payload: dict[str, Any], logger: Any = None) -> None:
        for callback in self._callbacks.get(event, []):
            try:
                callback(payload)
            except Exception as exc:
                if logger is not None:
                    logger.warning(f"instrumentation callback error: {exc}")

    def clear(self) -> None:
        for key in self._callbacks:
            self._callbacks[key] = []
