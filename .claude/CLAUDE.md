# clicksign-python-sdk

## Testing

- Run all tests: `pytest`
- Run with coverage: `pytest --cov=clicksign --cov-report=term-missing`
- Format: `ruff format .`
- Lint: `ruff check .`
- Type check: `mypy src/`

## Key Locations

- HTTP client (requests, headers, auth, retry, instrumentation): `src/clicksign/client.py`
- Instrumentation shared mixin: `src/clicksign/request_instrumentation.py`
- Retry backoff with full jitter: `src/clicksign/retry_backoff.py`
- Base resource class (CRUD, QueryProxy): `src/clicksign/resource.py`
- Error handling (HTTP status → exception): `src/clicksign/error_handler.py`
- Error classes (retryable, status_code, rate_limit_*): `src/clicksign/errors.py`
- Instrumentation hooks: `src/clicksign/instrumentation.py`
- Thread-local client scoping: `src/clicksign/services.py`
- Webhook HMAC validation: `src/clicksign/webhook.py`
- JSON:API layer: `src/clicksign/json_api/` (parser, serializer, query_builder, operations)
- Bulk operations client: `src/clicksign/json_api/bulk_operations_client.py`
- Resources: `src/clicksign/resources/` (notarial/, auto_signature/, acceptance_term/, root)
- Version (read from REVISION file): `src/clicksign/version.py`
- Test fixtures: `tests/support/json_api_fixtures.py`
- Test shared context: `tests/conftest.py`

## Architecture

- Minimal runtime dependencies — prefer stdlib (`urllib`, `json`, `hmac`, `hashlib`)
- If `httpx` is adopted for async support, it's the only runtime dep allowed
- JSON:API protocol (v1.1) for all requests/responses
- `Authorization: <token>` header — **NO** `Bearer` prefix
- Version read from `REVISION` file at import time — single source of truth
- Resources inherit from `clicksign.Resource`; dynamic attribute access via `__getattr__`
- Notarial namespace groups envelope-flow resources
- `_parent_id` pattern for nested resources so `update`/`delete`/`reload` work
- `RequestInstrumentation` mixin shared by `Client` and `BulkOperationsClient`
- `RetryBackoff` shared module — full jitter, capped at 30s
- Thread-local client via `threading.local()` in `Services`
- `Clicksign.configure(...)` must be called before threads spawn

## Behavioral contract

**Read `docs/SDK_CONTRACT.md` before implementing anything.**
It defines exact HTTP headers, error mapping, retry algorithm, pagination logic,
instrumentation event shapes, and resource CRUD behavior.

## Test conventions

- Use `pytest` + `responses` (or `pytest-httpx` if httpx adopted) — no real network
- All tests use fixtures from `tests/conftest.py` that configure SDK with a test base URL
- UUIDs in tests: `'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'` pattern — never real sandbox UUIDs
- Every resource test module has a `test_resource_configuration` block (`resource_type`, `endpoint`)
- Stubs de erro: `{"errors": [{"detail": "msg"}]}`
- `conftest.py` resets global config and clears instrumentation between tests
- All behaviors in `docs/SDK_TEST_MATRIX.md` must be covered

## QueryProxy chain

```python
Resource.filter(status='running') \
        .order('-created') \
        .page(1).per(20) \
        .with_includes('folder') \
        .to_list()
```

- `Resource.list()` — no args, eager list
- `Resource.with_includes(*types)` — canonical JSON:API sideload (str only, validated)
- Auto-pagination uses `links.next` first; item-count heuristic only as fallback

## Instrumentation

```python
Clicksign.on_request(lambda e: ...)
Clicksign.on_retry(lambda e: ...)
Clicksign.on_error(lambda e: ...)
```

`BulkOperationsClient` also publishes instrumentation events via shared mixin.

## Skills (slash commands)

- `/gen-resource <name>` — generate a new resource + tests from the Clicksign API source of truth
- `/sync-spec` — compare API routes with SDK resources, list gaps
- `/release` — release checklist

## Boas práticas (não repetir erros do passado)

- `BulkOperationsClient` retries only `TimeoutError`, not `ServerError` — intentional
- `with_includes` validates: raises `ValueError` for empty or non-str types
- `infer_resource_type` must guard against unnamed/anonymous classes
- `fetch_auto_pages` uses `links['next']` when present — do NOT make extra request when null
- Callback exceptions must never propagate — catch with `except Exception` inside loop
- `hmac.compare_digest` required for webhook — never `==` string comparison
- Thread-local via `threading.local()` incompatible with async (asyncio/trio) — document clearly

## Comments

- Comments only for non-obvious WHY — never for what the code does
- Docstrings on public API only, one-line max unless complex behavior
