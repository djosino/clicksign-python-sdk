# Observabilidade — Clicksign Python SDK

A SDK não depende de APM nem OpenTelemetry. Expõe **hooks leves** (`clicksign.on_request`, `on_retry`, `on_error`), **logging integrado** (`clicksign.log` / `CLICKSIGN_LOG`) e `Configuration.logger` para erros em callbacks customizados. Você conecta ao stack que já usa (structlog, OTel manual, Sentry).

---

## Logging integrado

Ative logs HTTP sem registrar callbacks manualmente:

```python
import clicksign

clicksign.log = "info"          # resumo: method, path, status, duration
clicksign.log = "debug"         # inclui headers (Authorization redacted) e bodies truncados
clicksign.configure(log="warn") # retries
# export CLICKSIGN_LOG=debug
```

| Nível | O que registra |
|-------|----------------|
| `debug` | Request/response completos (headers sanitizados, body até 4 KiB) |
| `info` | Resumo por tentativa HTTP |
| `warn` | Retries antes do backoff |
| `error` | Falha final (após esgotar retries) |

Logger stdlib: `logging.getLogger("clicksign")`. Se sua app já configura handlers para esse logger, a SDK só ajusta o nível; caso contrário, adiciona um `StreamHandler` simples.

`Authorization` e headers sensíveis nunca aparecem nos logs. Os hooks `on_*` continuam disponíveis para métricas, tracing ou logs estruturados no formato da sua aplicação.

---

## Eventos disponíveis (hooks)

| Evento | Quando dispara | Onde |
|--------|----------------|------|
| `request` | Após cada tentativa HTTP (sucesso ou erro HTTP) | `Client`, `BulkOperationsClient` |
| `retry` | Antes do `sleep`, quando vai retentar | `Client` (5xx/429/timeout), `BulkOperationsClient` (timeout) |
| `error` | Quando uma exceção `ClicksignError` (ou `TimeoutError`) será relançada | `Client`, `BulkOperationsClient` |

> Webhooks de **entrada** (seu controller) não passam por esses hooks — só chamadas de saída à API.

---

## Payload por evento

### `request`

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `method` | `str` | `"get"`, `"post"`, `"patch"`, `"delete"` |
| `path` | `str` | Caminho relativo (ex. `/envelopes`) |
| `attempt` | `int` | Número da tentativa (1 na primeira) |
| `status` | `int \| None` | HTTP status; `None` em timeout de rede |
| `duration_ms` | `float` | Duração da tentativa em ms |

### `retry`

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `method`, `path`, `attempt` | — | Igual ao request |
| `max_retries` | `int` | `configure(max_retries=...)` ou `RequestOptions` |
| `error` | `Exception` | `ServerError`, `RateLimitError`, `TimeoutError` |
| `wait_ms` | `float` | Delay com jitter antes da próxima tentativa |

### `error`

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `method`, `path`, `attempt` | — | Contexto da chamada |
| `error` | `Exception` | Instância `clicksign.errors.*` |
| `status` | `int \| None` | HTTP quando aplicável |
| `duration_ms` | `float` | Tempo até a falha |

Em erros HTTP, `request` e `error` disparam na mesma falha (request com status de erro, depois `error` com a exceção).

---

## Correlation id (`X-Correlation-Id`)

Propague o id da sua requisição HTTP ou job para chamadas da SDK:

```python
from clicksign import ClicksignClient, RequestOptions, correlation_id

client = ClicksignClient(api_key="...", environment="sandbox")
client.envelopes.retrieve(
    "uuid",
    options=RequestOptions(headers=correlation_id("req-abc-123")),
)
# equivalent: headers={"X-Correlation-Id": "req-abc-123"}
```

Helper: `clicksign.correlation_id(value)` → `dict` pronto para `RequestOptions.headers`. Constante: `CORRELATION_ID_HEADER`.

Em falhas, use `error.request_id` (resposta `X-Request-Id` da Clicksign) para suporte — distinto do correlation id que **você** envia.

---

## Python — logs estruturados (stdlib)

```python
import logging
import clicksign

clicksign.configure(api_key="...", environment="sandbox", log="info")

# Ou integre com o logging da sua app:
logger = logging.getLogger("clicksign")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
clicksign.set_log("debug")

clicksign.on_request(lambda e: logger.info("clicksign.request", extra=e))
```

Example — structlog: [`examples/09-observability-structlog.md`](examples/09-observability-structlog.md).

---

## Python — PII em `on_error`

O payload do hook **não** inclui `response_body` por padrão. Se você acessar a exceção, **evite** logar ou enviar ao Sentry/Datadog:

- `error.response_body` — JSON completo da API (pode ter e-mail, CPF, conteúdo de documento)
- Atributos de resources em mensagens de validação

**Faça:**

```python
clicksign.on_error(
    lambda e: logger.error(
        "clicksign.error",
        method=e["method"],
        path=e["path"],
        status=e.get("status"),
        error=type(e["error"]).__name__,
        detail=str(e["error"]),
        request_id=getattr(e["error"], "request_id", None),
    )
)
```

O logger integrado da SDK (`CLICKSIGN_LOG=debug`) trunca bodies e redige `Authorization`; callbacks customizados são responsabilidade do host app.

---

## Python — OpenTelemetry e métricas

- OpenTelemetry manual: [`examples/10-observability-opentelemetry.md`](examples/10-observability-opentelemetry.md)
- Prometheus / StatsD via hooks: [`examples/11-observability-metrics.md`](examples/11-observability-metrics.md)

Não há módulo `clicksign.metrics` no core — hooks são o ponto de extensão.

---

## Python — testes

`tests/conftest.py` chama `clicksign.instrumentation.clear()` após cada teste para não vazar callbacks entre casos.

---

## Python — Sentry (ou similar)

```python
import clicksign
from clicksign.errors import ClicksignError

def on_error(payload: dict) -> None:
    err = payload["error"]
    if not isinstance(err, ClicksignError):
        return
    sentry_sdk.capture_exception(
        err,
        extras={
            "clicksign_method": payload["method"],
            "clicksign_path": payload["path"],
            "clicksign_status": payload.get("status"),
            "clicksign_request_id": getattr(err, "request_id", None),
        },
    )

clicksign.on_error(on_error)
```

Não envie `response_body` inteiro se contiver PII.

---

## Python — métricas e OpenTelemetry

Receitas completas:

- [`examples/11-observability-metrics.md`](examples/11-observability-metrics.md) — Prometheus / StatsD via hooks
- [`examples/10-observability-opentelemetry.md`](examples/10-observability-opentelemetry.md) — spans manuais

Normalize `path` em tags (substituir UUIDs por `:id`) para evitar cardinalidade alta.

---

## O que o SDK não faz (ainda)

- Spans OTel embutidos
- Export automático para Datadog/New Relic
- Correlação `request_id` da API com trace ID (copie `getattr(payload["error"], "request_id", None)` no hook)
- Retry automático em 5xx/429 no `BulkOperationsClient` (só timeout; ver [01-retries](examples/01-retries.md))

---

## Referência

- README: [Timeouts, retry e instrumentação](../README.md#timeouts-retry-e-instrumentação)
- Retries: [examples/01-retries.md](examples/01-retries.md)
- Arquitetura dos hooks: [ARCHITECTURE.md](ARCHITECTURE.md)
- Falhas silenciosas em callback: [TROUBLESHOOTING.md](TROUBLESHOOTING.md#instrumentação-some-erro-do-callback)
