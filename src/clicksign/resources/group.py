from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ..request_options import RequestOptions
from ..resource import QueryProxy, Resource
from ..types import GroupCreateParams, GroupFilterParams, GroupUpdateParams
from ..types._attrs import str_attr


class Group(Resource):
    resource_type = "groups"
    endpoint = "/groups"

    @property
    def name(self) -> str | None:
        return str_attr(self, "name")

    @property
    def created(self) -> str | None:
        return str_attr(self, "created")

    @property
    def modified(self) -> str | None:
        return str_attr(self, "modified")

    @classmethod
    def filter(cls, **kwargs: Unpack[GroupFilterParams]) -> QueryProxy[Group]:  # type: ignore[override]
        return super().filter(**kwargs)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[GroupCreateParams],
    ) -> Group:
        return super().create(relationships, options=options, **attrs)  # type: ignore[return-value]

    def update(  # type: ignore[override]
        self,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[GroupUpdateParams],
    ) -> Group:
        super().update(relationships, options=options, **attrs)
        return self
