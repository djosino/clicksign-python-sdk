"""Config local para scripts sandbox (não importar no pacote)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SANDBOX_DIR = Path(__file__).resolve().parent
LAST_RUN_PATH = SANDBOX_DIR / ".last_run.json"


def _load_dotenv() -> None:
    env_file = SANDBOX_DIR / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def get_client():
    _load_dotenv()
    api_key = os.environ.get("CLICKSIGN_API_KEY", "").strip()
    if not api_key:
        print(
            "Defina CLICKSIGN_API_KEY em scripts/sandbox/.env "
            "(copie de .env.example)",
            file=sys.stderr,
        )
        sys.exit(1)

    from clicksign import ClicksignClient

    environment = os.environ.get("CLICKSIGN_ENVIRONMENT", "sandbox").strip()
    return ClicksignClient(api_key=api_key, environment=environment)


def save_last_run(data: dict[str, str]) -> None:
    LAST_RUN_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"\nIDs salvos em {LAST_RUN_PATH}")


def load_last_run() -> dict[str, str]:
    if not LAST_RUN_PATH.is_file():
        return {}
    return json.loads(LAST_RUN_PATH.read_text(encoding="utf-8"))


# PDF mínimo válido (1 página em branco)
MINIMAL_PDF_BYTES = (
    b"%PDF-1.4\n1 0 obj<<>>endobj\n2 0 obj<</Length 44>>stream\n"
    b"BT /F1 12 Tf 100 700 Td (SDK sandbox test) Tj ET\n"
    b"endstream\nendobj\n3 0 obj<</Type/Page/Parent 4 0 R/MediaBox[0 0 612 792]"
    b"/Contents 2 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"trailer<</Root 4 0 R>>\n%%EOF\n"
)


def pdf_content_base64() -> str:
    import base64

    raw = base64.b64encode(MINIMAL_PDF_BYTES).decode("ascii")
    return f"data:application/pdf;base64,{raw}"
