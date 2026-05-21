from __future__ import annotations

import threading
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client
    from .json_api.bulk_operations_client import BulkOperationsClient


@contextmanager
def client_scope(
    client: Client,
    bulk_client: BulkOperationsClient | None = None,
) -> Generator[None, None, None]:
    thread = threading.current_thread()
    prev_client = thread.__dict__.get("_clicksign_client")
    prev_bulk = thread.__dict__.get("_clicksign_bulk_client")

    thread.__dict__["_clicksign_client"] = client
    if bulk_client is not None:
        thread.__dict__["_clicksign_bulk_client"] = bulk_client

    try:
        yield
    finally:
        if prev_client is None:
            thread.__dict__.pop("_clicksign_client", None)
        else:
            thread.__dict__["_clicksign_client"] = prev_client

        if bulk_client is not None:
            if prev_bulk is None:
                thread.__dict__.pop("_clicksign_bulk_client", None)
            else:
                thread.__dict__["_clicksign_bulk_client"] = prev_bulk


def get_thread_client() -> Client | None:
    return threading.current_thread().__dict__.get("_clicksign_client")


def get_thread_bulk_client() -> BulkOperationsClient | None:
    return threading.current_thread().__dict__.get("_clicksign_bulk_client")
