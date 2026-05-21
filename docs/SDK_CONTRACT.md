# Clicksign SDK Contract — Language-Agnostic Specification

**Version:** 1.0
**Source:** Clicksign API v3 (JSON:API 1.1)
**Reference implementation:** `../clicksign-ruby-sdk`

This document defines the **complete behavioral contract** for any Clicksign SDK port.
Implement every section exactly. When Python idioms differ from Ruby, prefer Python idioms
but preserve the behavior.

---

## 1. Authentication

- Header: `Authorization: <token>` — **NO** `Bearer` prefix, no `Token` prefix, raw token only
- Header: `Content-Type: application/vnd.api+json`
- Header: `Accept: application/vnd.api+json`
- Token comes from `Configuration.api_key`

## 2. Base URLs

| Environment | URL |
|-------------|-----|
| Production  | `https://app.clicksign.com/api/v3` |
| Sandbox     | `https://sandbox.clicksign.com/api/v3` |

Default: production. Shortcut: `config.environment = 'sandbox'` sets the URL automatically.
Unknown environment string raises `ValueError` (or equivalent).

## 3. Configuration

Single configuration object, set once at startup. Attributes:

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | str | None | API token |
| `base_url` | str | production URL | Full base URL |
| `open_timeout` | float | 2.0 | TCP connect timeout (seconds) |
| `read_timeout` | float | 10.0 | Read timeout (seconds) |
| `write_timeout` | float | 10.0 | Write timeout (seconds) |
| `max_retries` | int | 3 | Retry attempts (0 = no retry) |
| `logger` | Logger | None | Optional logger for callback errors |

`environment=` shortcut sets `base_url` from the table above.

**Thread safety:** not safe for concurrent first access. Must be configured once before threads spawn.

## 4. Request / Response format

### Request body (POST, PATCH)

JSON:API document:

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

- Omit `id` on create
- Omit `relationships` key when empty (not `"relationships": {}`)
- Include `id` on update (PATCH)

### Response parsing

```json
{
  "data": { "id": "uuid", "type": "envelopes", "attributes": {}, "relationships": {} },
  "included": [],
  "links": { "next": "url-or-null" },
  "meta": {}
}
```

- `data` may be a single object or an array
- `included` entries without `type` must be filtered out (API bug workaround)
- `links.next` drives pagination when present (null = last page)
- Body may be empty (204 No Content) — return None

### Atomic operations (bulk)

```json
{
  "atomic:operations": [
    { "op": "add", "data": { "type": "requirements", "attributes": {}, "relationships": {} } },
    { "op": "remove", "ref": { "type": "requirements", "id": "uuid" } }
  ]
}
```

Response: `{ "atomic:results": [ ... ] }` — each slot maps to one operation.
Top-level `errors` key → raise exception. Per-slot errors → return as result, do not raise.

## 5. Error hierarchy

Map HTTP status to exception. All inherit from a base `ClicksignError`:

| HTTP status | Exception class | `retryable` |
|-------------|-----------------|-------------|
| 401, 403 | `AuthenticationError` | False |
| 404 | `NotFoundError` | False |
| 400, 422 | `ValidationError` | False |
| 409 | `ConflictError` | False |
| 429 | `RateLimitError` | **True** |
| 5xx | `ServerError` | **True** |
| Timeout / connection | `TimeoutError` | **True** |

Each exception exposes:
- `message` — first `errors[].detail` or `errors[].title` from body, fallback to HTTP reason
- `status_code` — integer HTTP status (None for timeout)
- `request_id` — from `X-Request-Id` response header
- `response_body` — raw response body string
- `retryable` — bool property

`RateLimitError` additionally exposes:
- `rate_limit_remaining` — from `X-RateLimit-Remaining` header
- `rate_limit_reset` — from `X-RateLimit-Reset` header

**Body extraction rules:**
1. Empty/nil body → use HTTP reason phrase
2. Body is valid JSON but not a dict (e.g., array) → use HTTP reason phrase
3. `body["errors"][0]["detail"]` → use detail
4. `body["errors"][0]["title"]` → use title as fallback
5. JSON parse error → use HTTP reason phrase

## 6. Retry behavior

Only `retryable=True` errors trigger retry. Non-retryable errors raise immediately.

**Backoff algorithm — full jitter:**

```
ceiling(attempt) = min(0.5 * 2^(attempt-1), 30.0)
delay(attempt)   = random(0, ceiling(attempt))   # uniform, not triangular
```

- Attempt 1 → ceiling 0.5s
- Attempt 2 → ceiling 1.0s
- Attempt 3 → ceiling 2.0s
- Capped at 30.0s

`max_retries = N` means up to N retry attempts (N+1 total requests).

**`BulkOperationsClient` retries only `TimeoutError`** — not `ServerError`. This is intentional:
atomic operations are not idempotent by default.

## 7. Pagination

### Auto-pagination (fetch all pages transparently)

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

