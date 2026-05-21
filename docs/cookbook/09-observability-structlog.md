# Observabilidade — structlog

Integração da SDK com [structlog](https://www.structlog.org/) via hooks globais. Não há dependência structlog no pacote `clicksign` — instale no seu app.

```bash
pip install structlog
```

## Setup

```python
import structlog
import clicksign

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
log = structlog.get_logger("clicksign")

clicksign.configure(api_key="...", environment="sandbox", log="info")

clicksign.on_request(
    lambda e: log.info(
        "clicksign.request",
        method=e["method"],
        path=e["path"],
        status=e["status"],
        attempt=e["attempt"],
        duration_ms=e["duration_ms"],
    )
)

clicksign.on_retry(
    lambda e: log.warning(
        "clicksign.retry",
        method=e["method"],
        path=e["path"],
        attempt=e["attempt"],
        max_retries=e["max_retries"],
        wait_ms=e["wait_ms"],
        error=type(e["error"]).__name__,
    )
)

clicksign.on_error(
    lambda e: log.error(
        "clicksign.error",
        method=e["method"],
        path=e["path"],
        status=e.get("status"),
        error=type(e["error"]).__name__,
        detail=str(e["error"]),
        request_id=getattr(e["error"], "request_id", None),
        # Do not log e["error"].response_body — may contain PII
    )
)
```

## Correlation id por request

Propague o id do seu middleware para a API:

```python
from clicksign import ClicksignClient, RequestOptions, correlation_id

client = ClicksignClient(api_key="...", environment="sandbox")

def fetch_envelope(envelope_id: str, request_id: str):
    return client.envelopes.retrieve(
        envelope_id,
        options=RequestOptions(headers=correlation_id(request_id)),
    )
```

## Testes

`tests/conftest.py` chama `clicksign.instrumentation.clear()` após cada teste — evita callbacks vazando entre exemplos.

## Referência

- [`OBSERVABILITY.md`](../OBSERVABILITY.md) — PII em `on_error`
- OpenTelemetry: [`10-observability-opentelemetry.md`](10-observability-opentelemetry.md)
- Métricas: [`11-observability-metrics.md`](11-observability-metrics.md)
