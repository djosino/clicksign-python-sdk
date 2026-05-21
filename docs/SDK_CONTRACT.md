# Clicksign SDK Contract — Especificação Agnóstica de Linguagem

**Versão:** 1.0
**Fonte:** Clicksign API v3 (JSON:API 1.1)
**Implementação:** este repositório (`clicksign` no PyPI)

Este documento define o **contrato comportamental** do SDK Python. Implementações em outras linguagens devem preservar o mesmo comportamento observável (HTTP, retry, erros, bulk, paginação).
Mapa de classes e rotas: [`SPEC.md`](SPEC.md).

---

## 1. Autenticação

- Header: `Authorization: <token>` — **SEM** prefixo `Bearer`, sem prefixo `Token`, token puro
- Header: `Content-Type: application/vnd.api+json`
- Header: `Accept: application/vnd.api+json`
- Token vem de `Configuration.api_key`

## 2. URLs base

| Ambiente | URL |
|-------------|-----|
| Produção  | `https://app.clicksign.com/api/v3` |
| Sandbox     | `https://sandbox.clicksign.com/api/v3` |

Padrão: produção. Atalho: `config.environment = 'sandbox'` define a URL automaticamente.
String de ambiente desconhecida lança `ValueError` (ou equivalente).

## 3. Configuração

Objeto de configuração único, definido uma vez na inicialização. Atributos:

| Atributo | Tipo | Padrão | Descrição |
|-----------|------|---------|-------------|
| `api_key` | str | None | Token da API |
| `base_url` | str | URL de produção | URL base completa |
| `open_timeout` | float | 2.0 | Timeout de conexão TCP (segundos) |
| `read_timeout` | float | 10.0 | Timeout de leitura (segundos) |
| `write_timeout` | float | 10.0 | Timeout de escrita (segundos) |
| `max_retries` | int | 3 | Tentativas de retry (0 = sem retry) |
| `logger` | Logger | None | Logger opcional para erros de callback |

O atalho `environment=` define `base_url` a partir da tabela acima.

**Thread safety:** não é seguro para acesso concorrente inicial. Deve ser configurado uma vez antes de as threads serem criadas.

## 4. Formato de Request / Response

### Corpo do request (POST, PATCH)

Documento JSON:API:

```json
{
  "data": {
    "type": "envelopes",
    "attributes": { "name": "Contract" },
    "relationships": {
      "folder": { "data": { "type": "folders", "id": "uuid" } }
    }
  }
}
```

- Omita `id` na criação
- Omita a chave `relationships` quando vazia (não `"relationships": {}`)
- Inclua `id` na atualização (PATCH)

### Parsing do response

```json
{
  "data": { "id": "uuid", "type": "envelopes", "attributes": {}, "relationships": {} },
  "included": [],
  "links": { "next": "url-or-null" },
  "meta": {}
}
```

- `data` pode ser um objeto único ou um array
- Entradas de `included` sem `type` devem ser filtradas (contorno de bug da API)
- `links.next` controla a paginação quando presente (null = última página)
- O corpo pode ser vazio (204 No Content) — retorne None

### Operações atômicas (bulk)

```json
{
  "atomic:operations": [
    { "op": "add", "data": { "type": "requirements", "attributes": {}, "relationships": {} } },
    { "op": "remove", "ref": { "type": "requirements", "id": "uuid" } }
  ]
}
```

Response: `{ "atomic:results": [ ... ] }` — cada slot corresponde a uma operação.
Chave `errors` no nível raiz → lança exceção. Erros por slot → retorna como resultado, não lança.

## 5. Hierarquia de erros

Mapeia status HTTP para exceção. Todos herdam de `ClicksignError` base:

| Status HTTP | Classe de exceção | `retryable` |
|-------------|-----------------|-------------|
| 401, 403 | `AuthenticationError` | False |
| 404 | `NotFoundError` | False |
| 400, 422 | `ValidationError` | False |
| 409 | `ConflictError` | False |
| 429 | `RateLimitError` | **True** |
| 5xx | `ServerError` | **True** |
| Timeout / conexão | `TimeoutError` | **True** |

