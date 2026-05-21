# Retries e timeouts

A SDK expõe timeouts e retentativas na config global, em `Services`, `ClicksignClient` e `RequestOptions`. O backoff é exponencial com **full jitter** (`retry_backoff`); em 429 usa `max(jitter, Retry-After)` quando o header existir.

---

## Configuração global

```python
import clicksign

clicksign.configure(
    api_key="...",
    environment="sandbox",  # ou base_url explícito
    open_timeout=2.0,
    read_timeout=30.0,   # PDFs grandes
    write_timeout=30.0,
    max_retries=3,       # padrão 3; 0 = desliga retry automático
)
```

---

## Client explícito ou multi-tenant

```python
from clicksign import ClicksignClient, Services

client = ClicksignClient(
    api_key=tenant_token,
    environment="production",
    read_timeout=45.0,
    max_retries=2,
)

tenant = Services(api_key=tenant_token, environment="production", max_retries=2)

with tenant.use():
    from clicksign import Envelope
    Envelope.retrieve(envelope_id)
```

**Override por chamada** (precedência: request > client > global):

```python
from clicksign import RequestOptions

client.envelopes.retrieve(
    envelope_id,
    options=RequestOptions(max_retries=0, read_timeout=60.0),
)
```

---

## Bulk vs `Client`

| Erro | `Client` (resources) | `BulkOperationsClient` |
|------|-------------------|------------------------|
| Timeout / conexão | Sim | Sim |
| HTTP 429 | Sim (+ `Retry-After`) | **Não** |
| HTTP 5xx | Sim | **Não** |
| 401, 403, 404, 422 | Não | Não |

Total de tentativas HTTP = **1 + `max_retries`**.

`bulk_requirements` usa o bulk client da mesma config/client que `ClicksignClient` passa no construtor. Em multi-tenant com `Services`, o bulk segue a config global memoizada — veja [04-multi-client.md](04-multi-client.md).

---

## Observar retries em produção

```python
import clicksign

clicksign.on_retry(
    lambda e: print(
        f"retry {e['attempt']}/{e['max_retries']} "
        f"{e['method']} {e['path']} wait={e['wait_ms']}ms "
        f"{type(e['error']).__name__}"
    )
)

clicksign.on_error(
    lambda e: print(
        type(e["error"]).__name__,
        getattr(e["error"], "request_id", None),
    )
)
```

`:retry` dispara **antes** do `sleep`; `wait_ms` é o delay daquela tentativa.

---

## Rate limit além do retry automático

```python
from clicksign.errors import RateLimitError

try:
    client.envelopes.retrieve(envelope_id)
except RateLimitError as e:
    # e.retryable is True
    # e.rate_limit_remaining, e.rate_limit_reset quando a API envia headers
    raise
```

---

## Quando não aumentar `max_retries`

- **422 / 400** — corrigir payload.
- **401 / 403** — token ou ambiente (`sandbox` vs `production`).
- POST sem idempotência na API — retries podem repetir efeitos colaterais.

---

## Referência

- Contrato: [`SDK_CONTRACT.md`](../SDK_CONTRACT.md) §6
- Código: `src/clicksign/retry_backoff.py`, `src/clicksign/http_executor.py`
- Testes: `tests/clicksign/test_client.py`, `tests/clicksign/test_bulk_operations_client.py`
