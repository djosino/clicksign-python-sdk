from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Unpack

from ..request_options import RequestOptions
from ..resource import QueryProxy, Resource
from ..types import FolderCreateParams, FolderFilterParams
from ..types._attrs import bool_attr, str_attr


class Folder(Resource):
    resource_type = "folders"
    endpoint = "/folders"

    @property
    def name(self) -> str | None:
        return str_attr(self, "name")

    @property
    def path(self) -> str | None:
        return str_attr(self, "path")

    @property
    def in_root(self) -> bool | None:
        return bool_attr(self, "in_root")

    @property
    def created_at(self) -> str | None:
        return str_attr(self, "created_at")

    @property
    def updated_at(self) -> str | None:
        return str_attr(self, "updated_at")

    @property
    def parent_folder_id(self) -> str | None:
        return (self.relationships.get("folder") or {}).get("data", {}).get("id")  # type: ignore[no-any-return]

    @classmethod
    def filter(cls, **kwargs: Unpack[FolderFilterParams]) -> QueryProxy[Folder]:  # type: ignore[override]
        return super().filter(**kwargs)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        relationships: dict[str, Any] | None = None,
        *,
        options: RequestOptions | dict[str, Any] | None = None,
        **attrs: Unpack[FolderCreateParams],
    ) -> Folder:
        return super().create(relationships, options=options, **attrs)  # type: ignore[return-value]

    def update(self, **attrs: object) -> Folder:  # type: ignore[override]
        raise NotImplementedError("Folder does not support update")

    def delete(self, *, options: RequestOptions | dict[str, Any] | None = None) -> None:
        raise NotImplementedError("Folder does not support delete")
