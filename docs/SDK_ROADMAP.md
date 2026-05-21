# SDK Python — Checklist de implementação

Roadmap de infraestrutura e DX do SDK Clicksign Python (camada HTTP, resources, observabilidade).

**Escopo:** comportamento do SDK — não cobertura de endpoints da API Clicksign.

**Referência:** análise de maio/2026. Contrato interno: [`SDK_CONTRACT.md`](SDK_CONTRACT.md).

**Legenda de prioridade**

| Prioridade | Significado |
|------------|-------------|
| Alta | Quebra contrato, funcionalidade incompleta ou impacto direto em produção |
| Média | Melhoria relevante de DX/observabilidade; workaround possível |
| Baixa | Polish de SDK maduro ou escopo explícito de versão futura (v2) |
| Design | Decisão intencional documentada — não é bug |

---

## Já implementado (v1)

- [x] Configuração global (`configure()`)
- [x] Retry com full jitter (429, 5xx, timeout) no `Client`; `Retry-After` em 429
- [x] Hierarquia de exceções com flag `retryable`
- [x] Paginação automática (`QueryProxy`, `links.next`, `on_page`, `page_responses`)
- [x] Verificação HMAC de webhook (`verify_signature`, `construct_event`)
- [x] Multi-tenant via thread-local (`Services.use()`)
- [x] Operações atômicas (`BulkOperationsClient`)
- [x] Instrumentation hooks (`on_request`, `on_retry`, `on_error`)
- [x] Transporte plugável (`UrllibHTTPClient`, `HttpxHTTPClient` extra)
- [x] Timeouts `open` / `read` / `write`
- [x] `ClicksignClient` facade + `raw_request` / `deserialize`
- [x] `RequestOptions` (api_key, headers, timeouts, `max_retries`)
- [x] `last_response` / `ResponseMetadata`
- [x] JSON:API `included` (sideload)
- [x] Erros estruturados (`api_errors`, pointers)
- [x] Logging integrado (`CLICKSIGN_LOG`, `clicksign.log`)
- [x] User-Agent + `set_app_info`
- [x] Telemetria opt-in (`enable_telemetry`)
- [x] Tipagem TypedDict (14 resources) — [`TYPES.md`](TYPES.md)
- [x] `AsyncClicksignClient` + `clicksign[async]`
- [x] `correlation_id()` helper
- [x] Runtime default stdlib-only; extras `httpx` / `async`

Detalhes por § abaixo permanecem como histórico; gaps abertos do cliente: [`SDK_CLIENT_GAPS.md`](SDK_CLIENT_GAPS.md). Índice de docs: [`README.md`](README.md).

---

## 1. Transporte HTTP plugável

**Prioridade:** Baixa (v2) / Design parcial — **implementado (v1 mínimo)**

**Alvo:** clientes HTTP intercambiáveis; proxy e `verify_ssl_certs` configuráveis.

**Clicksign:** `UrllibHTTPClient` (default via `http.client`), `HttpxHTTPClient` (extra `[httpx]`), injeção via `http_client=` em `Client`, `BulkOperationsClient`, `Services` e `configure()`.

**Impacto:** sem connection pool no default stdlib; pool disponível ao injetar `HttpxHTTPClient` ou client custom.

### Checklist

- [x] Definir interface `HTTPClient` (get/post/patch/delete + timeouts)
- [x] Manter `UrllibHTTPClient` como implementação padrão (stdlib)
- [x] Implementar adapter opcional `httpx` (extra `[httpx]`)
- [x] Suporte a `proxy=` na configuração ou no client
- [x] Suporte a `verify_ssl_certs=` (ou equivalente)
- [x] Documentar trade-off stdlib vs pool persistente
- [x] Testes com mock de transporte injetado

### Futuro (v2 — não implementado)

- [ ] Avaliar `HttpxHTTPClient` como transporte **default** (breaking: dependência de runtime `httpx`)
- [ ] Se mudar default: major version + guia de migração (`UrllibHTTPClient` explícito para quem quiser stdlib-only)

Documentado em v1: [`cookbook/12-http-connection-pool.md`](cookbook/12-http-connection-pool.md), [`08-production-limitations.md`](cookbook/08-production-limitations.md).

---

## 2. Timeouts incompletos (`open_timeout` / `write_timeout`)

**Prioridade:** Alta

