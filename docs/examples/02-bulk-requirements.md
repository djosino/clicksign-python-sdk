# Bulk requirements

Cria ou remove vários requisitos de assinatura em **uma** requisição (`POST /envelopes/:id/bulk_requirements`). Use quando o setup do signatário no documento já está definido e o envelope está em **`draft`**.

---

## Setup completo em uma chamada

```python
import os
import clicksign
from clicksign.resources.notarial.bulk_requirement import BulkRequirement

clicksign.configure(api_key=os.environ["CLICKSIGN_API_KEY"], environment="sandbox")

# envelope, document e signer já criados (status draft)
response = BulkRequirement.create(
    envelope.id,
    block=lambda ops: (
        ops.add_agree(signer_id=signer.id, document_id=document.id, role="sign"),
        ops.add_provide_evidence(
            signer_id=signer.id,
            document_id=document.id,
            auth="email",
        ),
        ops.add_rubricate(
            signer_id=signer.id,
            document_id=document.id,
            pages="all",
        ),
    ),
)
```

---

## Tratar sucesso parcial (`atomic:results`)

A API pode responder com HTTP 200 e slots com erro — **sem** lançar exceção. Inspecione `response.success()` e `response.failures`:

```python
if response.success():
    for req in response.requirements:
        print(f"OK: {req.id} ({req.action})")
else:
    for failure in response.failures:
        print(f"Falha no slot {failure.index} op={failure.op}: {failure.errors}")
    # abortar ativação, compensar (rollback manual), alertar operador
```

Cada `failure` expõe `index`, `op`, `errors` e `raw` (slot bruto da API).

---

## Remover e adicionar no mesmo bulk

```python
response = BulkRequirement.create(
    envelope.id,
    block=lambda ops: (
        ops.remove(requirement_id=requisito_antigo.id),
        ops.add_agree(signer_id=signer.id, document_id=document.id, role="sign"),
    ),
)
```

---

## Rubrica em campo específico

```python
ops.add_rubricate(
    signer_id=signer.id,
    document_id=document.id,
    rubric_field="campo_rubrica_1",
    kind="initials",  # opcional: initials | manuscript
)
```

É obrigatório informar `pages` **ou** `rubric_field`.

---

## Erro no envelope inteiro (422)

Quando a API devolve erros **top-level** (sem `atomic:results`), o SDK lança `ValidationError`:

```python
from clicksign import ValidationError

try:
    BulkRequirement.create(
        envelope.id,
        block=lambda ops: ops.add_agree(
            signer_id=signer.id,
            document_id=document.id,
            role="sign",
        ),
    )
except ValidationError as exc:
    print(exc)
    print(exc.response_body)
```

---

## Bulk vs requirement individual

| | `Requirement.create` | `BulkRequirement.create` |
|--|----------------------|--------------------------|
| Chamadas HTTP | 1 por requisito | 1 para N operações |
| Falha parcial | Exceção por request | `response.failures` por slot |
| Retry em 5xx / 429 | Sim (`Client`) | Não — só timeout de rede no bulk client |
| Bloco obrigatório | Não | Sim (`TypeError` sem `block`) |

---

## Ativar o envelope depois do bulk

Só ative quando a política de negócio permitir (ex.: todos os slots OK):

```python
if response.success():
    envelope.update(status="running")
```

---

## Referência

- README: [Requisitos — operações em lote](../../README.md)
- Implementação: `src/clicksign/resources/notarial/bulk_requirement.py`, `src/clicksign/json_api/operations.py`
