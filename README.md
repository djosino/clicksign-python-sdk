# Clicksign Python SDK

Python client for the [Clicksign API v3](https://developers.clicksign.com/) (JSON:API).

**Status:** beta — core notarial + admin resources, sync/async clients, webhooks, pagination, and observability hooks. See [`docs/SDK_CONTRACT.md`](docs/SDK_CONTRACT.md) and [`docs/SDK_ROADMAP.md`](docs/SDK_ROADMAP.md).

**Reference implementation:** [`../clicksign-ruby-sdk`](../clicksign-ruby-sdk)

---

## Documentation

**Index:** [`docs/README.md`](docs/README.md) — mapa por tema (contrato, gaps, examples, observabilidade, paginação).

| Start here | Also |
|------------|------|
| [`SDK_CONTRACT.md`](docs/SDK_CONTRACT.md) | [`SPEC.md`](docs/SPEC.md), [`WORKFLOW.md`](docs/WORKFLOW.md) |
| [`SDK_CLIENT_GAPS.md`](docs/SDK_CLIENT_GAPS.md) | [`SDK_ROADMAP.md`](docs/SDK_ROADMAP.md), [`SDK_TEST_MATRIX.md`](docs/SDK_TEST_MATRIX.md) |
| [`OBSERVABILITY.md`](docs/OBSERVABILITY.md) | [`PAGINATION.md`](docs/PAGINATION.md), [`TYPES.md`](docs/TYPES.md) |
| [`examples/`](docs/examples/) | [`ARCHITECTURE.md`](docs/ARCHITECTURE.md) |

### API surface (`ClicksignClient`)

| Namespace | Resource | Import alternativo |
|-----------|----------|-------------------|
| `client.notarial.envelopes` | `Envelope` | `from clicksign import Envelope` |
| `client.notarial.documents` | `Document` | `from clicksign import Document` |
| `client.notarial.signers` | `Signer` | `from clicksign import Signer` |
| `client.notarial.requirements` | `Requirement` | `from clicksign import Requirement` |
| `client.notarial.bulk_requirements` | `BulkRequirement` | `from clicksign import BulkRequirement` |
| `client.notarial.signature_watchers` | `SignatureWatcher` | `from clicksign.resources.notarial.signature_watcher import SignatureWatcher` |
| `client.notarial.events` | `Event` (notarial) | `from clicksign.resources.notarial.event import Event` |
| `client.webhooks` | `Webhook` | `from clicksign.resources.webhook import Webhook` |
| `client.users` | `User` | `from clicksign.resources.user import User` |
| `client.templates` / `template_fields` | `Template`, `TemplateField` | `from clicksign.resources.template import Template` |
| `client.memberships` / `groups` | `Membership`, `Group` | imports em `clicksign.resources.*` |
| `client.folders` | `Folder` | `from clicksign.resources.folder import Folder` |
| `client.events` | `Event` (conta) | `from clicksign.resources.event import Event` |
| `client.access_control_lists` | `AccessControlList` | `from clicksign.resources.access_control_list import AccessControlList` |
| `client.envelope_bulk_creations` | `EnvelopeBulkCreation` | import direto do módulo |
| `client.acceptance_term.whatsapps` | `Whatsapp` | `from clicksign.resources.acceptance_term.whatsapp import Whatsapp` |
| `client.auto_signature.terms` | `Term` | `from clicksign.resources.auto_signature.term import Term` |

Endpoints sem resource dedicado: `client.raw_request()` + `client.deserialize()`.

---

## Requirements

- Python >= 3.10
- No runtime dependencies (stdlib only)

Optional extras: `pip install clicksign[httpx]` for connection pooling and lower latency under load; `pip install clicksign[async]` for asyncio.

---

## Usage

The SDK supports two main patterns. Both call the same API; choose based on how your app manages credentials and concurrency.

### Global configuration (single tenant)

Configure once at startup, then import resource classes directly. Best for scripts, workers with one API key per process, and quick prototypes.

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

Instrumentation hooks are also global:

```python
clicksign.on_request(lambda payload: print(payload["method"], payload["path"]))
```

Built-in HTTP logging:

```python
import clicksign

clicksign.log = "debug"  # or: clicksign.configure(..., log="info")
# export CLICKSIGN_LOG=debug

# Uses stdlib logger "clicksign"; Authorization is never logged.
```

See [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md) for hooks, logging levels, structlog/OpenTelemetry/metrics examples, and **avoiding PII** in custom `on_error` handlers.

**Correlation:** pass `X-Correlation-Id` per call via `RequestOptions(headers=correlation_id("your-id"))` to tie SDK requests to your web request or job id. The API may echo correlation in support; use `error.request_id` from `X-Request-Id` on failures for Clicksign support tickets.

### Explicit client (`ClicksignClient`)

Create a client instance when you need multiple API keys in the same process, clearer discoverability, or no global state.

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

Each `ClicksignClient` owns its own HTTP and bulk clients. Pass a custom transport if needed:

```python
from clicksign import ClicksignClient, UrllibHTTPClient

client = ClicksignClient(
    api_key="YOUR_API_KEY",
    environment="sandbox",
    http_client=UrllibHTTPClient(proxy="http://proxy:8080"),
)
```

### HTTP transport and connection pool

**Default:** `UrllibHTTPClient` (stdlib only, **no** connection pool — one TCP/TLS handshake per request). Fine for scripts and low QPS.

**High concurrency** (web apps, workers with many API calls per second): install httpx and inject a shared client:

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

`AsyncClicksignClient` (`clicksign[async]`) also uses `httpx` with a connection pool on the event loop.

Trade-offs and mitigations: [`docs/examples/08-production-limitations.md`](docs/examples/08-production-limitations.md) · singleton recipe: [`docs/examples/12-http-connection-pool.md`](docs/examples/12-http-connection-pool.md).

### Multi-tenant (thread-local)

For web apps or job queues where each request/job uses a different API key, use `Services` to bind a client to the current thread without global `configure()`:

```python
from clicksign import Envelope, Services

tenant = Services(api_key="TENANT_API_KEY", environment="sandbox")

with tenant.use():
    Envelope.list()  # routed through this tenant's client
```

`Services.use()` sets both the HTTP client and the bulk client for the thread. Prefer `ClicksignClient` directly when running under async/fiber runtimes where thread-local context may not propagate.

### Async (FastAPI, asyncio)

Install the optional extra: `pip install clicksign[async]` (requires `httpx`). The API is unchanged; the client runs non-blocking HTTP on your event loop.

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

Do not use `Services.use()` inside asyncio — pass an explicit `AsyncClicksignClient`. Bulk atomic operations remain on the sync `ClicksignClient.bulk` client for now.

Per-request overrides (api key, headers, timeouts, `max_retries`) without switching client. Default retry count is **3** (`max_retries=0` disables retries on a single call):

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

Precedence: **options on the call** override the client's defaults (thread-local and global config are unchanged).

### Unmapped or beta endpoints

Use `raw_request` for paths not yet covered by resource classes, then optionally deserialize:

```python
from clicksign import ClicksignClient, Envelope

client = ClicksignClient(api_key="YOUR_API_KEY", environment="sandbox")

raw = client.raw_request("get", "/beta/feature")
print(raw.status, raw.request_id, raw.body)

envelope = client.deserialize(raw, Envelope)
print(envelope.last_response.status)
```

After any successful call, inspect HTTP metadata via `client.last_response`, `client.bulk_last_response`, or `resource.last_response` (`status`, `request_id`, rate limit headers).

### Structured validation errors

On 400/422 responses, exceptions expose the full JSON:API `errors` array:

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

Map field errors in forms using `source.pointer` or `source.parameter` from each entry in `err.errors` / `err.api_errors`.

### JSON:API sideload (`included`)

Request related resources in one call with `with_includes()` and access them as attributes:

```python
envelopes = client.envelopes.with_includes("folder").to_list()
print(envelopes[0].folder.name)  # sideloaded Folder, no extra HTTP call
print(envelopes[0].included_resources)  # all entries from `included`
```

**Limits:** only relationships present in `included` are resolved (otherwise `envelope.folder` is `None`); nested includes depend on what the API returns; unknown types fall back to base `Resource`.

### User-Agent and app identification

Every request includes a `User-Agent` header identifying the SDK and Python runtime. Host apps can add their own identifier:

```python
import clicksign

clicksign.set_app_info("My CRM", "2.1.0", "https://example.com")
# User-Agent: clicksign-python/x.y.z Python/3.10.x My_CRM/2.1.0
```

Per-client override:

```python
from clicksign import AppInfo, ClicksignClient

client = ClicksignClient(api_key="...", app_info=AppInfo(name="Tenant", version="1.0"))
```

### Provider telemetry (opt-in)

The SDK can send anonymized latency metrics to Clicksign (no API keys, no request/response bodies). Disabled by default until you opt in:

```python
clicksign.configure(enable_telemetry=True)

# opt-out
clicksign.configure(enable_telemetry=False)
# or
clicksign.set_enable_telemetry(False)
```

Custom endpoint (staging): `configure(enable_telemetry=True, telemetry_url="https://sandbox.clicksign.com/sdk/telemetry/v1/events")`.

Metrics include SDK version, Python version, HTTP method, normalized path (UUIDs masked), status, and duration.

### Which pattern to use?

| Pattern | When |
|---------|------|
| `configure()` + resources | One API key per process; scripts; legacy style |
| `ClicksignClient` | Multiple keys; explicit dependencies; new application code |
| `Services.use()` | Multi-tenant Rails/Django/Celery-style apps (one thread per request/job) |
| `HttpxHTTPClient` (shared) | High QPS per worker; see [connection pool](docs/examples/12-http-connection-pool.md) |

See [`docs/WORKFLOW.md`](docs/WORKFLOW.md) for a full signing workflow and [`docs/examples/`](docs/examples/) for scenario-specific recipes.

---

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src/
```
