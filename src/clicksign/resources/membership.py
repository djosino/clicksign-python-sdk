from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ..request_options import RequestOptions
from ..resource import QueryProxy, Resource
from ..types import MembershipCreateParams, MembershipFilterParams, MembershipUpdateParams
from ..types._attrs import bool_attr, str_attr


class Membership(Resource):
    resource_type = "memberships"
    endpoint = "/memberships"

    @property
    def role(self) -> str | None:
        return str_attr(self, "role")

    @property
    def consumption_accessible(self) -> bool | None:
        return bool_attr(self, "consumption_accessible")

    @property
    def tracking_accessible(self) -> bool | None:
        return bool_attr(self, "tracking_accessible")

    @property
    def folder_management_accessible(self) -> bool | None:
        return bool_attr(self, "folder_management_accessible")

    @property
    def created(self) -> str | None:
        return str_attr(self, "created")

    @property
    def modified(self) -> str | None:
        return str_attr(self, "modified")

    @property
    def user_id(self) -> str | None:
        return (self.relationships.get("user") or {}).get("data", {}).get("id")  # type: ignore[no-any-return]

    @classmethod
    def filter(cls, **kwargs: Unpack[MembershipFilterParams]) -> QueryProxy[Membership]:  # type: ignore[override]
        return super().filter(**kwargs)

    @classmethod
    def filter_for_user(
        cls, user_id: str, **kwargs: Unpack[MembershipFilterParams]
    ) -> QueryProxy[Membership]:
        """Filter memberships by related user id (API filter ``user.id``)."""
        return cls.filter(**{"user.id": user_id}, **kwargs)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[MembershipCreateParams],
    ) -> Membership:
        return super().create(relationships, options=options, **attrs)  # type: ignore[return-value]

    def update(  # type: ignore[override]
        self,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[MembershipUpdateParams],
    ) -> Membership:
        super().update(relationships, options=options, **attrs)
        return self
