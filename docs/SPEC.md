# Especificação técnica — Clicksign Python SDK

**Versão do documento:** 3.0 (Python)  
**Fonte:** [Clicksign API v3](https://developers.clicksign.com/) (JSON:API)  
**Contrato comportamental:** [`SDK_CONTRACT.md`](SDK_CONTRACT.md)  
**Fluxo de assinatura:** [`WORKFLOW.md`](WORKFLOW.md)

---

## 1. Visão geral

O **clicksign** é o cliente Python oficial da API REST Clicksign v3. Abstrai HTTPS, JSON:API, autenticação, paginação, retry, bulk atômico e webhooks HMAC.

**Problema que resolve:**

- Comunicação com `sandbox.clicksign.com/api/v3` e `app.clicksign.com/api/v3`
- Respostas materializadas em instâncias `Resource` com properties tipadas
- API fluente: `Envelope.filter(...)`, `.list()`, `.create()`, `.retrieve()`, `.update()`, `.delete()`
- Exceções HTTP padronizadas (`clicksign.errors`)

**Personas:**

| Persona | Uso típico |
|--------|------------|
| Desenvolvedor backend Python | FastAPI, Django, Celery, scripts |
| Integrador de assinatura | Envelope → documento → signatário → requisitos → ativação |
| Operador de webhooks | `construct_event` + validação HMAC no servidor |
| Admin de conta | Users, groups, memberships, templates |

---

## 2. Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│  Aplicação Python (FastAPI, Django, jobs, scripts)          │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
   ClicksignClient    configure()      AsyncClicksignClient
   (facade)           + Resource       (asyncio + httpx)
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │  Client / AsyncClient     │
              │  BulkOperationsClient     │
              └─────────────┬─────────────┘
                            │
              ┌─────────────┴─────────────┐
              │  json_api (parser,        │
              │  serializer, bulk ops)    │
              └─────────────┬─────────────┘
                            │
              ┌─────────────┴─────────────┐
              │  _http/transport          │
              │  (Urllib / Httpx)         │
              └─────────────┬─────────────┘
                            │
              ┌─────────────┴─────────────┐
              │  Clicksign API v3         │
              └───────────────────────────┘
```

| Camada | Módulos |
|--------|---------|
| Entrada | `clicksign.configure()`, `ClicksignClient`, `AsyncClicksignClient` |
| Facade | `clicksign_client.py`, `_async/clicksign_client.py` |
| HTTP | `client.py`, `_async/client.py`, `_http/executor.py` |
| Resources | `resource.py`, `resources/**`, `bound_resource.py` |
| JSON:API | `json_api/parser.py`, `serializer.py`, `bulk_operations_client.py` |
| Erros | `errors.py`, `error_handler.py` |
| Webhooks | `webhook.py` (`verify_signature`, `construct_event`) |

Diagrama detalhado: [`ARCHITECTURE.md`](ARCHITECTURE.md).

### Autenticação

Header `Authorization: <token>` **sem** prefixo `Bearer`.

```python
import os
from clicksign import ClicksignClient

client = ClicksignClient(
    api_key=os.environ["CLICKSIGN_API_KEY"],
    environment="sandbox",
)
```

Legado global:

```python
import clicksign
from clicksign.resources.notarial.envelope import Envelope

clicksign.configure(api_key="...", environment="sandbox")
```

### Stack

| Tecnologia | Papel |
|------------|-------|
| Python | >= 3.10 |
| stdlib | HTTP default (`UrllibHTTPClient`) |
| httpx (extra) | Pool + `AsyncClicksignClient` |
| pytest | Testes com transport mockado |

---

## 3. Mapa de resources (API v3)

### Namespacing no SDK Python

| Facade / módulo | Classes | Rotas |
|-----------------|---------|-------|
| `client.notarial.*` | `Envelope`, `Document`, `Signer`, `Requirement`, `BulkRequirement`, `SignatureWatcher` | `/envelopes/...` |
| `clicksign.resources.notarial.event` | `Event` (somente nested) | `/envelopes/.../events`, `/documents/.../events` |
| `client.auto_signature.terms` | `Term` | `/auto_signature/terms` |
| `client.acceptance_term.whatsapps` | `Whatsapp` | `/acceptance_term/whatsapps` |
| `client.webhooks`, `client.users`, … | `Webhook`, `User`, `Membership`, `Group`, `Template`, `TemplateField`, `Folder`, `EnvelopeBulkCreation`, `AccessControlList` | top-level |

Import direto: `from clicksign import Envelope, Document, Signer` (notarial exportados no pacote raiz).

---

### 3.1 Envelopes

**Base:** `/api/v3/envelopes`

| Método | SDK Python | HTTP |
|--------|------------|------|
| Listar | `Envelope.list()` ou `client.notarial.envelopes.list()` | `GET /envelopes` |
| Filtrar | `Envelope.filter(status="draft").to_list()` | `GET /envelopes?filter[...]` |
| Buscar | `Envelope.retrieve(id)` | `GET /envelopes/:id` |
| Criar | `Envelope.create(name=..., locale=...)` | `POST /envelopes` |
| Atualizar | `envelope.update(status="running")` | `PATCH /envelopes/:id` |
| Deletar | `envelope.delete()` | `DELETE /envelopes/:id` |
| Ativar | `Envelope.activate(id)` | `POST /envelopes/:id/activate` |

**Sub-resources:**

- `Envelope.list_events(envelope_id, **filters)`
- `Envelope.list_documents` / `list_signers` / `list_requirements` / `list_signature_watchers`
- `envelope.notify(message=..., subject=...)`

---

### 3.2 Documentos

**Base (nested):** `/envelopes/:envelope_id/documents`

| Método | SDK Python | HTTP |
|--------|------------|------|
| Listar | `Document.list_for_envelope(envelope_id)` | `GET /envelopes/:id/documents` |
| Buscar | `Document.retrieve(doc_id, envelope_id=...)` | `GET /envelopes/:eid/documents/:id` |
| Criar | `Document.create(envelope_id, filename=..., content_base64=...)` | `POST /envelopes/:eid/documents` |
| Atualizar | `document.update(**attrs)` | `PATCH ...` |
| Deletar | `document.delete()` | `DELETE ...` |

**Facade:** `client.notarial.documents.create(envelope.id, ...)` — **primeiro argumento posicional** é o id do envelope.

**Eventos:**

- `Document.list_events(document_id, envelope_id=...)`
- `Event.create_for_document(envelope_id, document_id, name=..., data=...)`

---

### 3.3 Signatários

**Base (nested):** `/envelopes/:envelope_id/signers`

| Método | SDK Python | HTTP |
|--------|------------|------|
| Listar | `Signer.list_for_envelope(envelope_id)` | `GET /envelopes/:id/signers` |
| Criar | `Signer.create(envelope_id, name=..., email=...)` | `POST ...` |
| Deletar | `signer.delete()` | `DELETE ...` |

`Signer.update` não implementado (API não expõe PATCH).

**Facade:** `client.notarial.signers.create(envelope.id, ...)`.

---

### 3.4 Requisitos

| Método | SDK Python | HTTP |
|--------|------------|------|
| Listar (envelope) | `Envelope.list_requirements(envelope_id, **filters)` | `GET /envelopes/:id/requirements` |
| Listar (documento) | `Requirement.list_for_document(document_id, **filters)` | relacionamento |
| Listar (signatário) | `Requirement.list_for_signer(signer_id, **filters)` | relacionamento |
| Criar | `Requirement.create(envelope_id, relationships=rels, action=..., role=..., auth=...)` | `POST ...` |
| Buscar | `Requirement.retrieve(id, envelope_id=...)` | `GET ...` |
| Atualizar / deletar | instância | `PATCH` / `DELETE` |

**Bulk:** `BulkRequirement.create(envelope_id, block=lambda ops: ...)` → `POST /envelopes/:id/bulk_requirements`

```python
response = client.notarial.bulk_requirements.create(
    envelope.id,
    block=lambda ops: (
        ops.add_agree(signer_id=signer.id, document_id=document.id, role="sign"),
        ops.add_provide_evidence(signer_id=signer.id, document_id=document.id, auth="email"),
        ops.add_rubricate(signer_id=signer.id, document_id=document.id, pages="all"),
        ops.remove(requirement_id=old_id),
    ),
)
if response.success():
    ...
else:
    for f in response.failures:
        print(f.index, f.op, f.errors)
```

Detalhes: [`examples/02-bulk-requirements.md`](examples/02-bulk-requirements.md).

---

### 3.5 Signature watchers

Nested em envelope — `SignatureWatcher.list_for_envelope`, `create`, `retrieve`, `delete`.

---

### 3.6 Webhooks

**Base:** `/webhooks` — CRUD via `client.webhooks` ou `Webhook`.

Validação de callback: `clicksign.construct_event(body, signature, secret)` — [`examples/03-webhooks.md`](examples/03-webhooks.md).

---

### 3.7–3.16 Admin e outros

| Resource | Facade | Notas |
|----------|--------|-------|
| `User` | `client.users` | `User.me()` |
| `Membership` | `client.memberships` | `Membership.filter_for_user(user_id)` |
| `Group` | `client.groups` | |
| `Template` / `TemplateField` | `client.templates`, `template_fields` | |
| `Folder` | `client.folders` | |
| `EnvelopeBulkCreation` | `client.envelope_bulk_creations` | create only |
| `AccessControlList` | `client.access_control_lists` | create / destroy |
| `Term` | `client.auto_signature.terms` | |
| `Whatsapp` | `client.acceptance_term.whatsapps` | |

Endpoints sem classe: `client.raw_request()` + `client.deserialize()`.

---

## 4. Mapeamento de erros

`error_handler` converte status HTTP em exceções antes de retornar ao resource.

| HTTP | Exceção Python |
|------|----------------|
| 401, 403 | `AuthenticationError` |
| 404 | `NotFoundError` |
| 400, 422 | `ValidationError` |
| 409 | `ConflictError` |
| 429 | `RateLimitError` |
| 5xx | `ServerError` |
| Rede / timeout | `TimeoutError` |

Todas herdam de `ClicksignError`. Atributos úteis: `message`, `request_id`, `api_errors`, `retryable`.

```python
from clicksign import ValidationError, RateLimitError

try:
    envelope.update(status="running")
except ValidationError as exc:
    print(exc.api_errors)
```

---

## 5. Convenções de implementação

### Classe Resource

```python
from clicksign.resource import Resource
from clicksign.types._attrs import str_attr

class Envelope(Resource):
    resource_type = "envelopes"
    endpoint = "/envelopes"

    @property
    def name(self) -> str | None:
        return str_attr(self, "name")

    @classmethod
    def create(cls, folder_id: str | None = None, **attrs) -> Envelope:
        rels = None
        if folder_id:
            rels = {"folder": {"data": {"type": "folders", "id": folder_id}}}
        return super().create(rels, **attrs)
```

### Nested lists

```python
@classmethod
def list_events(cls, envelope_id: str, **kwargs) -> list[Event]:
    return cls.nested_list(envelope_id, "events", as_class=Event, params=...)
```

### Nomenclatura

| Usar | Não usar |
|------|----------|
| `list` | `index`, `all` |
| `retrieve` | `get`, `find` |
| `create` | `new`, `build` |
| `delete` | `destroy` |

### `resource_type` e `endpoint`

- `resource_type` — tipo JSON:API (`"envelopes"`)
- `endpoint` — path base (`"/envelopes"` ou `"/auto_signature/terms"`)

### Tipagem

TypedDicts em `clicksign.types` — ver [`TYPES.md`](TYPES.md). Gerador: `scripts/generate_resource_types.py`.

---

## 6. Estrutura do repositório

```
src/clicksign/
  __init__.py              # exports, configure()
  client.py                # HTTP sync
  clicksign_client.py      # facade
  resource.py              # CRUD, QueryProxy
  bound_resource.py
  errors.py
  webhook.py
  _http/transport.py       # UrllibHTTPClient, HttpxHTTPClient
  _http/executor.py
  _async/                  # AsyncClient, AsyncClicksignClient
  json_api/
  resources/
    notarial/
    auto_signature/
    acceptance_term/
    webhook.py, user.py, ...

tests/clicksign/
docs/
```

---

## 7. Referências

| Documento | Conteúdo |
|-----------|----------|
| [`SDK_CONTRACT.md`](SDK_CONTRACT.md) | Retry, timeouts, bulk, paginação |
| [`SDK_TEST_MATRIX.md`](SDK_TEST_MATRIX.md) | Testes comportamentais |
| [`WORKFLOW.md`](WORKFLOW.md) | Tutorial assinatura |
| [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) | Erros comuns |
| API oficial | https://developers.clicksign.com/ |