Cada exceção expõe:
- `message` — primeiro `errors[].detail` ou `errors[].title` do corpo, fallback para o reason HTTP
- `status_code` — status HTTP inteiro (None para timeout)
- `request_id` — do header de response `X-Request-Id`
- `response_body` — string do corpo bruto da response
- `retryable` — propriedade bool

`RateLimitError` expõe adicionalmente:
- `rate_limit_remaining` — do header `X-RateLimit-Remaining`
- `rate_limit_reset` — do header `X-RateLimit-Reset`

**Regras de extração do corpo:**
1. Corpo vazio/nil → usa o reason phrase HTTP
2. Corpo é JSON válido mas não é um dict (ex.: array) → usa o reason phrase HTTP
3. `body["errors"][0]["detail"]` → usa detail
4. `body["errors"][0]["title"]` → usa title como fallback
5. Erro de parse JSON → usa o reason phrase HTTP

## 6. Comportamento de retry

Apenas erros com `retryable=True` disparam retry. Erros não-retryable lançam imediatamente.

**Algoritmo de backoff — full jitter:**

```
ceiling(attempt) = min(0.5 * 2^(attempt-1), 30.0)
delay(attempt)   = random(0, ceiling(attempt))   # uniform, not triangular
```

- Tentativa 1 → ceiling 0.5s
- Tentativa 2 → ceiling 1.0s
- Tentativa 3 → ceiling 2.0s
- Limitado a 30.0s

`max_retries = N` significa até N tentativas de retry (N+1 requisições no total).

**`BulkOperationsClient` faz retry apenas em `TimeoutError`** — não em `ServerError`. Isso é intencional:
operações atômicas não são idempotentes por padrão.

## 7. Paginação

### Auto-paginação (busca todas as páginas de forma transparente)

```
fetch_auto_pages(params):
  per = params.get('page[size]', 20)
  page = 1
  loop:
    response = GET endpoint, params={**base_params, 'page[number]': page, 'page[size]': per}
    items = parse(response)
    yield items
    if links.next present:
      break if links.next is null or empty
    else:
      break if len(items) < per   # legacy heuristic
    page += 1
```

**`links.next` tem prioridade.** A heurística de contagem é o fallback para APIs que omitem `links`.
Quando `links.next` é null, NÃO faça outra requisição mesmo que `len(items) == per`.

**Página explícita:** em `to_list()` / `for ... in proxy` / `count()` / `last()`, o `page[number]` da chain **não** é usado — a auto-paginação reinicia em `page = 1`. Para buscar uma página fixa, use `.first()` (uma requisição com os params da chain) ou não use auto-paginação.

### Query chain

Builder encadeável que acumula parâmetros antes de executar:

```python
Resource.filter(status='running') \
        .order('-created') \
        .page(1).per(20) \
        .with_includes('folder') \
        .fields(envelopes=['name', 'status']) \
        .to_list()   # executes
```

Métodos: `filter(**kw)`, `order(field)`, `page(n)`, `per(n)` (máx 50 — veja `pagination.MAX_PAGE_SIZE`), `with_includes(*types)`, `fields(**types)`, `on_page(callback)`

Veja [`PAGINATION.md`](PAGINATION.md) para `last_response` / `page_responses` por página e heurística `links.next` vs. contagem.

`with_includes` valida: os tipos devem ser str, lança `ValueError` se vazio ou tipo errado.

`include` (se exposto) deve tratar tanto module mixing (conforme o idioma da linguagem) quanto tipos JSON:API.

## 8. Classe base de resource

### Métodos de classe

| Método | HTTP | Descrição |
|--------|------|-------------|
| `list()` | GET `/resources` | Sem argumentos, lista eager |
| `filter(**kw)` | — | Retorna QueryProxy |
| `retrieve(id)` | GET `/resources/:id` | Objeto único |
| `create(**attrs)` | POST `/resources` | Retorna nova instância |

### Métodos de instância

| Método | HTTP | Descrição |
|--------|------|-------------|
| `update(**attrs)` | PATCH `/resources/:id` | Muta e retorna self |
| `delete()` | DELETE `/resources/:id` | Retorna None |
| `reload()` | GET `/resources/:id` | Atualiza a partir da API |

### Acesso dinâmico a atributos

Atributos de `data.attributes` acessíveis como propriedades:
```python
envelope.name    # → str
envelope.status  # → str
envelope['name'] # → equivalent via __getitem__
```

