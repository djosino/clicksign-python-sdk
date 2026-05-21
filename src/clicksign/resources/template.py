from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ..request_options import RequestOptions
from ..resource import QueryProxy, Resource
from ..types import TemplateCreateParams, TemplateFilterParams, TemplateUpdateParams
from ..types._attrs import str_attr


class Template(Resource):
    resource_type = "templates"
    endpoint = "/templates"

    @property
    def name(self) -> str | None:
        return str_attr(self, "name")

    @property
    def color(self) -> str | None:
        return str_attr(self, "color")

    @property
    def content_base64(self) -> str | None:
        return str_attr(self, "content_base64")

    @property
    def created(self) -> str | None:
        return str_attr(self, "created")

    @property
    def modified(self) -> str | None:
        return str_attr(self, "modified")

    @classmethod
    def filter(cls, **kwargs: Unpack[TemplateFilterParams]) -> QueryProxy[Template]:  # type: ignore[override]
        return super().filter(**kwargs)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[TemplateCreateParams],
    ) -> Template:
        return super().create(relationships, options=options, **attrs)  # type: ignore[return-value]

    def update(  # type: ignore[override]
        self,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[TemplateUpdateParams],
    ) -> Template:
        super().update(relationships, options=options, **attrs)
        return self
