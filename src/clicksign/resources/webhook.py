from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ..request_options import RequestOptions
from ..resource import QueryProxy, Resource
from ..types import WebhookCreateParams, WebhookFilterParams, WebhookUpdateParams
from ..types._attrs import list_str_attr, str_attr


class Webhook(Resource):
    resource_type = "webhooks"
    endpoint = "/webhooks"

    @property
    def callback_endpoint(self) -> str | None:
        """Webhook URL registered in Clicksign (API attribute ``endpoint``)."""
        return str_attr(self, "endpoint")

    @property
    def status(self) -> str | None:
        return str_attr(self, "status")

    @property
    def events(self) -> list[str] | None:
        return list_str_attr(self, "events")

    @property
    def secret(self) -> str | None:
        return str_attr(self, "secret")

    @property
    def created_at(self) -> str | None:
        return str_attr(self, "created_at")

    @property
    def updated_at(self) -> str | None:
        return str_attr(self, "updated_at")

    def __getattr__(self, name: str) -> Any:
        if name == "endpoint":
            value = self.callback_endpoint
            if value is not None:
                return value
        return super().__getattr__(name)

    @classmethod
    def filter(cls, **kwargs: Unpack[WebhookFilterParams]) -> QueryProxy[Webhook]:  # type: ignore[override]
        return super().filter(**kwargs)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[WebhookCreateParams],
    ) -> Webhook:
        return super().create(relationships, options=options, **attrs)  # type: ignore[return-value]

    def update(  # type: ignore[override]
        self,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[WebhookUpdateParams],
    ) -> Webhook:
        super().update(relationships, options=options, **attrs)
        return self