**`links.next` takes priority.** The count heuristic is the fallback for APIs that omit `links`.
When `links.next` is null, do NOT make another request even if `len(items) == per`.

### Query chain

Chainable builder accumulating params before executing:

```python
Resource.filter(status='running') \
        .order('-created') \
        .page(1).per(20) \
        .with_includes('folder') \
        .fields(envelopes=['name', 'status']) \
        .to_list()   # executes
```

Methods: `filter(**kw)`, `order(field)`, `page(n)`, `per(n)` (max 50 — see `pagination.MAX_PAGE_SIZE`), `with_includes(*types)`, `fields(**types)`, `on_page(callback)`

See [`PAGINATION.md`](PAGINATION.md) for `last_response` / `page_responses` per page and `links.next` vs. count heuristic.

`with_includes` validates: types must be str, raises `ValueError` if empty or wrong type.

`include` (if exposed) must handle both module mixing (language-appropriate) and JSON:API types.

## 8. Resource base class

### Class methods

| Method | HTTP | Description |
|--------|------|-------------|
| `list()` | GET `/resources` | No args, eager list |
| `filter(**kw)` | — | Returns QueryProxy |
| `retrieve(id)` | GET `/resources/:id` | Single object |
| `create(**attrs)` | POST `/resources` | Returns new instance |

### Instance methods

| Method | HTTP | Description |
|--------|------|-------------|
| `update(**attrs)` | PATCH `/resources/:id` | Mutates and returns self |
| `delete()` | DELETE `/resources/:id` | Returns None |
| `reload()` | GET `/resources/:id` | Refreshes from API |

### Dynamic attribute access

Attributes from `data.attributes` accessible as properties:
```python
envelope.name    # → str
envelope.status  # → str
envelope['name'] # → equivalent via __getitem__
```

Unknown attribute → `AttributeError` (not silent None).

### Nested resources

`nested_list(parent_id, nested_type, as_class=None, params={})` → GET `/{endpoint}/{parent_id}/{nested_type}`

Parent ID stored in `_parent_id` so `update`/`delete`/`reload` build correct nested URL.

## 9. Instrumentation

Three events, published before raising any exception:

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

Callbacks must be isolated — exceptions in callbacks must never propagate to the caller.
If `config.logger` is set, log callback errors via `logger.warning(...)`. Otherwise silent.

Registration API:
```python
Clicksign.on_request(callback)
Clicksign.on_retry(callback)
Clicksign.on_error(callback)
Clicksign.instrumentation.clear()   # for tests
```

## 10. Resource namespacing

| Namespace | Module path | Resources |
|-----------|-------------|-----------|
| Notarial | `clicksign.resources.notarial` | Envelope, Document, Signer, Requirement, BulkRequirement, SignatureWatcher, Event |
| AutoSignature | `clicksign.resources.auto_signature` | Term |
| AcceptanceTerm | `clicksign.resources.acceptance_term` | Whatsapp |
| Root | `clicksign.resources` | Webhook, User, Membership, Group, Folder, Template, TemplateField, AccessControlList, EnvelopeBulkCreation |

## 11. Thread / async safety

- Single global configuration — not safe for concurrent mutation
- Thread-local client: `Services.use(api_key, base_url)` context manager sets client for current thread only
- Async: use `AsyncClicksignClient` / `AsyncClient` (`pip install clicksign[async]`). Do not rely on `Services.use()` under asyncio; pass an explicit async client per app/coroutine scope
- Instance updates in async flows: `update_async`, `delete_async`, `reload_async` on resources returned by the async client

## 12. Webhook validation

HMAC-SHA256 constant-time comparison:

```python
import hmac, hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = 'sha256=' + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

`WebhookSignatureError` raised on mismatch.

---

## Checklist — "done" per module

- [ ] Configuration with all attributes and `environment=` shortcut
- [ ] HTTP client with timeouts, auth headers, JSON:API headers
- [ ] Error hierarchy with `retryable`, `status_code`, `request_id`
- [ ] `ErrorHandler` with all body-extraction rules
- [ ] `RetryBackoff` with full jitter, tested deterministically with seeded RNG
- [ ] `JsonApiSerializer` — produces correct body for create/update/no-relationships
- [ ] `JsonApiParser` — handles single/array data, filters `included` without `type`
- [ ] `QueryBuilder` — all chain methods, `to_params()` output verified
- [ ] `Resource` base — all CRUD, dynamic attributes, `__getitem__`, nested list
- [ ] `QueryProxy` — all chain methods return proxy; `to_list`, `first`, `last`, `count`, auto-paging
- [ ] `Instrumentation` — all 3 events, callback isolation, logger integration
- [ ] `BulkOperationsClient` — atomic ops, per-slot results, timeout-only retry, instrumentation
- [ ] `Services` — thread-local context manager
- [ ] `Webhook` — constant-time HMAC verification
- [ ] All resources implemented per SPEC.md
- [ ] All spec behaviors from SDK_TEST_MATRIX.md covered
