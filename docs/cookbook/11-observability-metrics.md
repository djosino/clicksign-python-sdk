# Observabilidade — métricas (Prometheus / StatsD)

Contadores e latência via hooks, sem módulo `clicksign.metrics` no core. Adapte ao cliente que você já usa (statsd, prometheus_client, Datadog, etc.).

## Exemplo (StatsD-style)

```python
import clicksign

# statsd = seu cliente configurado
statsd = ...

def normalize_path(path: str) -> str:
    """Reduce cardinality: replace UUID segments with :id."""
    import re

    return re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        ":id",
        path,
        flags=re.I,
    )

def on_request_metrics(e: dict) -> None:
    if not e.get("status"):
        return
    path = normalize_path(e["path"])
    statsd.increment(
        "clicksign.requests",
        tags=[f"method:{e['method']}", f"status:{e['status']}", f"path:{path}"],
    )
    statsd.timing(
        "clicksign.duration_ms",
        e["duration_ms"],
        tags=[f"path:{path}"],
    )

clicksign.on_request(on_request_metrics)

clicksign.on_retry(
    lambda e: statsd.increment(
        "clicksign.retries",
        tags=[f"error:{type(e['error']).__name__}"],
    )
)

clicksign.on_error(
    lambda e: statsd.increment(
        "clicksign.errors",
        tags=[
            f"method:{e['method']}",
            f"status:{e.get('status')}",
            f"error:{type(e['error']).__name__}",
        ],
    )
)
```

## Prometheus (conceitual)

```python
from prometheus_client import Counter, Histogram

REQUESTS = Counter(
    "clicksign_requests_total",
    "Clicksign API requests",
    ["method", "path", "status"],
)
DURATION = Histogram(
    "clicksign_request_duration_seconds",
    "Request duration",
    ["method", "path"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

def on_request_prom(e: dict) -> None:
    if not e.get("status"):
        return
    path = normalize_path(e["path"])
    REQUESTS.labels(e["method"], path, str(e["status"])).inc()
    DURATION.labels(e["method"], path).observe(e["duration_ms"] / 1000.0)

clicksign.on_request(on_request_prom)
```

## PII e payloads

**Não** incremente métricas com labels derivados de `response_body` ou atributos de signatários. Use apenas `method`, `path` normalizado, `status`, `error` class name.

Em logs/APM paralelos, o mesmo vale para `on_error` — veja structlog cookbook.

## Referência

- [`OBSERVABILITY.md`](../OBSERVABILITY.md)
- [`09-observability-structlog.md`](09-observability-structlog.md)
