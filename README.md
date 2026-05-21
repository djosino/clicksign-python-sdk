# Clicksign Python SDK

Cliente Python para a [Clicksign API v3](https://developers.clicksign.com/) (JSON:API).

**Status:** beta — recursos notariais e administrativos principais, clientes sync/async, webhooks, paginação e hooks de observabilidade. Veja [`docs/SDK_CONTRACT.md`](docs/SDK_CONTRACT.md) e [`docs/SDK_ROADMAP.md`](docs/SDK_ROADMAP.md).

**Implementação de referência:** [`../clicksign-ruby-sdk`](../clicksign-ruby-sdk)

---

## Documentação

**Índice:** [`docs/README.md`](docs/README.md) — mapa por tema (contrato, roadmap, exemplos, observabilidade, paginação).

| Comece aqui | Também |
|------------|------|
| [`SDK_CONTRACT.md`](docs/SDK_CONTRACT.md) | [`SPEC.md`](docs/SPEC.md), [`WORKFLOW.md`](docs/WORKFLOW.md) |
| [`OBSERVABILITY.md`](docs/OBSERVABILITY.md) | [`PAGINATION.md`](docs/PAGINATION.md), [`TYPES.md`](docs/TYPES.md) |
| [`examples/`](docs/examples/) | [`ARCHITECTURE.md`](docs/ARCHITECTURE.md) |

### Superfície da API (`ClicksignClient`)

| Namespace | Resource | Import alternativo |
|-----------|----------|-------------------|
| `client.notarial.envelopes` | `Envelope` | `from clicksign import Envelope` |
| `client.notarial.documents` | `Document` | `from clicksign import Document` |
| `client.notarial.signers` | `Signer` | `from clicksign import Signer` |
| `client.notarial.requirements` | `Requirement` | `from clicksign import Requirement` |
| `client.notarial.bulk_requirements` | `BulkRequirement` | `from clicksign import BulkRequirement` |
| `client.notarial.signature_watchers` | `SignatureWatcher` | `from clicksign.resources.notarial.signature_watcher import SignatureWatcher` |
| — | `Event` (aninhado) | `Envelope.list_events(id)`, `Document.list_events(doc_id, envelope_id=…)`, `Event.create_for_document` |
| `client.webhooks` | `Webhook` | `from clicksign.resources.webhook import Webhook` |
| `client.users` | `User` | `from clicksign.resources.user import User` |
| `client.templates` / `template_fields` | `Template`, `TemplateField` | `from clicksign.resources.template import Template` |
| `client.memberships` / `groups` | `Membership`, `Group` | imports em `clicksign.resources.*` |
| `client.folders` | `Folder` | `from clicksign.resources.folder import Folder` |
| `client.access_control_lists` | `AccessControlList` | `from clicksign.resources.access_control_list import AccessControlList` |
| `client.envelope_bulk_creations` | `EnvelopeBulkCreation` | import direto do módulo |
| `client.acceptance_term.whatsapps` | `Whatsapp` | `from clicksign.resources.acceptance_term.whatsapp import Whatsapp` |
| `client.auto_signature.terms` | `Term` | `from clicksign.resources.auto_signature.term import Term` |

Endpoints sem resource dedicado: `client.raw_request()` + `client.deserialize()`.

---

## Requisitos

- Python >= 3.10
- Sem dependências de runtime (apenas stdlib)

Extras opcionais: `pip install clicksign[httpx]` para connection pooling e menor latência sob carga; `pip install clicksign[async]` para asyncio.

---

## Uso

O SDK suporta dois padrões principais. Ambos chamam a mesma API; escolha com base em como sua aplicação gerencia credenciais e concorrência.

### Configuração global (single tenant)

Configure uma vez na inicialização e importe as classes de resource diretamente. Ideal para scripts, workers com uma única API key por processo e protótipos rápidos.

```python
import clicksign
from clicksign import Envelope, Document

clicksign.configure(
    api_key="YOUR_API_KEY",
    environment="sandbox",  # or "production"
)

envelopes = Envelope.list()
envelope = Envelope.create(name="Contract", locale="pt-BR")
document = Document.create(envelope_id=envelope.id, filename="contract.pdf", content_base64="...")
```

Os hooks de instrumentação também são globais:

```python
clicksign.on_request(lambda payload: print(payload["method"], payload["path"]))
```

Log HTTP integrado:

```python
import clicksign

clicksign.log = "debug"  # or: clicksign.configure(..., log="info")
# export CLICKSIGN_LOG=debug

# Uses stdlib logger "clicksign"; Authorization is never logged.
```

Veja [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md) para hooks, níveis de logging, exemplos com structlog/OpenTelemetry/metrics e **como evitar PII** em handlers `on_error` customizados.

**Correlação:** passe `X-Correlation-Id` por chamada via `RequestOptions(headers=correlation_id("your-id"))` para vincular requisições do SDK ao seu web request ou job id. A API pode ecoar a correlação no suporte; use `error.request_id` de `X-Request-Id` em falhas para tickets de suporte da Clicksign.

### Cliente explícito (`ClicksignClient`)

Crie uma instância do cliente quando precisar de múltiplas API keys no mesmo processo, maior descobribilidade ou ausência de estado global.

```python
from clicksign import ClicksignClient

client = ClicksignClient(api_key="YOUR_API_KEY", environment="sandbox")

# Namespaced resources
envelopes = client.notarial.envelopes.list()
envelope = client.notarial.envelopes.create(name="Contract", locale="pt-BR")

# Shorthand alias
envelope = client.envelopes.retrieve(envelope.id)
envelope.update(name="Updated contract")

# Query chain (auto-pagination; per() max 50 — see docs/PAGINATION.md)
drafts = client.envelopes.filter(status="draft").per(20).to_list()

# Bulk operations (atomic requirements)
client.notarial.bulk_requirements.create(
    envelope.id,
    block=lambda ops: ops.add_agree(
        signer_id="...",
        document_id="...",
        role="sign",
    ),
)
```

Cada `ClicksignClient` possui seus próprios clientes HTTP e bulk. Passe um transport customizado se necessário:

```python
from clicksign import ClicksignClient, UrllibHTTPClient

client = ClicksignClient(
    api_key="YOUR_API_KEY",
    environment="sandbox",
    http_client=UrllibHTTPClient(proxy="http://proxy:8080"),
)
```

### HTTP transport e connection pool

**Padrão:** `UrllibHTTPClient` (apenas stdlib, **sem** connection pool — um handshake TCP/TLS por requisição). Adequado para scripts e baixo QPS.

**Alta concorrência** (aplicações web, workers com muitas chamadas de API por segundo): instale httpx e injete um cliente compartilhado:

```bash
pip install clicksign[httpx]
```

```python
from clicksign import ClicksignClient, HttpxHTTPClient

# One HttpxHTTPClient per process (or per worker) reuses connections
http = HttpxHTTPClient()
client = ClicksignClient(api_key="YOUR_API_KEY", environment="production", http_client=http)

# Global style
import clicksign
clicksign.configure(api_key="...", environment="production", http_client=http)
```

`AsyncClicksignClient` (`clicksign[async]`) também usa `httpx` com connection pool no event loop.

Trade-offs e mitigações: [`docs/examples/08-production-limitations.md`](docs/examples/08-production-limitations.md) · receita singleton: [`docs/examples/12-http-connection-pool.md`](docs/examples/12-http-connection-pool.md).

### Multi-tenant (thread-local)

Para aplicações web ou filas de jobs onde cada requisição/job usa uma API key diferente, use `Services` para vincular um cliente à thread atual sem o `configure()` global:

```python
from clicksign import Envelope, Services

tenant = Services(api_key="TENANT_API_KEY", environment="sandbox")

with tenant.use():
    Envelope.list()  # routed through this tenant's client
```

`Services.use()` define tanto o cliente HTTP quanto o cliente bulk para a thread. Prefira `ClicksignClient` diretamente ao rodar sob runtimes async/fiber onde o contexto thread-local pode não se propagar.

### Async (FastAPI, asyncio)

Instale o extra opcional: `pip install clicksign[async]` (requer `httpx`). A API permanece inalterada; o cliente executa HTTP não-bloqueante no seu event loop.

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

Não use `Services.use()` dentro do asyncio — passe um `AsyncClicksignClient` explícito. Operações atômicas bulk permanecem no cliente sync `ClicksignClient.bulk` por enquanto.

Sobrescritas por requisição (api key, headers, timeouts, `max_retries`) sem trocar de cliente. O número padrão de retries é **3** (`max_retries=0` desativa retries em uma única chamada):

```python
from clicksign import ClicksignClient, RequestOptions, correlation_id

client = ClicksignClient(api_key="DEFAULT_KEY", environment="sandbox")

client.notarial.envelopes.retrieve(
    "uuid",
    options={"api_key": "TENANT_KEY"},
)

client.envelopes.create(
    name="Contract",
    options=RequestOptions(
        headers=correlation_id("req-123"),  # or {"X-Correlation-Id": "req-123"}
        read_timeout=30.0,
    ),
)

client.envelopes.filter(status="draft").to_list(options={"api_key": "TENANT_KEY"})

# Critical path: no retries even if the client default is 3
client.envelopes.retrieve("uuid", options={"max_retries": 0})
```

Precedência: **options na chamada** sobrescrevem os padrões do cliente (thread-local e configuração global não são alterados).

### Endpoints não mapeados ou beta

Use `raw_request` para caminhos ainda não cobertos pelas classes de resource e, opcionalmente, desserialize:

```python
from clicksign import ClicksignClient, Envelope

client = ClicksignClient(api_key="YOUR_API_KEY", environment="sandbox")

raw = client.raw_request("get", "/beta/feature")
print(raw.status, raw.request_id, raw.body)

envelope = client.deserialize(raw, Envelope)
print(envelope.last_response.status)
```

Após qualquer chamada bem-sucedida, inspecione os metadados HTTP via `client.last_response`, `client.bulk_last_response` ou `resource.last_response` (`status`, `request_id`, headers de rate limit).

### Erros de validação estruturados

Em respostas 400/422, as exceções expõem o array `errors` completo do JSON:API:

```python
from clicksign.errors import ValidationError

try:
    client.envelopes.create(name="")
except ValidationError as err:
    print(err.message)          # first error detail (backward compatible)
    print(err.error_code)       # first error code
    print(err.source_pointer)   # e.g. /data/attributes/name
    for api_error in err.api_errors:
        print(api_error.pointer, api_error.detail)
```

Mapeie erros de campo em formulários usando `source.pointer` ou `source.parameter` de cada entrada em `err.errors` / `err.api_errors`.

### JSON:API sideload (`included`)

Solicite recursos relacionados em uma única chamada com `with_includes()` e acesse-os como atributos:

```python
envelopes = client.envelopes.with_includes("folder").to_list()
print(envelopes[0].folder.name)  # sideloaded Folder, no extra HTTP call
print(envelopes[0].included_resources)  # all entries from `included`
```

**Limitações:** apenas relacionamentos presentes em `included` são resolvidos (caso contrário `envelope.folder` é `None`); includes aninhados dependem do que a API retorna; tipos desconhecidos fazem fallback para `Resource` base.

### User-Agent e identificação da aplicação

Toda requisição inclui um header `User-Agent` identificando o SDK e o runtime Python. Aplicações host podem adicionar seu próprio identificador:

```python
import clicksign

clicksign.set_app_info("My CRM", "2.1.0", "https://example.com")
# User-Agent: clicksign-python/x.y.z Python/3.10.x My_CRM/2.1.0
```

Sobrescrita por cliente:

```python
from clicksign import AppInfo, ClicksignClient

client = ClicksignClient(api_key="...", app_info=AppInfo(name="Tenant", version="1.0"))
```

### Telemetria do provider (opt-in)

O SDK pode enviar métricas de latência anonimizadas para a Clicksign (sem API keys, sem corpos de requisição/resposta). Desativado por padrão até você fazer opt-in:

```python
clicksign.configure(enable_telemetry=True)

# opt-out
clicksign.configure(enable_telemetry=False)
# or
clicksign.set_enable_telemetry(False)
```

Endpoint customizado (staging): `configure(enable_telemetry=True, telemetry_url="https://sandbox.clicksign.com/sdk/telemetry/v1/events")`.

As métricas incluem versão do SDK, versão do Python, método HTTP, caminho normalizado (UUIDs mascarados), status e duração.

### Qual padrão usar?

| Padrão | Quando |
|---------|------|
| `configure()` + resources | Uma API key por processo; scripts; estilo legado |
| `ClicksignClient` | Múltiplas keys; dependências explícitas; código novo |
| `Services.use()` | Apps multi-tenant estilo Rails/Django/Celery (uma thread por requisição/job) |
| `HttpxHTTPClient` (compartilhado) | Alto QPS por worker; veja [connection pool](docs/examples/12-http-connection-pool.md) |

Veja [`docs/WORKFLOW.md`](docs/WORKFLOW.md) para um fluxo completo de assinatura e [`docs/examples/`](docs/examples/) para receitas específicas por cenário.

---

## Desenvolvimento

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src/
```
