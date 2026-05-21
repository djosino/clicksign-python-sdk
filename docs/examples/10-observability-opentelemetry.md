# Observabilidade — OpenTelemetry (manual)

A SDK **não** cria spans automaticamente. Use `on_request` / `on_error` para bridge com OpenTelemetry já configurado no host app.

```bash
pip install opentelemetry-api opentelemetry-sdk
```

## Exemplo

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

import clicksign

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    SimpleSpanProcessor(ConsoleSpanExporter())
)
tracer = trace.get_tracer("clicksign-python-sdk")

clicksign.configure(api_key="...", environment="sandbox")

def _on_request(e: dict) -> None:
    status = e.get("status")
    if status is None or status >= 400:
        return
    with tracer.start_as_current_span(
        f"clicksign {e['method']} {e['path']}",
        attributes={
            "http.method": e["method"].upper(),
            "http.route": e["path"],
            "http.status_code": status,
            "clicksign.attempt": e["attempt"],
            "clicksign.duration_ms": e["duration_ms"],
        },
    ):
        pass

def _on_error(e: dict) -> None:
    err = e["error"]
    with tracer.start_as_current_span(
        "clicksign error",
        attributes={
            "http.method": e["method"].upper(),
            "http.route": e["path"],
            "clicksign.error": type(err).__name__,
        },
    ) as span:
        span.record_exception(err)
        span.set_status(trace.Status(trace.StatusCode.ERROR))

clicksign.on_request(_on_request)
clicksign.on_error(_on_error)
```

## `request_id` da API

Em falhas, copie `error.request_id` (header `X-Request-Id` da resposta) para o span ativo da sua app:

```python
def on_error(e: dict) -> None:
    err = e["error"]
    rid = getattr(err, "request_id", None)
    span = trace.get_current_span()
    if rid and span.is_recording():
        span.set_attribute("clicksign.request_id", rid)
```

## Retries

Use `on_retry` para eventos no span pai ou métricas:

```python
clicksign.on_retry(
    lambda e: trace.get_current_span().add_event(
        "clicksign.retry",
        {"wait_ms": e["wait_ms"], "attempt": e["attempt"]},
    )
)
```

## Referência

- [`OBSERVABILITY.md`](../OBSERVABILITY.md)