**Alvo:** timeouts de conexão, leitura e escrita aplicados pelo HTTP client.

**Clicksign:** `Configuration` expõe os três timeouts; `UrllibHTTPClient` aplica via `http.client` (connect/write/read separados).

**Referência:** `src/clicksign/http_transport.py`, `src/clicksign/client.py`.

### Checklist

- [x] Aplicar `open_timeout` na fase de conexão TCP/TLS
- [x] Aplicar `write_timeout` no envio do body (POST/PATCH)
- [x] Manter `read_timeout` na leitura da resposta
- [x] Replicar comportamento no `BulkOperationsClient`
- [x] Testes: connect timeout, read timeout, write timeout isolados
- [x] Atualizar `SDK_TEST_MATRIX.md`

---

## 3. Async — **implementado** (`clicksign[async]`)

**Prioridade:** Baixa — concluído em v1 via extra opcional.

**Clicksign:** `AsyncClient`, `AsyncClicksignClient`, `AsyncQueryProxy` com `async for`; ver `SDK_CONTRACT.md` §11.

### Checklist

- [x] Dependência `httpx` no extra `[async]`
- [x] `AsyncClient` separado
- [x] Facade `AsyncClicksignClient` + resources bound
- [x] Paginação async (`async for`)
- [x] Documentar incompatibilidade de `Services.use()` com asyncio
- [x] Extra `clicksign[async]` no `pyproject.toml`
- [x] Testes `pytest-asyncio`

---

## 4. Entry point público (`ClicksignClient`)

**Prioridade:** Média

**Alvo:** client explícito com namespace de resources (`client.envelopes.list()`).

**Clicksign:** `configure()` + import de resources; `Client`, `Services` e `ClicksignClient` exportados em `clicksign.__all__`.

### Checklist

- [x] Exportar `Client` e `Services` em `clicksign.__init__`
- [x] `ClicksignClient` como facade de alto nível (`client.notarial.envelopes.list()`)
- [x] Exportar resources principais no namespace raiz (opcional)
- [x] Exemplo no README: padrão global vs client explícito
- [x] Manter compatibilidade com `configure()` existente

---

## 5. Opções por request

**Prioridade:** Média

**Alvo:** override de api key, headers e timeouts por chamada.

**Clicksign:** config global, `Services.use()` por thread ou `ClicksignClient`; override via `RequestOptions`.

### Checklist

- [x] Definir tipo `RequestOptions` (api_key, headers, timeouts, `max_retries`)
- [x] Propagar options em `Client._request()`
- [x] Suportar options em class methods de `Resource` (retrieve, create, list via proxy)
- [x] Documentar precedência: per-request > thread-local > global
- [x] Testes: duas api_keys no mesmo processo via options

---

## 6. `last_response` (status e headers em sucesso)

**Prioridade:** Média

**Alvo:** metadados HTTP acessíveis após sucesso (status, headers).

**Clicksign:** `Resource.last_response` e `QueryProxy.last_response` com `ResponseMetadata`.

### Checklist

- [x] Criar dataclass `ResponseMetadata` (status, headers, request_id, duration_ms)
- [x] Anexar `last_response` em instâncias de `Resource` após CRUD
- [x] Anexar em resultados de `QueryProxy.to_list()` / `first()` (ou no proxy)
- [x] Expor headers úteis (`X-Request-Id`, rate limit)
- [x] Testes: retrieve popula `last_response`

---

## 7. `raw_request` (escape hatch)

**Prioridade:** Média

**Alvo:** chamada HTTP bruta + deserialização opcional para resources.

**Clicksign:** `Client.raw_request()` e `Client.deserialize()` expostos publicamente.

### Checklist

- [x] Expor `Client.raw_request(method, path, *, params, body, headers)`
- [x] Retornar corpo parseado (dict) ou wrapper com status/headers
- [x] Opcional: `Client.deserialize(response, resource_class)` para JSON:API
- [x] Respeitar retry e instrumentation existentes
- [x] Documentar uso para endpoints beta/não mapeados
- [x] Testes com path arbitrário

---

## 8. Erros estruturados

**Prioridade:** Média

**Alvo:** erros de API com código, ponteiro de campo e lista completa de erros.

**Clicksign:** `ValidationError` e demais exceções expõem `errors`, `error_code`, `source_pointer` e `api_errors`.

### Checklist

