# SDK Test Matrix — Cobertura comportamental (Python)

Cada item deve ter teste em `tests/clicksign/`. Marque `[x]` quando coberto.

**Referência:** `tests/clicksign/test_*.py` e `tests/clicksign/resources/`.

**Defaults atuais:** `max_retries=3` (global/client); timeouts `2` / `10` / `10` s.

---

## Configuration — `test_configuration.py`

- [x] Defaults: production base_url, open/read/write timeouts, `max_retries=3`, logger=None
- [x] `environment='sandbox'` / `'production'`
- [x] Unknown environment raises ValueError
- [x] Accepts a logger object

---

## HTTP Client — `test_client.py`, `test_http_transport.py`

- [x] GET/POST/PATCH/DELETE headers e body
- [x] `Authorization` sem prefixo `Bearer`
- [x] TimeoutError em connect / read / connection refused
- [x] `open_timeout` / `read_timeout` / `write_timeout` repassados ao transporte
- [x] `HttpxHTTPClient` opcional (`test_client.py`)

---

## Error handler — `test_error_handler.py`, `test_errors.py`, `test_structured_errors.py`

- [x] Mapeamento 401, 403, 404, 400, 422, 409, 429, 5xx
- [x] Body não-JSON, array JSON, title sem detail, body vazio
- [x] `status_code`, `request_id`, rate limit headers em 429
- [x] `retryable` True/False por tipo

---

## Retry — `test_client.py`, `test_request_options.py`

- [x] `max_retries=0` → uma tentativa
- [x] Retry 500, 429, TimeoutError; não retry 422
- [x] Esgota após N retries; backoff com jitter
- [x] 429 com header `Retry-After` (`test_retry_backoff.py`)
- [x] `RequestOptions.max_retries` override (`test_request_options.py`)

---

## RetryBackoff — `test_retry_backoff.py`

- [x] `ceiling`, `delay`, `parse_retry_after`, `retry_delay`

---

## JsonApiSerializer / Parser — `test_json_api_serializer.py`, `test_json_api_parser.py`

- [x] Create/update payload rules
- [x] Parse single/array/empty, included, filter sem `type`

---

## QueryBuilder — `test_query_builder.py`

- [x] filter, order, page, per (max 50), includes, fields, chain
- [x] `per` acima do máximo levanta ValueError

---

## Resource / QueryProxy / pagination — `test_resource.py`, `test_pagination.py`, `test_last_response.py`

- [x] CRUD, dynamic attrs, QueryProxy chain
- [x] Auto-pagination: `links.next`, heurística, página cheia extra
- [x] `QueryProxy.last_response` por página; `on_page` callback
- [x] `page_responses` lista metadados

---

## Instrumentation — `test_instrumentation.py`, `test_client.py`

- [x] request / retry / error events
- [x] Callback exception não propaga; `clear()` no `conftest`
- [x] `on_request`, `on_retry`, `on_error` no pacote raiz

---

## BulkOperationsClient — `test_bulk_operations_client.py`

- [x] Headers, POST JSON, parse `atomic:results`
- [x] Retry só TimeoutError; **não** retry 500
- [x] Instrumentation

---

## Services — `test_services.py`

- [x] `use()` isola client; restaura após bloco e exceção
- [x] Unknown environment

---

## Webhook — `test_webhook.py`

- [x] `verify_signature`, `construct_event`, constant-time compare

---

## ClicksignClient / raw — `test_clicksign_client.py`, `test_raw_request.py`

- [x] Facade namespaces, `raw_request`, `deserialize`, `last_response`

---

## Async — `test_async_client.py`, `test_async_clicksign_client.py`

- [x] AsyncClient HTTP; AsyncClicksignClient resources e paginação

---

## Logging / UA / telemetry — `test_log.py`, `test_user_agent.py`, `test_provider_telemetry.py`

- [x] `CLICKSIGN_LOG`, redação de Authorization
- [x] User-Agent + `set_app_info`
- [x] Telemetria opt-in

---

## Request headers — `test_request_options.py`

- [x] `correlation_id()` → `X-Correlation-Id` merged

---

## Resource specs — `tests/clicksign/resources/`

Cobertura por resource (CRUD, filter, erros 404/422 onde aplicável):

- [x] Notarial: envelope, document, signer, requirement, signature_watcher, bulk_requirement, event
- [x] Admin: user, template, template_field, membership, group, folder, webhook, event
- [x] Parcial: acceptance_term, auto_signature, access_control_list, envelope_bulk_creation (conforme métodos expostos)

Adicionar testes ao criar novos métodos em [`SDK_CLIENT_GAPS.md`](SDK_CLIENT_GAPS.md) §3.

---

## Bulk vs Client retry (documentado + testado)

| Política | Teste |
|----------|--------|
| Client retenta 429/5xx/timeout | `test_client.py` |
| Bulk retenta só timeout | `test_bulk_operations_client.py` (`test_does_not_retry_on_server_error`) |

Ver [`cookbook/01-retries.md`](cookbook/01-retries.md).
