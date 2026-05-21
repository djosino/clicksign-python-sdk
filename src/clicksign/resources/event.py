from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ..resource import QueryProxy, Resource
from ..types import AccountEventFilterParams
from ..types._attrs import dict_attr, str_attr


class Event(Resource):
    """Account-level audit events (``GET /events``)."""

    resource_type = "events"
    endpoint = "/events"

    @property
    def name(self) -> str | None:
        return str_attr(self, "name")

    @property
    def data(self) -> dict[str, Any] | None:
        return dict_attr(self, "data")

    @property
    def created(self) -> str | None:
        return str_attr(self, "created")

    @classmethod
    def filter(cls, **kwargs: Unpack[AccountEventFilterParams]) -> QueryProxy[Event]:  # type: ignore[override]
        return super().filter(**kwargs)
