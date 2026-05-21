from __future__ import annotations

from typing import Any

from ...resource import Resource


class Whatsapp(Resource):
    resource_type = "acceptance_term_whatsapps"
    endpoint = "/acceptance_term/whatsapps"

    def delete(self, *, options: Any = None) -> None:
        raise NotImplementedError("AcceptanceTerm::Whatsapp does not support delete")
