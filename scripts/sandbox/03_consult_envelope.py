#!/usr/bin/env python3
"""Consulta envelope e listagens aninhadas no sandbox."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _config import get_client, load_last_run  # noqa: E402


def main() -> None:
    envelope_id = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not envelope_id:
        envelope_id = load_last_run().get("envelope_id", "")
    if not envelope_id:
        print("Uso: python 03_consult_envelope.py <envelope_id>", file=sys.stderr)
        sys.exit(1)

    client = get_client()
    last = load_last_run()

    with client.use():
        print(f"=== Envelope {envelope_id} ===")
        envelope = client.notarial.envelopes.retrieve(envelope_id)
        print(
            f"  name={envelope.name!r} status={envelope.status!r} locale={envelope.locale!r}"
        )

        print("\n--- Documentos (envelope.list_documents) ---")
        for doc in client.notarial.envelopes.list_documents(envelope_id):
            print(f"  {doc.id}  filename={doc.filename!r} status={doc.status!r}")

        print("\n--- Signatários (envelope.list_signers) ---")
        for signer in client.notarial.envelopes.list_signers(envelope_id):
            print(f"  {signer.id}  name={signer.name!r} email={signer.email!r}")

        print("\n--- Requisitos (envelope.list_requirements) ---")
        for req in client.notarial.envelopes.list_requirements(envelope_id):
            print(
                f"  {req.id}  action={req.action!r} role={getattr(req, 'role', None)!r}"
            )

        print("\n--- Document.list_for_envelope (atalho) ---")
        for doc in client.notarial.documents.list_for_envelope(envelope_id):
            print(f"  Document.list_for_envelope → {doc.id}")

        print("\n--- Eventos do envelope ---")
        events = client.notarial.envelopes.list_events(envelope_id)
        print(f"  {len(events)} evento(s)")
        for ev in events[:5]:
            print(f"    {ev.id}  name={getattr(ev, 'name', None)!r}")

        doc_id = last.get("document_id")
        if not doc_id:
            docs = client.notarial.envelopes.list_documents(envelope_id)
            doc_id = docs[0].id if docs else ""
        if doc_id:
            doc_events = client.notarial.documents.list_events(
                doc_id, envelope_id=envelope_id
            )
            print(f"  eventos do documento {doc_id}: {len(doc_events)}")

    print("\nOK.")


if __name__ == "__main__":
    main()
