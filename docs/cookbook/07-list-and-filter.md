# List vs filter — consultas

Dois jeitos de listar recursos na API. Contratos **diferentes** de propósito.

---

## Regra rápida

| Precisa de | Use | Retorno |
|------------|-----|---------|
| Primeira página, sem filtros na chain | `.list()` | `list[Resource]` |
| Filtros, ordenação, página, includes, auto-pagination | `.filter(...)` | `QueryProxy` até o terminal |

**Não use** `list` com filtros — use `filter`.

---

## `list` — primeira página simples

```python
from clicksign import ClicksignClient

client = ClicksignClient(api_key="...", environment="sandbox")
hooks = client.webhooks.list()
print(hooks[0].callback_endpoint)
```

Uma requisição GET na collection (paginação padrão da API).

---

## `filter` — query chainable

```python
# Materializar tudo (auto-pagination)
drafts = client.envelopes.filter(status="draft").to_list()

# Chain
running = (
    client.envelopes.filter(status="running", name="Contrato")
    .with_includes("folder")
    .order("-created_at")
    .per(20)
    .to_list()
)

# Atalhos (uma página ou agregado)
client.envelopes.filter(status="draft").first()
client.envelopes.filter(status="draft").count()

# Iterator (todas as páginas)
for envelope in client.envelopes.filter(status="running"):
    process(envelope)
```

Ver paginação: [`../PAGINATION.md`](../PAGINATION.md).

---

## Equivalências

| Evitar | Preferir |
|--------|----------|
| `Envelope.list(status="draft")` | `Envelope.filter(status="draft").to_list()` |

Com `ClicksignClient`: `client.envelopes.filter(...).to_list()`.

---

## Listagens aninhadas

Métodos como `Envelope.list_documents(envelope_id)` são rotas aninhadas — não passam por `filter` da collection raiz. Ver [`SPEC.md`](../SPEC.md).

---

## Referência

- README · Paginação: [`PAGINATION.md`](../PAGINATION.md)
- Arquitetura: [`ARCHITECTURE.md`](../ARCHITECTURE.md)
