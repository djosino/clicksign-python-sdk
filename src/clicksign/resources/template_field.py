from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ..request_options import RequestOptions
from ..resource import QueryProxy, Resource
from ..types import TemplateFieldFilterParams
from ..types._attrs import str_attr


class TemplateField(Resource):
    resource_type = "template_fields"
    endpoint = "/template_fields"

    @property
    def name(self) -> str | None:
        return str_attr(self, "name")

    @property
    def kind(self) -> str | None:
        return str_attr(self, "kind")

    @property
    def created(self) -> str | None:
        return str_attr(self, "created")

    @property
    def modified(self) -> str | None:
        return str_attr(self, "modified")

    @property
    def template_id(self) -> str | None:
        return (self.relationships.get("template") or {}).get("data", {}).get("id")  # type: ignore[no-any-return]

    @classmethod
    def filter(cls, **kwargs: Unpack[TemplateFieldFilterParams]) -> QueryProxy[TemplateField]:  # type: ignore[override]
        return super().filter(**kwargs)

    def update(self, **attrs: object) -> TemplateField:  # type: ignore[override]
        raise NotImplementedError("TemplateField does not support update")

    def delete(self, *, options: RequestOptions | dict[str, Any] | None = None) -> None:
        raise NotImplementedError("TemplateField does not support delete")

    @classmethod
    def retrieve(
        cls,
        resource_id: str,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
    ) -> TemplateField:
        raise NotImplementedError("TemplateField does not support retrieve")

    @classmethod
    def create(cls, **attrs: object) -> TemplateField:  # type: ignore[override]
        raise NotImplementedError("TemplateField does not support create")