Atributo desconhecido → `AttributeError` (não None silencioso).

### Resources aninhados

`nested_list(parent_id, nested_type, as_class=None, params={})` → GET `/{endpoint}/{parent_id}/{nested_type}`

ID do pai armazenado em `_parent_id` para que `update`/`delete`/`reload` construam a URL aninhada correta.

## 9. Instrumentação

Três eventos, publicados antes de lançar qualquer exceção:

```python
# Event payloads (dicts):
request_event = {
    'method': 'get',           # lowercase str
    'path': '/envelopes',      # without base_url
    'status': 200,             # int, None for timeout
    'attempt': 1,              # 1-based
    'duration_ms': 45.3,       # float
}
retry_event = {
    'method': 'get',
    'path': '/envelopes',
    'attempt': 1,
    'max_retries': 3,
    'error': <exception>,
    'wait_ms': 250,
}
error_event = {
    'method': 'get',
    'path': '/envelopes',
    'status': 500,             # None for timeout
    'error': <exception>,
    'duration_ms': 45.3,
}
```

Callbacks devem ser isolados — exceções em callbacks nunca devem se propagar para o chamador.
Se `config.logger` estiver definido, registre erros de callback via `logger.warning(...)`. Caso contrário, silencioso.

API de registro:
```python
Clicksign.on_request(callback)
Clicksign.on_retry(callback)
Clicksign.on_error(callback)
Clicksign.instrumentation.clear()   # for tests
```

## 10. Namespacing de resources

| Namespace | Caminho do módulo | Resources |
|-----------|-------------|-----------|
| Notarial | `clicksign.resources.notarial` | Envelope, Document, Signer, Requirement, BulkRequirement, SignatureWatcher, Event |
| AutoSignature | `clicksign.resources.auto_signature` | Term |
| AcceptanceTerm | `clicksign.resources.acceptance_term` | Whatsapp |
| Root | `clicksign.resources` | Webhook, User, Membership, Group, Folder, Template, TemplateField, AccessControlList, EnvelopeBulkCreation |

## 11. Segurança de thread / async

- Configuração global única — não é segura para mutação concorrente
- Cliente thread-local: context manager `Services.use(api_key, base_url)` define o cliente apenas para a thread atual
- Async: use `AsyncClicksignClient` / `AsyncClient` (`pip install clicksign[async]`). Não dependa de `Services.use()` sob asyncio; passe um cliente async explícito por escopo de app/coroutine
- Atualizações de instância em fluxos async: `update_async`, `delete_async`, `reload_async` nos resources retornados pelo cliente async

## 12. Validação de webhook

Comparação em tempo constante HMAC-SHA256:

```python
import hmac, hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = 'sha256=' + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

`WebhookSignatureError` lançado em caso de divergência.

---

## Checklist — "concluído" por módulo

- [ ] Configuration com todos os atributos e atalho `environment=`
- [ ] Cliente HTTP com timeouts, headers de autenticação, headers JSON:API
- [ ] Hierarquia de erros com `retryable`, `status_code`, `request_id`
- [ ] `ErrorHandler` com todas as regras de extração do corpo
- [ ] `RetryBackoff` com full jitter, testado deterministicamente com RNG com seed
- [ ] `JsonApiSerializer` — produz corpo correto para create/update/sem-relacionamentos
- [ ] `JsonApiParser` — trata data único/array, filtra `included` sem `type`
- [ ] `QueryBuilder` — todos os métodos de chain, saída de `to_params()` verificada
- [ ] `Resource` base — todos os CRUD, atributos dinâmicos, `__getitem__`, nested list
- [ ] `QueryProxy` — todos os métodos de chain retornam proxy; `to_list`, `first`, `last`, `count`, auto-paging
- [ ] `Instrumentation` — todos os 3 eventos, isolamento de callback, integração com logger
- [ ] `BulkOperationsClient` — atomic ops, resultados por slot, retry apenas em timeout, instrumentação
- [ ] `Services` — context manager thread-local
- [ ] `Webhook` — verificação HMAC em tempo constante
- [ ] Todos os resources implementados conforme SPEC.md
- [ ] Todos os comportamentos de spec do SDK_TEST_MATRIX.md cobertos