- [x] Expor `errors: list[dict]` (ou typed) em `ValidationError` / `ClicksignError`
- [x] Expor `error_code` / `source.pointer` quando presentes (JSON:API)
- [x] Manter `message` como atalho para o primeiro erro (compatibilidade)
- [x] Testes: múltiplos erros no body 422
- [x] Documentar formato para consumo em formulários

---

## 9. JSON:API `included` (sideload)

**Prioridade:** Alta

**Alvo:** resolver relacionamentos incluídos na mesma resposta (equivalente a “expand”).

**Clicksign:** `with_includes()` envia o param; `included` é indexado e relacionamentos sideloaded resolvem em atributos (`envelope.folder`).

### Checklist

- [x] Retornar `included` de `_parse_response` (ou objeto `ParsedResponse` público)
- [x] Indexar `included` por `(type, id)` para lookup
- [x] Resolver relacionamentos sideloaded em `Resource` (ex.: `envelope.folder`)
- [x] `QueryProxy.with_includes()` popula sideload nos itens retornados
- [x] Testes: list com `include=folder` retorna folder resolvível
- [x] Documentar limites (includes aninhados, polymorphic)

---

## 10. Webhooks — parse completo do evento

**Prioridade:** Média

**Alvo:** validar assinatura e parsear payload em um passo (`construct_event`).

**Clicksign:** `verify_signature()` / `verify_signature_or_raise()` + `construct_event()` → `WebhookEvent`.

### Checklist

- [x] `construct_event(payload, signature, secret) -> WebhookEvent`
- [x] Validar assinatura + parse JSON em um passo
- [x] Tolerância de timestamp anti-replay via `event.occurred_at` (opcional)
- [x] Classe `WebhookEvent` (`type`, `data`, `id`, `occurred_at`, `payload`)
- [x] Testes: payload válido, assinatura inválida, payload alterado
- [x] Documentar formato de assinatura Clicksign

### Formato Clicksign (webhooks de entrada)

| Aspecto | Comportamento |
|---------|----------------|
| Header | `Content-HMAC` com valor `sha256=<hex>` |
| Algoritmo | HMAC-SHA256 do **body bruto** (não reformatar JSON antes do hash) |
| Anti-replay | `tolerance` opcional checando `event.occurred_at` no JSON |
| Payload | `{ "event": { "name", "data", "occurred_at" }, ...recursos do evento }` |

---

## 11. Logging integrado

**Prioridade:** Baixa

**Alvo:** logger dedicado do SDK com nível via env; logs HTTP em debug sem vazar secrets.

**Clicksign:** logger `clicksign.*` via stdlib; `clicksign.log` / `CLICKSIGN_LOG`; `Configuration.logger` para erros em callbacks customizados.

### Checklist

- [x] Logger dedicado `clicksign` (stdlib `logging`)
- [x] Nível configurável via env `CLICKSIGN_LOG=debug|info`
- [x] Log de request/response em debug (sem vazar api_key)
- [x] Integrar com hooks existentes ou substituir parcialmente
- [x] Documentar em README e `OBSERVABILITY.md`

---

## 12. User-Agent e identificação de app

**Prioridade:** Baixa

**Alvo:** identificar SDK e app host no `User-Agent`.

**Clicksign:** `User-Agent` com versão do SDK e Python; `set_app_info()` para identificar a app host.

### Checklist

- [x] Header `User-Agent: clicksign-python/<version>`
- [x] API `set_app_info(name, version, url)` global ou por client
- [x] Incluir versão Python e bindings no UA (opcional)
- [x] Testes: header presente nas requests
- [x] Documentar para plugins/integrações

---

## 13. Telemetria para o provedor

**Prioridade:** Baixa / Design (opt-in)

**Alvo:** telemetria de latência enviada ao provedor da API, desligável.

**Clicksign:** telemetria opt-in (`enable_telemetry`, default `False`); hooks locais (`on_request`) permanecem.

### Checklist

- [x] Flag `enable_telemetry` (default `False` até endpoint oficial)
- [x] Respeitar privacidade (sem payload/body)
- [x] Documentar opt-out

---

## 14. Tipagem estática nos resources

**Prioridade:** Média

**Alvo:** TypedDict / `Unpack` por resource; autocomplete no IDE.

**Clicksign:** TypedDict + properties explícitas nos resources principais; `QueryProxy[T]` genérico.

### Checklist

