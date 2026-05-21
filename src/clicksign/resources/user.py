from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ..request_options import RequestOptions
from ..resource import QueryProxy, Resource
from ..types import UserCreateParams, UserFilterParams
from ..types._attrs import str_attr


class User(Resource):
    resource_type = "users"
    endpoint = "/users"

    @property
    def name(self) -> str | None:
        return str_attr(self, "name")

    @property
    def email(self) -> str | None:
        return str_attr(self, "email")

    @property
    def phone_number(self) -> str | None:
        return str_attr(self, "phone_number")

    @property
    def created(self) -> str | None:
        return str_attr(self, "created")

    @property
    def modified(self) -> str | None:
        return str_attr(self, "modified")

    @classmethod
    def filter(cls, **kwargs: Unpack[UserFilterParams]) -> QueryProxy[User]:  # type: ignore[override]
        return super().filter(**kwargs)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[UserCreateParams],
    ) -> User:
        return super().create(relationships, options=options, **attrs)  # type: ignore[return-value]

    @classmethod
    def me(cls) -> User:
        client = cls._get_client()
        response = client.get("/users/me")
        instances, _ = cls._parse_response(response)
        return cls._attach_from_client(client, instances)[0]  # type: ignore[return-value]

    def update(self, **attrs: object) -> User:  # type: ignore[override]
        raise NotImplementedError("User does not support update")

    def delete(self, *, options: RequestOptions | dict[str, Any] | None = None) -> None:
        raise NotImplementedError("User does not support delete")
