#!/usr/bin/env python3
"""
Cria envelope + documento + signatário + requisitos no sandbox (permanece em draft).

Não ativa nem notifica — use 03_consult_envelope.py depois.
"""

from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _config import get_client, pdf_content_base64, save_last_run  # noqa: E402


def main() -> None:
    client = get_client()
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    suffix = uuid.uuid4().hex[:8]

    print("1/4 Criando envelope...")
    envelope = client.notarial.envelopes.create(
        name=f"SDK sandbox {stamp}",
        locale="pt-BR",
        auto_close=True,
    )
    print(f"   envelope.id = {envelope.id}  status={envelope.status}")

    print("2/4 Criando documento...")
    doc = client.notarial.documents.create(
        envelope.id,
        filename=f"sandbox-{stamp}.pdf",
        content_base64=pdf_content_base64(),
    )
    print(f"   document.id = {doc.id}  filename={doc.filename}")

    print("3/4 Criando signatário...")
    email = f"sandbox+{suffix}@mailinator.com"
    signer = client.notarial.signers.create(
        envelope.id,
        name="Maria Sandbox Silva",
        email=email,
        has_documentation=False,
    )
    print(f"   signer.id = {signer.id}  email={email}")

    print("4/4 Criando requisitos (bulk)...")
    bulk = client.notarial.bulk_requirements.create(
        envelope.id,
        block=lambda ops: (
            ops.add_agree(signer_id=signer.id, document_id=doc.id, role="sign"),
            ops.add_provide_evidence(
                signer_id=signer.id,
                document_id=doc.id,
                auth="email",
            ),
        ),
    )
    if bulk.success():
        print("   bulk: sucesso")
    else:
        print("   bulk: falhas parciais")
        for f in bulk.failures:
            print(f"     - slot {f.index} op={f.op} errors={f.errors}")
        sys.exit(1)

    # Reconsulta via API
    envelope2 = client.notarial.envelopes.retrieve(envelope.id)
    print(f"\nEnvelope após bulk: status={envelope2.status}")

    save_last_run(
        {
            "envelope_id": envelope.id,
            "document_id": doc.id,
            "signer_id": signer.id,
        }
    )

    print("\nPróximo passo:")
    print(f"  python scripts/sandbox/03_consult_envelope.py {envelope.id}")
    print("  # ou sem argumento para usar .last_run.json")


if __name__ == "__main__":
    main()
