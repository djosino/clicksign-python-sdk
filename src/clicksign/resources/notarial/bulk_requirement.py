from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ...json_api.bulk_operations_client import BulkResponse
from ...json_api.operations import BulkRequirementOperations
from ...request_options import RequestOptions
from ...resource import Resource


class BulkRequirement(Resource):
    resource_type = "bulk_requirements"
    endpoint = "/bulk_requirements"

    @classmethod
    def create(  # type: ignore[override]
        cls,
        envelope_id: str,
        block: Callable[[BulkRequirementOperations], None] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> BulkResponse:
        if block is None:
            raise TypeError("block callable is required for BulkRequirement.create")

        ops = BulkRequirementOperations()
        block(ops)

        from ... import _global_bulk_client
        from ...client_scope import get_thread_bulk_client

        bulk_client = get_thread_bulk_client() or _global_bulk_client()
        path = f"/envelopes/{envelope_id}/bulk_requirements"
        return bulk_client.post(path, ops.to_payload(), options=options)
