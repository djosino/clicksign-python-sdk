# SDK Test Matrix — Cobertura comportamental (Python)

Cada item deve ter teste em `tests/clicksign/`. Marque `[x]` quando coberto.

**Referência:** `tests/clicksign/test_*.py` e `tests/clicksign/resources/`.

**Defaults atuais:** `max_retries=3` (global/client); timeouts `2` / `10` / `10` s.

---

## Configuração — `test_configuration.py`

- [x] Defaults: production base_url, open/read/write timeouts, `max_retries=3`, logger=None
- [x] `environment='sandbox'` / `'production'`
- [x] Ambiente desconhecido levanta ValueError
- [x] Aceita um objeto logger

---

## HTTP Client — `test_client.py`, `test_http_transport.py`

- [x] GET/POST/PATCH/DELETE headers e body
- [x] `Authorization` sem prefixo `Bearer`
- [x] TimeoutError em connect / read / connection refused
- [x] `open_timeout` / `read_timeout` / `write_timeout` repassados ao transporte
- [x] `HttpxHTTPClient` opcional (`test_client.py`)

---

## Tratamento de erros — `test_error_handler.py`, `test_errors.py`, `test_structured_errors.py`

- [x] Mapeamento 401, 403, 404, 400, 422, 409, 429, 5xx
- [x] Body não-JSON, array JSON, title sem detail, body vazio
- [x] `status_code`, `request_id`, headers de rate limit em 429
- [x] `retryable` True/False por tipo

---

## Retry — `test_client.py`, `test_request_options.py`

- [x] `max_retries=0` → uma tentativa
- [x] Retry em 500, 429, TimeoutError; sem retry em 422
- [x] Esgota após N retries; backoff com jitter
- [x] 429 com header `Retry-After` (`test_retry_backoff.py`)
- [x] Override de `RequestOptions.max_retries` (`test_request_options.py`)

---

## RetryBackoff — `test_retry_backoff.py`

- [x] `ceiling`, `delay`, `parse_retry_after`, `retry_delay`

---

## JsonApiSerializer / Parser — `test_json_api_serializer.py`, `test_json_api_parser.py`

- [x] Regras de payload para create/update
- [x] Parse de single/array/empty, included, filtro sem `type`

---

## QueryBuilder — `test_query_builder.py`

- [x] filter, order, page, per (máx 50), includes, fields, chain
- [x] `per` acima do máximo levanta ValueError

---

## Resource / QueryProxy / paginação — `test_resource.py`, `test_pagination.py`, `test_last_response.py`

- [x] CRUD, atributos dinâmicos, chain de QueryProxy
- [x] Auto-paginação: `links.next`, heurística, página cheia extra
- [x] `QueryProxy.last_response` por página; callback `on_page`
- [x] `page_responses` lista metadados

---

## Instrumentation — `test_instrumentation.py`, `test_client.py`

- [x] Eventos de request / retry / error
- [x] Exceção em callback não propaga; `clear()` no `conftest`
- [x] `on_request`, `on_retry`, `on_error` no pacote raiz

---

## BulkOperationsClient — `test_bulk_operations_client.py`

- [x] Headers, POST JSON, parse de `atomic:results`
- [x] Retry apenas em TimeoutError; **sem** retry em 500
- [x] Instrumentation

---

## Services — `test_services.py`

- [x] `use()` isola client; restaura após bloco e exceção
- [x] Ambiente desconhecido

---

## Webhook — `test_webhook.py`

- [x] `verify_signature`, `construct_event`, comparação em tempo constante

---

## ClicksignClient / raw — `test_clicksign_client.py`, `test_raw_request.py`

- [x] Namespaces da facade, `raw_request`, `deserialize`, `last_response`

---

## Async — `test_async_client.py`, `test_async_clicksign_client.py`

- [x] HTTP do AsyncClient; resources e paginação do AsyncClicksignClient

---

## Logging / UA / telemetria — `test_log.py`, `test_user_agent.py`, `test_provider_telemetry.py`

- [x] `CLICKSIGN_LOG`, redação do header Authorization
- [x] User-Agent + `set_app_info`
- [x] Telemetria opt-in

---

## Headers de request — `test_request_options.py`

- [x] `correlation_id()` → `X-Correlation-Id` mesclado

---

## Specs de resource — `tests/clicksign/resources/`

Cobertura por resource (CRUD, filter, erros 404/422 onde aplicável):

- [x] Notarial: envelope, document, signer, requirement, signature_watcher, bulk_requirement, event
- [x] Admin: user, template, template_field, membership, group, folder, webhook
- [x] Parcial: acceptance_term, auto_signature, access_control_list, envelope_bulk_creation (conforme métodos expostos)

Adicionar testes ao criar novos métodos (ver [`SPEC.md`](SPEC.md) e esta matriz).

---

## Retry Bulk vs Client (documentado + testado)

| Política | Teste |
|----------|--------|
| Client retenta 429/5xx/timeout | `test_client.py` |
| Bulk retenta apenas timeout | `test_bulk_operations_client.py` (`test_does_not_retry_on_server_error`) |

Ver [`examples/01-retries.md`](examples/01-retries.md).
