# Vários clientes (multi-conta / multi-tenant)

Quando cada conta ou job usa **token e ambiente diferentes**, evite depender só de `clicksign.configure()` global. Use `Services` (thread-local) ou `ClicksignClient` explícito.

---

## Dois clientes no mesmo processo

```python
import clicksign
from clicksign import ClicksignClient, Envelope, Services

clicksign.configure(
    api_key="default-key",
    environment="sandbox",
)

prod = Services(api_key="TOKEN_EMPRESA_A", environment="production", max_retries=3)
sandbox = Services(api_key="TOKEN_EMPRESA_B", environment="sandbox", max_retries=1)

with prod.use():
    Envelope.create(name="Contrato — Empresa A")

with sandbox.use():
    Envelope.filter(status="draft").to_list()
```

Dentro de cada `use`, class methods de `Resource` usam o client daquele contexto (`Authorization` do tenant).

---

## Django / Flask (sync): um client por tenant

```python
from clicksign import ClicksignClient, Services

class Tenant:
    def __init__(self, api_key: str, environment: str):
        self._service = Services(
            api_key=api_key,
            environment=environment,
            max_retries=2,
        )

    @property
    def clicksign(self) -> Services:
        return self._service


def create_envelope(tenant: Tenant, name: str):
    with tenant.clicksign.use():
        from clicksign import Envelope
        return Envelope.create(name=name, locale="pt-BR")
```

Prefira **`ClicksignClient` por tenant** se quiser injeção explícita sem thread-local:

```python
def client_for(tenant) -> ClicksignClient:
    return ClicksignClient(
        api_key=tenant.api_key,
        environment=tenant.environment,
    )

client_for(tenant).envelopes.create(name="...")
```

---

## Celery: token por task

```python
@celery.task
def sync_envelopes(tenant_id: str):
    tenant = load_tenant(tenant_id)
    with tenant.clicksign_service.use():
        from clicksign import Envelope
        for envelope in Envelope.filter(status="running"):
            sync_one(envelope)
```

Cada worker thread tem seu próprio `threading.local` — jobs paralelos de tenants diferentes não misturam tokens.

---

## FastAPI / asyncio

**Não use** `Services.use()` no event loop. Use `AsyncClicksignClient` por app ou por request scope:

```python
from clicksign import AsyncClicksignClient

async def get_client(tenant_id: str) -> AsyncClicksignClient:
    tenant = await load_tenant(tenant_id)
    return AsyncClicksignClient(api_key=tenant.api_key, environment=tenant.environment)
```

Ver [08-production-limitations.md](08-production-limitations.md).

---

## Blocos aninhados

`use` restaura o client anterior ao sair:

```python
suporte = Services(api_key=support_token, environment="production")
cliente = Services(api_key=client_token, environment="production")

with suporte.use():
    # token suporte
    with cliente.use():
        # token cliente
        pass
    # volta suporte
```

Exceções no bloco interno ainda restauram o contexto no `finally`.

---

## HTTP direto (`Client` / `raw_request`)

Sem passar por class methods de `Resource`:

```python
from clicksign import Client

client_a = Client(
    api_key="TOKEN_A",
    base_url="https://app.clicksign.com/api/v3",
    open_timeout=2.0,
    read_timeout=10.0,
    write_timeout=10.0,
    max_retries=2,
    instrumentation=clicksign.instrumentation,
)
client_a.get("/envelopes", params={"filter[status]": "draft"})
```

| API | Isolamento |
|-----|------------|
| `Services.use()` + resources | Thread-local automático |
| `ClicksignClient` / `Client` | Você guarda a instância |

---

## Bulk e config global

`client.notarial.bulk_requirements` usa o `BulkOperationsClient` criado junto com `ClicksignClient`. Com `Services` + resources, o bulk memoizado global pode divergir do tenant no `use` — em multi-tenant crítico, use `ClicksignClient(api_key=tenant...)` para alinhar HTTP e bulk.

---

## Escolha rápida

| Cenário | Abordagem |
|---------|-----------|
| Um token por app | `configure()` |
| SaaS sync (Django, Celery) | `Services.use()` por request/task |
| FastAPI / asyncio | `AsyncClicksignClient` |
| Dois tokens no mesmo script | Dois `Services` ou dois `ClicksignClient` |
| Alta QPS | `HttpxHTTPClient` compartilhado — [12-http-connection-pool.md](12-http-connection-pool.md) |

---

## Referência

- Código: `src/clicksign/services.py`, `src/clicksign/client_scope.py`
- Retries: [01-retries.md](01-retries.md)
