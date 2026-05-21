#!/usr/bin/env python3
"""
Opcional: ativa envelope (status running) e envia notificação.

Uso: python 04_activate_optional.py [envelope_id]
Requer IDs em .last_run.json (rode 02_create_notarial_draft.py antes).

Nota: alguns tokens sandbox retornam 403 em POST /activate; neste caso
usamos PATCH status=running (documentado em docs/WORKFLOW.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _config import get_client, load_last_run  # noqa: E402


def _activate_envelope(client, envelope_id: str):
    """Ativa o envelope; tenta POST /activate e faz fallback para PATCH."""
    from clicksign.errors import AuthenticationError

    envelope = client.notarial.envelopes.retrieve(envelope_id)
    if envelope.status == "running":
        print("  envelope já está em running")
        return envelope

    try:
        return client.notarial.envelopes.activate(envelope_id)
    except AuthenticationError as exc:
        if exc.status_code != 403:
            raise
        print("  POST /activate retornou 403 (token sem permissão) — usando update(status='running')")
        envelope.update(status="running")
        return envelope


def main() -> None:
    last = load_last_run()
    envelope_id = (sys.argv[1] if len(sys.argv) > 1 else last.get("envelope_id", "")).strip()
    signer_id = last.get("signer_id", "")
    if not envelope_id:
        print("Precisa de envelope_id (.last_run.json ou argumento)", file=sys.stderr)
        sys.exit(1)

    client = get_client()

    with client.use():
        print(f"Ativando envelope {envelope_id}...")
        envelope = _activate_envelope(client, envelope_id)
        print(f"  status={envelope.status}")

        print("Notificando signatários (envelope.notify)...")
        envelope.notify(
            message="Teste SDK Python — documento disponível para assinatura (sandbox).",
        )
        print("  envelope.notify: OK")

        if signer_id:
            print(f"Notificando signatário {signer_id} (Signer.notify, sem subject)...")
            try:
                client.notarial.signers.notify(
                    envelope_id,
                    signer_id,
                    message="Lembrete: seu documento aguarda assinatura (sandbox).",
                )
                print("  Signer.notify: OK")
            except Exception as exc:
                # 429 ou restrições de conta — envelope.notify já disparou
                print(f"  Signer.notify ignorado: {type(exc).__name__}: {exc}")

    print("\nOK — envelope ativo e notificação enviada.")


if __name__ == "__main__":
    main()
