from __future__ import annotations

from ...resource import Resource


class Whatsapp(Resource):
    resource_type = "acceptance_term_whatsapps"
    endpoint = "/acceptance_term/whatsapps"

    def delete(self) -> None:
        raise NotImplementedError("AcceptanceTerm::Whatsapp does not support delete")