- [x] TypedDict por resource principal (Envelope, Document, Signer, …)
- [x] Overloads em `create(**attrs)` / `update(**attrs)` onde viável
- [x] Gerar types a partir de spec incremental (`scripts/generate_resource_types.py`)
- [x] Documentar estratégia de versioning dos types
- [x] CI: mypy nos resources tipados

Ver [`docs/TYPES.md`](TYPES.md).

---

## 15. Retry em 409 Conflict

**Prioridade:** Baixa / **Fora de escopo (N/A)**

**Alvo:** retry automático em 409 apenas quando transitório e com idempotência.

**Clicksign:** `ConflictError(retryable=False)` — **decisão:** a API Clicksign não expõe 409 transitório.

### Checklist

- [x] Validar com API Clicksign se 409 é transitório — **não há caso de uso**
- [x] Retry 409 / idempotência — N/A

---

## 16. Rate limit — header `Retry-After`

**Prioridade:** Baixa

**Alvo:** respeitar `Retry-After` em 429 quando presente.

**Clicksign:** usa `Retry-After` em 429 (`max(jitter, retry_after)`); fallback para jitter.

### Checklist

- [x] Ler `Retry-After` em respostas 429
- [x] Usar `max(jitter, retry_after)` quando header presente
- [x] Fallback para algoritmo atual quando header ausente
- [x] Testes: 429 com e sem `Retry-After`

---

## 17. Assimetria `BulkOperationsClient` vs `Client`

**Prioridade:** Design (documentado)

**Alvo (SDK maduro):** mesma política de retry em todos os clients HTTP.

**Clicksign:** `BulkOperationsClient` retenta **apenas** `TimeoutError`; não retenta 429/5xx — ops atômicas não são idempotentes sem `Idempotency-Key` na API.

### Política de retry

| Erro | `Client` | `BulkOperationsClient` |
|------|----------|------------------------|
| Timeout / conexão | Sim | Sim |
| HTTP 429 | Sim (+ `Retry-After`) | **Não** |
| HTTP 5xx | Sim | **Não** |
| 401, 403, 404, 422 | Não | Não |

**Decisão (429 no bulk):** não habilitar retry de 429 até a API suportar idempotência em POST atômico. Rate limit no bulk deve ser tratado na aplicação (backoff manual + reenvio do payload).

### Checklist

- [x] Comportamento documentado em `SDK_CONTRACT.md` §6
- [x] Tabela em `docs/cookbook/01-retries.md`
- [x] Teste `test_does_not_retry_on_server_error` em bulk client
- [x] Decisão: retry de 429 no bulk — **não** (sem idempotência)
- [x] Documentar assimetria Client vs Bulk (este §17)

---

## 18. Idempotência

**Prioridade:** Alta / **Fora de escopo (N/A)**

**Alvo:** header `Idempotency-Key` em POST; retry seguro.

**Clicksign:** **não implementado** — a API Clicksign ainda não suporta o header no servidor.

### Checklist

- [x] Suporte da API — **servidor não implementa**
- [x] Header / retry seguro em bulk — N/A até API evoluir

---

## Resumo por prioridade (estado maio/2026)

### Concluído no v1

Itens §2–§14, §16–§17 (exceto N/A §15, §18). Ver lista **Já implementado** acima e [`SDK_CLIENT_GAPS.md`](SDK_CLIENT_GAPS.md) para polish recente.

### Aberto / contínuo

| Área | Onde |
|------|------|
| Cobertura de resources admin | `SDK_CLIENT_GAPS.md` §3 |
| httpx como default (breaking) | §1 futuro v2 |
| Idempotência / retry 409 | §15, §18 — N/A API |

### Design intencional

| Item | Nota |
|------|------|
| stdlib default sem pool | [`cookbook/08-production-limitations.md`](cookbook/08-production-limitations.md) |
| Bulk sem retry 5xx/429 | `SDK_CONTRACT.md` §6, [`01-retries.md`](cookbook/01-retries.md) |
| Retry 409 / idempotência | API não suporta |

---

## Como usar este documento

1. Priorizar itens **Alta** antes de release major.
2. Marcar `[x]` conforme implementação e testes forem concluídos.
3. Atualizar `SDK_TEST_MATRIX.md` quando um item virar comportamento contratual.
4. Revisar trimestralmente o roadmap com o contrato em `SDK_CONTRACT.md`.
