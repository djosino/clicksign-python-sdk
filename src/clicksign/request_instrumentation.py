from __future__ import annotations

from typing import Any

from .instrumentation import Instrumentation


class RequestInstrumentation:
    """Mixin that publishes instrumentation events. Used by Client and BulkOperationsClient."""

    def _publish_request(
        self, payload: dict[str, Any], inst: Instrumentation, logger: Any = None
    ) -> None:
        inst.publish("request", payload, logger)

    def _publish_retry(
        self, payload: dict[str, Any], inst: Instrumentation, logger: Any = None
    ) -> None:
        inst.publish("retry", payload, logger)

    def _publish_error(
        self, payload: dict[str, Any], inst: Instrumentation, logger: Any = None
    ) -> None:
        inst.publish("error", payload, logger)
