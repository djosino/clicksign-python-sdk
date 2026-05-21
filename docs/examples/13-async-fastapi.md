# FastAPI e asyncio — `AsyncClicksignClient`

Receita para apps async: lifespan, dependência por request e fluxo notarial mínimo.

**Requisito:** `pip install clicksign-python-sdk[async]` (httpx).

---

## Regras

| Faça | Evite |
|------|--------|
| `AsyncClicksignClient` explícito (app state ou `Depends`) | `Services.use()` no event loop |
| `async with client` ou `await client.aclose()` no shutdown | Cliente novo por request sem necessidade |
| `await envelope.update_async(...)` em instâncias async | `envelope.update()` bloqueante no loop |
| `Signer.notify(envelope_id, signer_id, ...)` | `signer.notify(...)` sem ids |

Ver também: [08-production-limitations.md](08-production-limitations.md) · [12-http-connection-pool.md](12-http-connection-pool.md).

---

## Lifespan (um client por processo)

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from clicksign import AsyncClicksignClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncClicksignClient(
        api_key=settings.clicksign_api_key,
        environment="production",
    )
    app.state.clicksign = client
    try:
        yield
    finally:
        await client.aclose()

app = FastAPI(lifespan=lifespan)
```

`AsyncClicksignClient` já usa `httpx.AsyncClient` com pool no event loop — um client por worker é o padrão recomendado.

---

## Dependência FastAPI

```python
from fastapi import Depends, Request
from clicksign import AsyncClicksignClient

def get_clicksign(request: Request) -> AsyncClicksignClient:
    return request.app.state.clicksign
```

Multi-tenant (client por request):

```python
async def get_tenant_clicksign(tenant_id: str) -> AsyncClicksignClient:
    tenant = await load_tenant(tenant_id)
    return AsyncClicksignClient(
        api_key=tenant.clicksign_api_key,
        environment=tenant.environment,
    )
```

Feche com `await client.aclose()` ao final do request se criar instância descartável.

---

## Fluxo notarial (async)

```python
from clicksign import AsyncClicksignClient
from clicksign.resources.notarial.signer import Signer

async def run_flow(client: AsyncClicksignClient) -> None:
    envelope = await client.notarial.envelopes.create(name="Contrato", locale="pt-BR")

    doc = await client.notarial.documents.create(
        envelope.id,
        filename="contrato.pdf",
        content_base64="data:application/pdf;base64,...",
    )

    signer = await client.notarial.signers.create(
        envelope.id,
        name="Maria Silva",
        email="maria@example.com",
    )

    bulk = await client.notarial.bulk_requirements.create(
        envelope.id,
        block=lambda ops: (
            ops.add_agree(signer_id=signer.id, document_id=doc.id, role="sign"),
            ops.add_provide_evidence(
                signer_id=signer.id, document_id=doc.id, auth="email"
            ),
        ),
    )
    if not bulk.success():
        raise RuntimeError("bulk incompleto")

    await envelope.update_async(status="running")
    # ou: await client.notarial.envelopes.activate(envelope.id)

    Signer.notify(envelope.id, signer.id, message="Documento disponível para assinatura.")
```

---

## Listar e paginar

```python
# Uma página explícita (não auto-pagina todas)
first = await client.envelopes.filter(status="draft").page(2).per(10).first()

# Todas as páginas
async for envelope in client.envelopes.filter(status="draft"):
    print(envelope.id)
```

`page(n)` com `.first()` / `.last()` respeita o número da página; `.to_list()` na auto-paginação **reinicia** em `page=1` — ver [`../PAGINATION.md`](../PAGINATION.md).

---

## Referência

- README (seção Async) · [04-multi-client.md](04-multi-client.md)
- Contrato: [`../SDK_CONTRACT.md`](../SDK_CONTRACT.md)
- Fluxo sync detalhado: [`../WORKFLOW.md`](../WORKFLOW.md)
