# clicksign-python-sdk

## Testing

- Run all tests: `pytest`
- Run with coverage: `pytest --cov=clicksign --cov-report=term-missing`
- Format: `ruff format .`
- Lint: `ruff check .`
- Type check: `mypy`

## Key Locations

### Core HTTP stack
- HTTP transport: `src/clicksign/_http/transport.py` — `UrllibHTTPClient`, `HttpxHTTPClient`, `HTTPClient`
- HTTP execution (retry, instrumentation, errors): `src/clicksign/_http/executor.py`
- Async stack: `src/clicksign/_async/` — `AsyncClient`, `AsyncClicksignClient`
- HTTP client (public API: get/post/patch/delete, raw_request): `src/clicksign/client.py`
- Bulk operations client (atomic ops, timeout-only retry): `src/clicksign/json_api/bulk_operations_client.py`
- Per-request options: `src/clicksign/request_options.py` — `RequestOptions(api_key, headers, timeouts)`
- Response metadata: `src/clicksign/response_metadata.py` — `ResponseMetadata(status, headers, request_id, duration_ms)`
- Raw escape-hatch response: `src/clicksign/raw_response.py`
- Request headers builder: `src/clicksign/request_headers.py`

### Configuration & entry points
- Global configuration: `src/clicksign/configuration.py`
- Facade client (explicit, no global state): `src/clicksign/clicksign_client.py` — `ClicksignClient`
- Thread-local client scoping: `src/clicksign/client_scope.py` — `client_scope()`
- Services (thread-local context manager): `src/clicksign/services.py`
- Bound resource (resource tied to explicit client): `src/clicksign/bound_resource.py`
- Module entry point: `src/clicksign/__init__.py`
- Version (read from REVISION): `src/clicksign/version.py`

### Error handling
- Error classes (retryable, status_code, errors list, rate_limit_*): `src/clicksign/errors.py`
- HTTP status → exception mapping: `src/clicksign/error_handler.py`
- Structured JSON:API error dataclass: `src/clicksign/api_error.py` — `ApiError(detail, title, code, source)`

### Resource layer
- Base resource class (CRUD, QueryProxy, last_response, relationship resolution): `src/clicksign/resource.py`
- JSON:API sideload index: `src/clicksign/json_api/included.py` — `IncludedIndex`
- Resource type → class registry: `src/clicksign/json_api/resource_registry.py`
- JSON:API parser: `src/clicksign/json_api/parser.py`
- JSON:API serializer: `src/clicksign/json_api/serializer.py`
- Query chain builder: `src/clicksign/json_api/query_builder.py`
- Atomic operations builder: `src/clicksign/json_api/operations.py`
- TypedDict per resource: `src/clicksign/types/resources.py`

### Resources
- `src/clicksign/resources/notarial/` — Envelope, Document, Signer, Requirement, BulkRequirement, SignatureWatcher, Event
- `src/clicksign/resources/auto_signature/` — Term (create-only)
- `src/clicksign/resources/acceptance_term/` — Whatsapp (no delete)
- `src/clicksign/resources/` — Webhook, User, Membership, Group, Template, TemplateField, Folder, EnvelopeBulkCreation, AccessControlList, Event

### Observability & identity
- Retry backoff (full jitter): `src/clicksign/retry_backoff.py`
- Instrumentation hooks: `src/clicksign/instrumentation.py`
- Instrumentation mixin (shared by Client and BulkOperationsClient): `src/clicksign/request_instrumentation.py`
- Dedicated logger (`clicksign.*`): `src/clicksign/log.py` — configurable via `CLICKSIGN_LOG=debug|info`
- User-Agent builder: `src/clicksign/user_agent.py`
- App info (set_app_info): `src/clicksign/app_info.py`
- Provider telemetry (opt-in): `src/clicksign/provider_telemetry.py`

### Webhook
- HMAC validation + event parsing: `src/clicksign/webhook.py` — `verify_signature`, `construct_event`

### Tests
- HTTP mock helpers: `tests/support/http_mock.py` — `mock_urlopen`, `make_response`, `make_http_error`
- Fake injectable HTTP client: `tests/support/fake_http_client.py` — `FakeHTTPClient`, `http_response`, `http_error`, `connection_error`
- JSON:API response fixtures: `tests/support/json_api_fixtures.py`
- Shared test setup: `tests/conftest.py`

## Architecture

### HTTP Transport
- `HTTPClient` Protocol — pluggable: inject via `http_client=` in `Client`, `BulkOperationsClient`, `Services`, `configure()`
- Default: `UrllibHTTPClient` (stdlib, no connection pool)
- Optional: `HttpxHTTPClient` (extra `[httpx]`) — enables connection pooling
- All three timeouts applied separately: `open_timeout` (TCP connect), `write_timeout` (body send), `read_timeout` (response)
- `http_executor.py` centralizes retry + instrumentation — used by both `Client` and `BulkOperationsClient`

### Two client patterns
| Pattern | When | How |
|---------|------|-----|
| **Global** | Single-tenant, scripts | `clicksign.configure(...)` → `Resource.list()` |
| **Explicit** | Multi-tenant, per-coroutine | `ClicksignClient(api_key=...)` → `client.notarial.envelopes.list()` |

