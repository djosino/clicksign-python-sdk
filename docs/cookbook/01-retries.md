# Retries e timeouts

A gem expõe timeouts e retentativas automáticas na configuração global, em `Clicksign::Services` e em `Clicksign::Client.new`. O backoff usa exponencial com **full jitter** (`Clicksign::RetryBackoff`) para reduzir picos quando muitos clientes falham ao mesmo tempo.

---

## Configuração global (Rails initializer)

```ruby
# config/initializers/clicksign.rb
require 'clicksign'

Clicksign.configure do |c|
  c.api_key       = ENV.fetch('CLICKSIGN_API_KEY')
  c.environment   = :production   # ou :sandbox
  c.open_timeout  = 2             # conexão (s) — padrão 2
  c.read_timeout  = 30            # leitura (s) — aumente para PDFs grandes
  c.write_timeout = 30            # escrita (s)
  c.max_retries   = 3             # 0 = desligado (padrão)
end
```

---

## Multi-conta com retry por tenant

`Clicksign::Services` repassa timeouts e `max_retries` para o `Client` usado dentro de `use`:

```ruby
tenant_service = Clicksign::Services.new(
  api_key: tenant.clicksign_token,
  environment: :production,
  read_timeout: 45,
  max_retries: 2
)

tenant_service.use do
  Clicksign::Resources::Notarial::Envelope.retrieve(envelope_id)
end
```

> **Nota:** `BulkRequirement` usa `Clicksign.bulk_operations_client`, criado a partir da **config global** (`Clicksign.configure`). Em apps multi-tenant, defina `max_retries` no initializer global ou execute bulk jobs com a mesma política de retry para todos os tenants. Hooks `:request`/`:retry`/`:error` funcionam no bulk; retry automático continua **só em timeout**. Ver [Vários clientes](04-multi-client.md).

---

## O que é retentado automaticamente

| Erro | `Client` (resources) | `BulkOperationsClient` (`BulkRequirement`) |
|------|----------------------|--------------------------------------------|
| Timeout / conexão (`TimeoutError`) | Sim | Sim |
| HTTP 429 (`RateLimitError`) | Sim | Não |
| HTTP 5xx (`ServerError`) | Sim | Não |
| 401, 403, 404, 422 | Não | Não |

Total de tentativas HTTP = **1 + `max_retries`** (a primeira falha conta como tentativa 1).

---

## Observar retries em produção

```ruby
Clicksign.on_retry do |event|
  Rails.logger.warn(
    "[Clicksign] retry #{event[:attempt]}/#{event[:max_retries]} " \
    "#{event[:method]} #{event[:path]} wait=#{event[:wait_ms]}ms " \
    "error=#{event[:error].class}"
  )
end

Clicksign.on_error do |event|
  Sentry.capture_exception(event[:error]) if defined?(Sentry)
end
```

O evento `:retry` é publicado **antes** do `sleep`; `wait_ms` reflete o delay com jitter daquela tentativa.

---

## Rate limit além do retry automático

```ruby
Envelope = Clicksign::Resources::Notarial::Envelope

begin
  Envelope.retrieve(envelope_id)
rescue Clicksign::RateLimitError => e
  # e.retryable? => true
  # e.rate_limit_remaining, e.rate_limit_reset — quando a API envia os headers
  Rails.logger.warn("Rate limit — reset: #{e.rate_limit_reset}")
  raise # ou reenfileirar job Sidekiq com delay
end
```

---

## Quando não aumentar `max_retries`

- **422 / 400** — corrigir payload (envelope em `draft` para requirements, campos obrigatórios, etc.).
- **401 / 403** — token ou ambiente (`:sandbox` vs `:production`) incorreto.
- **POST sem idempotência** na sua aplicação — retries podem duplicar efeitos colaterais se a API não for idempotente para aquele endpoint.

---

## Referência

- README: [Timeouts, retry e instrumentação](../../README.md#timeouts-retry-e-instrumentação)
- Implementação: `lib/clicksign/retry_backoff.rb`, `lib/clicksign/client.rb`
