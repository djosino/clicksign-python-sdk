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
| `:request` | Após cada tentativa HTTP (sucesso ou erro HTTP) | `Client`, `BulkOperationsClient` |
| `:retry` | Antes do `sleep`, quando vai retentar | `Client` (5xx/429/timeout), `BulkOperationsClient` (timeout) |
| `:error` | Quando uma exceção `Clicksign::Error` (ou `TimeoutError`) será relançada | `Client`, `BulkOperationsClient` |

> Webhooks de **entrada** (seu controller) não passam por esses hooks — só chamadas de saída à API.

---

## Payload por evento

### `:request`

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `method` | Symbol | `:get`, `:post`, `:patch`, `:delete` |
| `path` | String | Caminho relativo (ex. `/envelopes`) |
| `attempt` | Integer | Número da tentativa (1 na primeira) |
| `status` | Integer ou nil | HTTP status; `nil` em timeout de rede |
| `duration_ms` | Float | Duração da tentativa em ms |

### `:retry`

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `method`, `path`, `attempt` | — | Igual ao request |
| `max_retries` | Integer | Config da gem |
| `error` | Exception | `ServerError`, `RateLimitError`, `TimeoutError` |
| `wait_ms` | Integer | Delay com jitter antes da próxima tentativa |

### `:error`

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `method`, `path`, `attempt` | — | Contexto da chamada |
| `error` | Exception | Instância `Clicksign::*` |
| `status` | Integer ou nil | HTTP quando aplicável |
| `duration_ms` | Float | Tempo até a falha |

Em erros HTTP, `:request` e `:error` disparam na mesma falha (request com status de erro, depois error com a exceção).

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

## Rails — logs estruturados (Ruby SDK)

```ruby
# config/initializers/clicksign.rb
require 'clicksign'

Clicksign.configure do |c|
  c.api_key     = ENV.fetch('CLICKSIGN_API_KEY')
  c.environment = Rails.env.production? ? :production : :sandbox
  c.max_retries = 2
  c.logger      = Rails.logger
end

Clicksign.on_request do |e|
  Rails.logger.info(
    message: 'clicksign.request',
    method: e[:method],
    path: e[:path],
    status: e[:status],
    duration_ms: e[:duration_ms],
    attempt: e[:attempt],
  )
end

Clicksign.on_retry do |e|
  Rails.logger.warn(
    message: 'clicksign.retry',
    method: e[:method],
    path: e[:path],
    attempt: e[:attempt],
    max_retries: e[:max_retries],
    wait_ms: e[:wait_ms],
    error: e[:error].class.name,
  )
end

Clicksign.on_error do |e|
  Rails.logger.error(
    message: 'clicksign.error',
    method: e[:method],
    path: e[:path],
    status: e[:status],
    error: e[:error].class.name,
    detail: e[:error].message,
    request_id: e[:error].respond_to?(:request_id) ? e[:error].request_id : nil,
  )
end
```

Erros **dentro** dos callbacks não quebram a requisição; com `c.logger` definido, aparecem como `instrumentation callback error`.

---

## Sentry (ou similar)

```ruby
Clicksign.on_error do |e|
  err = e[:error]
  next unless err.is_a?(Clicksign::Error)

  Sentry.capture_exception(err, extra: {
    clicksign_method: e[:method],
    clicksign_path: e[:path],
    clicksign_status: e[:status],
    clicksign_request_id: err.request_id,
  })
end
```

Não envie `response_body` inteiro ao Sentry se contiver PII — filtre no seu projeto.

---

## Métricas simples (contador + histograma)

Exemplo conceitual com qualquer cliente StatsD/Prometheus:

```ruby
Clicksign.on_request do |e|
  next unless e[:status]

  statsd.increment('clicksign.requests', tags: [
    "method:#{e[:method]}",
    "status:#{e[:status]}",
  ])
  statsd.timing('clicksign.duration_ms', e[:duration_ms], tags: ["path:#{e[:path]}"])
end

Clicksign.on_retry do |e|
  statsd.increment('clicksign.retries', tags: ["error:#{e[:error].class.name}"])
end
```

Normalize `path` se cardinality explodir (ex. substituir UUIDs por `:id`).

---

## OpenTelemetry (bridge opcional, sem gem OTel obrigatória)

Se o projeto já usa OpenTelemetry Ruby, registre spans nos callbacks — a SDK não cria spans automaticamente.

```ruby
# config/initializers/clicksign_otel.rb
# Requer gems opentelemetry-sdk e opentelemetry-api no host app (não na clicksign-ruby-sdk).

tracer = OpenTelemetry.tracer_provider.tracer('clicksign-ruby-sdk')

Clicksign.on_request do |e|
  next unless e[:status] && e[:status] < 400

  tracer.in_span(
    "clicksign #{e[:method]} #{e[:path]}",
    attributes: {
      'http.method' => e[:method].to_s.upcase,
      'http.route' => e[:path],
      'http.status_code' => e[:status],
      'clicksign.attempt' => e[:attempt],
    },
  ) do |span|
    span['clicksign.duration_ms'] = e[:duration_ms]
  end
end

Clicksign.on_error do |e|
  tracer.in_span('clicksign error', attributes: {
    'http.method' => e[:method].to_s.upcase,
    'http.route' => e[:path],
    'clicksign.error' => e[:error].class.name,
  }) do |span|
    span.record_exception(e[:error]) if span.respond_to?(:record_exception)
    span.status = OpenTelemetry::Trace::Status.error
  end
end
```

Para retries, incremente um atributo ou evento no span pai da sua aplicação, ou use `on_retry` com `span.add_event('retry', attributes: { 'wait_ms' => e[:wait_ms] })` se mantiver referência ao span ativo no middleware.

---

## Testes — não vazar callbacks

```ruby
# spec/spec_helper.rb ou support
RSpec.configure do |config|
  config.after do
    Clicksign::Instrumentation.clear
  end
end
```

Em specs que registram `on_request`, chame `Instrumentation.clear` no `after` do exemplo.

---

## O que a gem não faz (ainda)

- Spans OTel embutidos
- Export automático para Datadog/New Relic
- Correlação `request_id` da API com trace ID (você pode copiar `e[:error].request_id` para o span manualmente)
- Retry automático em 5xx/429 no `BulkOperationsClient` (só timeout; ver [01-retries](examples/01-retries.md))

---

## Referência

- README: [Timeouts, retry e instrumentação](../README.md#timeouts-retry-e-instrumentação)
- Retries: [examples/01-retries.md](examples/01-retries.md)
- Arquitetura dos hooks: [ARCHITECTURE.md](ARCHITECTURE.md)
- Falhas silenciosas em callback: [TROUBLESHOOTING.md](TROUBLESHOOTING.md#instrumentação-some-erro-do-callback)
