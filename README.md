# Clicksign Python SDK

[![PyPI](https://img.shields.io/pypi/v/clicksign)](https://pypi.org/project/clicksign/)
[![CI](https://github.com/djosino/clicksign-python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/djosino/clicksign-python-sdk/actions)
[![Python](https://img.shields.io/pypi/pyversions/clicksign)](https://pypi.org/project/clicksign/)
[![License](https://img.shields.io/pypi/l/clicksign)](LICENSE)

Cliente Python para a [Clicksign API v3](https://developers.clicksign.com/) (JSON:API). Requer Python >= 3.10, sem dependências de runtime (apenas stdlib). Documentação detalhada em [`docs/`](docs/).

---

## Índice

- [Instalação](#instalação)
- [Configuração](#configuração)
- [Multi-conta](#multi-conta)
- [Timeouts, retry e instrumentação](#timeouts-retry-e-instrumentação)
- [Início rápido](#início-rápido)
- [Fluxo de assinatura (notarial)](#fluxo-de-assinatura-notarial)
- [Filtros, ordenação e paginação](#filtros-ordenação-e-paginação)
- [Outros recursos](#outros-recursos)
- [Tratamento de erros](#tratamento-de-erros)
- [Ambientes](#ambientes)
- [Async (FastAPI, asyncio)](#async-fastapi-asyncio)
- [HTTP transport e connection pool](#http-transport-e-connection-pool)
- [Limitações e produção](#limitações-e-produção)
- [Desenvolvimento](#desenvolvimento)

---

> **Fluxo completo:** [`docs/WORKFLOW.md`](docs/WORKFLOW.md) — envelope → documento → signatário → ativação passo a passo.

> **Examples:** [`docs/examples/`](docs/examples/) — receitas prontas para retry, webhooks, multi-tenant, observabilidade e connection pool.

> **Contrato do SDK:** [`docs/SDK_CONTRACT.md`](docs/SDK_CONTRACT.md) — timeouts, retry, JSON:API, erros e paginação.

> **Observabilidade:** [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md) — hooks, log, correlation id, structlog, OpenTelemetry, PII.

---

## Instalação

```bash
pip install clicksign
```

Extras opcionais:

```bash
pip install clicksign[httpx]   # connection pooling (alto QPS)
pip install clicksign[async]   # AsyncClicksignClient (requer httpx)
```

---

## Configuração

Dois padrões principais — escolha com base em como sua aplicação gerencia credenciais:

| Padrão | Quando usar |
|--------|-------------|
| `configure()` + resources | Uma API key por processo; scripts; workers simples |
| `ClicksignClient` | Múltiplas keys; dependências explícitas; código novo |

### Configuração global (single tenant)

```python
import clicksign
from clicksign import Envelope, Document

clicksign.configure(
    api_key="YOUR_API_KEY",
    environment="sandbox",  # or "production"
)

envelopes = Envelope.list()
envelope = Envelope.create(name="Contrato", locale="pt-BR")
document = Document.create(
    envelope_id=envelope.id,
    filename="contrato.pdf",
    content_base64="...",
)
```

### Cliente explícito (`ClicksignClient`)

```python
from clicksign import ClicksignClient

client = ClicksignClient(api_key="YOUR_API_KEY", environment="sandbox")

envelopes = client.notarial.envelopes.list()
envelope = client.notarial.envelopes.create(name="Contrato", locale="pt-BR")

# Alias direto (shorthand)
envelope = client.envelopes.retrieve(envelope.id)
envelope.update(name="Contrato atualizado")
```

---

## Multi-conta

Para apps multi-tenant onde cada requisição/job usa uma API key diferente, use `Services` para vincular um cliente à thread atual:

```python
from clicksign import Envelope, Services

tenant = Services(api_key="TENANT_API_KEY", environment="sandbox")

with tenant.use():
    Envelope.list()  # roteado pelo cliente deste tenant
```

`Services.use()` define cliente HTTP e bulk para a thread. Em runtime async/fiber, prefira `ClicksignClient` ou `AsyncClicksignClient` explícito — contexto thread-local pode não se propagar.

---

## Timeouts, retry e instrumentação

### Timeouts por requisição

```python
from clicksign import ClicksignClient, RequestOptions

client = ClicksignClient(api_key="YOUR_API_KEY", environment="sandbox")

client.envelopes.create(
    name="Contrato",
    options=RequestOptions(
        read_timeout=30.0,
        open_timeout=5.0,
    ),
)
```

Timeouts separados: `open_timeout` (TCP connect), `write_timeout` (envio do corpo), `read_timeout` (resposta).

### Retry

Padrão **3 retries** com full-jitter exponential backoff. Desative por chamada:

```python
client.envelopes.retrieve("uuid", options={"max_retries": 0})
```

`BulkRequirement.create` retenta apenas `TimeoutError` — operações atômicas não são idempotentes.

### Correlação de requisições

```python
from clicksign import RequestOptions, correlation_id

client.envelopes.retrieve(
    "uuid",
    options=RequestOptions(headers=correlation_id("req-123")),
)
```

Em falhas, use `error.request_id` (header `X-Request-Id`) para tickets de suporte da Clicksign.

### Hooks de instrumentação

```python
import clicksign

clicksign.on_request(lambda e: print(e["method"], e["path"], e["status"]))
clicksign.on_retry(lambda e: print(e["attempt"], e["wait_ms"]))
clicksign.on_error(lambda e: print(e["error"]))
```

Veja [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md) para exemplos com structlog, OpenTelemetry e Prometheus, e **como evitar PII** em handlers `on_error`.

### Log HTTP integrado

```bash
export CLICKSIGN_LOG=debug   # ou info, warn, error
```

```python
clicksign.configure(log="debug")
# Usa stdlib logger "clicksign"; header Authorization nunca é logado.
```

---

## Início rápido

```python
from clicksign import ClicksignClient

client = ClicksignClient(api_key="YOUR_API_KEY", environment="sandbox")

# Criar envelope
envelope = client.notarial.envelopes.create(name="Contrato NDA", locale="pt-BR")

# Adicionar documento
doc = client.notarial.documents.create(
    envelope_id=envelope.id,
    filename="nda.pdf",
    content_base64="...",
)

# Adicionar signatário
signer = client.notarial.signers.create(
    envelope_id=envelope.id,
    name="Ana Souza",
    email="ana@example.com",
    has_documentation=True,
)

# Requisito de assinatura (atomic)
client.notarial.bulk_requirements.create(
    envelope.id,
    block=lambda ops: ops.add_agree(
        signer_id=signer.id,
        document_id=doc.id,
        role="sign",
    ),
)

# Ativar envelope
envelope.update(status="running")
```

---

## Fluxo de assinatura (notarial)

### 1. Envelope

```python
envelope = client.notarial.envelopes.create(name="Contrato", locale="pt-BR")
envelope.update(deadline_at="2025-12-31T23:59:59Z")
```

### 2. Documento

```python
import base64

doc = client.notarial.documents.create(
    envelope_id=envelope.id,
    filename="contrato.pdf",
    content_base64=base64.b64encode(open("contrato.pdf", "rb").read()).decode(),
)
```

### 3. Signatário

```python
signer = client.notarial.signers.create(
    envelope_id=envelope.id,
    name="João Silva",
    email="joao@example.com",
    has_documentation=True,
    documentation="123.456.789-09",
)
```

### 4. Requisitos de assinatura (bulk atômico)

```python
client.notarial.bulk_requirements.create(
    envelope.id,
    block=lambda ops: (
        ops.add_agree(signer_id=signer.id, document_id=doc.id, role="sign"),
        ops.add_provide_evidence(signer_id=signer.id, document_id=doc.id, auth="email"),
    ),
)
```

### 5. Ativar

```python
envelope.update(status="running")
```

### 6. Monitorar eventos

```python
events = client.notarial.envelopes.retrieve(envelope.id)
# ou via webhook: docs/examples/03-webhooks.md
```

---

## Filtros, ordenação e paginação

```python
# QueryProxy chain
drafts = (
    client.envelopes
    .filter(status="draft")
    .order("-created_at")
    .per(20)
    .with_includes("folder")
    .to_list()
)

# Auto-paginação (itera todas as páginas)
for envelope in client.envelopes.filter(status="running"):
    print(envelope.id)

# page() + per() explícitos
page1 = client.envelopes.page(1).per(10).to_list()
```

`per()` máximo 50 — veja [`docs/PAGINATION.md`](docs/PAGINATION.md).

### JSON:API sideload (`included`)

```python
envelopes = client.envelopes.with_includes("folder").to_list()
print(envelopes[0].folder.name)  # sem chamada HTTP extra
```

---

## Outros recursos

| Namespace | Resource |
|-----------|----------|
| `client.notarial.envelopes` | `Envelope` |
| `client.notarial.documents` | `Document` |
| `client.notarial.signers` | `Signer` |
| `client.notarial.requirements` | `Requirement` |
| `client.notarial.bulk_requirements` | `BulkRequirement` |
| `client.notarial.signature_watchers` | `SignatureWatcher` |
| `client.webhooks` | `Webhook` |
| `client.users` | `User` |
| `client.templates` / `client.template_fields` | `Template`, `TemplateField` |
| `client.memberships` / `client.groups` | `Membership`, `Group` |
| `client.folders` | `Folder` |
| `client.access_control_lists` | `AccessControlList` |
| `client.envelope_bulk_creations` | `EnvelopeBulkCreation` |
| `client.acceptance_term.whatsapps` | `Whatsapp` |
| `client.auto_signature.terms` | `Term` |

Endpoints sem resource dedicado:

```python
raw = client.raw_request("get", "/beta/feature")
envelope = client.deserialize(raw, Envelope)
print(envelope.last_response.status)
```

### User-Agent e identificação da aplicação

```python
clicksign.set_app_info("My CRM", "2.1.0", "https://example.com")
# User-Agent: clicksign-python/x.y.z Python/3.10.x My_CRM/2.1.0
```

### Telemetria do provider (opt-in)

```python
clicksign.configure(enable_telemetry=True)
```

Envia métricas de latência anonimizadas (sem API keys nem corpos). Desativado por padrão.

---

## Tratamento de erros

```python
from clicksign.errors import (
    AuthenticationError,
    PermissionError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    TimeoutError,
)

try:
    client.envelopes.create(name="")
except ValidationError as err:
    print(err.message)          # primeiro detalhe (compatível)
    print(err.error_code)       # código do primeiro erro
    print(err.source_pointer)   # ex: /data/attributes/name
    for api_error in err.api_errors:
        print(api_error.pointer, api_error.detail)
except RateLimitError as err:
    print(err.rate_limit_reset)
except ServerError as err:
    if err.retryable:
        ...
```

| Exceção | Status HTTP |
|---------|-------------|
| `AuthenticationError` | 401 |
| `PermissionError` | 403 |
| `NotFoundError` | 404 |
| `ValidationError` | 400, 422 |
| `RateLimitError` | 429 |
| `ServerError` | 5xx |
| `TimeoutError` | timeout de rede |

---

## Ambientes

| Ambiente | Base URL |
|----------|----------|
| `sandbox` | `https://sandbox.clicksign.com/api/v3` |
| `production` | `https://app.clicksign.com/api/v3` |

```python
client = ClicksignClient(api_key="...", environment="production")
```

---

## Async (FastAPI, asyncio)

```python
import asyncio
from clicksign import AsyncClicksignClient

async def main():
    async with AsyncClicksignClient(api_key="YOUR_API_KEY", environment="sandbox") as client:
        envelopes = await client.notarial.envelopes.list()
        async for env in client.envelopes.filter(status="draft"):
            print(env.id)
        envelope = await client.envelopes.retrieve("uuid")
        await envelope.update_async(status="running")

asyncio.run(main())
```

Não use `Services.use()` dentro do asyncio — passe `AsyncClicksignClient` explícito por coroutine.

---

## HTTP transport e connection pool

**Padrão:** `UrllibHTTPClient` (stdlib, sem connection pool — um handshake TCP/TLS por requisição). Adequado para scripts e baixo QPS.

**Alto QPS:** instale `clicksign[httpx]` e injete um cliente compartilhado:

```python
from clicksign import ClicksignClient, HttpxHTTPClient

http = HttpxHTTPClient()  # um por processo / worker
client = ClicksignClient(api_key="...", environment="production", http_client=http)
```

`AsyncClicksignClient` usa httpx com connection pool no event loop.

Receita singleton: [`docs/examples/12-http-connection-pool.md`](docs/examples/12-http-connection-pool.md).

---

## Limitações e produção

- `UrllibHTTPClient` não reutiliza conexões — use `HttpxHTTPClient` sob carga.
- `Services.use()` usa `threading.local()` — incompatível com asyncio/trio.
- Operações bulk atômicas retentam apenas `TimeoutError` (não são idempotentes).
- Includes aninhados dependem do que a API retorna; tipos desconhecidos fazem fallback para `Resource` base.

Veja [`docs/examples/08-production-limitations.md`](docs/examples/08-production-limitations.md).

---

## Desenvolvimento

```bash
pip install -e ".[dev]"
pytest
pytest --cov=clicksign --cov-report=term-missing
ruff format .
ruff check .
mypy src/
```

---

## Licença

MIT — veja [LICENSE](LICENSE).