`Services.use()` / `client_scope()` sets thread-local for the global pattern.

### Request options precedence
`per-request RequestOptions` > `thread-local client` > `global configure()`

### Error hierarchy
All inherit from `ClicksignError`. Each has: `message`, `status_code`, `request_id`, `response_body`, `errors: list[ApiError]`, `retryable`.
- `RateLimitError` adds `rate_limit_remaining`, `rate_limit_reset`
- `ApiError` dataclass: `detail`, `title`, `code`, `status`, `source` (with `pointer`)

### Resource conventions
- Inherit from `Resource`; dynamic attribute access via `__getattr__`
- `_parent_id` + `_base_path` pattern for nested resources (update/delete/reload build correct path)
- `last_response: ResponseMetadata` attached after every successful CRUD call
- `_included_index` carries sideloaded resources; relationships resolve lazily
- Notarial namespace groups envelope-flow resources
- Resources with restricted routes raise `NotImplementedError` for unsupported methods

### JSON:API sideload
- `QueryProxy.with_includes(*types)` sends `include=` param
- `IncludedIndex` indexes `included` by `(type, id)`
- `resource_registry.py` maps JSON:API type strings → Python resource classes
- Relationships resolve lazily via `__getattr__` (e.g., `envelope.folder`)

### Authorization
- Header: `Authorization: <token>` — **NO** `Bearer` prefix
- Raw token only; from `Configuration.api_key` or `RequestOptions.api_key`

### Version
- Read from `REVISION` file at import time — single source of truth

## Behavioral contract

**Read `docs/SDK_CONTRACT.md` before implementing anything.**
It defines HTTP headers, error mapping, retry algorithm, pagination, instrumentation event shapes, resource CRUD behavior.

**Read `docs/GAPS_VS_STRIPE.md` for architectural decisions.**
Documents planned/implemented gaps vs stripe-python; marks intentional design choices.

## Test conventions

- Tests use `FakeHTTPClient` (injected transport) — no `urllib` patching needed in most tests
- `FakeHTTPClient` accepts a queue of `http_response()`, `http_error()`, `connection_error()` objects
- `tests/support/http_mock.py` — legacy `mock_urlopen` still available for low-level client tests
- All tests use `tests/conftest.py` fixtures (reset global config + instrumentation between tests)
- UUIDs in tests: `'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'` pattern — never real sandbox UUIDs
- Every resource test module has a `test_resource_type` / `test_endpoint` block
- Error stubs: `{"errors": [{"detail": "msg"}]}`
- All behaviors in `docs/SDK_TEST_MATRIX.md` must be covered

## QueryProxy chain

```python
Resource.filter(status='running') \
        .order('-created') \
        .page(1).per(20) \
        .with_includes('folder') \
        .fields(envelopes=['name', 'status']) \
        .to_list()
```

- `Resource.list()` — no args, eager (1 page)
- `Resource.with_includes(*types)` — validates: str only, raises `ValueError` if empty or non-str
- Auto-pagination: `links.next` takes priority; item-count heuristic only as fallback
- `QueryProxy` is generic: `QueryProxy[T]` preserves resource type through chain

## Instrumentation

```python
clicksign.on_request(lambda e: ...)   # method, path, status, attempt, duration_ms
clicksign.on_retry(lambda e: ...)     # method, path, attempt, max_retries, error, wait_ms
clicksign.on_error(lambda e: ...)     # method, path, status, error, duration_ms
```

`BulkOperationsClient` publishes same events via shared `http_executor`.

## Logging

```python
# env var
CLICKSIGN_LOG=debug  # or info, warn, error

# programmatic
import logging
logging.getLogger("clicksign").setLevel(logging.DEBUG)
```

Redacts `Authorization` header. Body truncated at 4096 chars.

## Skills (slash commands)

- `/gen-resource <name>` — generate new resource + tests from Clicksign API source of truth
- `/sync-spec` — compare API routes with SDK resources, list gaps
- `/release` — release checklist

## Boas práticas (não repetir erros do passado)

- `BulkOperationsClient` retries only `TimeoutError`, not `ServerError` — intentional (atomic ops not idempotent)
- `with_includes` validates: raises `ValueError` for empty or non-str types
- `infer_resource_type` must guard against unnamed/anonymous classes
- Auto-pagination: `links.next` null → stop immediately; do NOT make extra request
- Callback exceptions must never propagate — catch with `except Exception` inside loop
- `hmac.compare_digest` required for webhook — never `==` string comparison
- Thread-local via `threading.local()` incompatible with asyncio/trio — use `ClicksignClient` per coroutine
- `RequestOptions` per call does NOT reset the thread-local client — only overrides specified fields
- `_base_path` and `_parent_id` are class-level `None`; use `or` not `getattr` with default for falsy-safe access
- `err` variable in `except` block deleted after block in Python 3.10+ — use different name in sibling blocks
- `Resource.list` shadows builtin `list` inside class body — use `builtins.list[T]` or `List[T]` in annotations

## Comments

- Comments only for non-obvious WHY — never for what the code does
- Docstrings on public API only, one-line max unless complex behavior
