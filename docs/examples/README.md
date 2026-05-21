# Examples — Clicksign SDK

Receitas curtas por cenário. Exemplos Python salvo indicação; páginas legadas Ruby usam `require 'clicksign'`.

| Receita | Quando usar |
|---------|-------------|
| [Retries e timeouts](01-retries.md) | Produção, jobs, rate limit, falhas transitórias |
| [Bulk requirements](02-bulk-requirements.md) | Montar agree + evidência + rubrica em uma chamada |
| [Webhooks](03-webhooks.md) | Cadastrar endpoint na API, validar HMAC, processar eventos |
| [Vários clientes](04-multi-client.md) | Multi-tenant, Sidekiq, blocos aninhados, `Client` direto |
| [List vs filter](07-list-and-filter.md) | Quando usar `list` vs `filter` (QueryProxy) |
| [Limitações de produção](08-production-limitations.md) | Sem connection pool; `Thread.current` vs Fibers |
| [Observabilidade — structlog](09-observability-structlog.md) | Logs JSON com hooks `on_*` |
| [Observabilidade — OpenTelemetry](10-observability-opentelemetry.md) | Spans manuais por request/erro |
| [Observabilidade — métricas](11-observability-metrics.md) | Prometheus / StatsD via hooks |
| [HTTP — connection pool](12-http-connection-pool.md) | `HttpxHTTPClient` singleton por worker |

**Fluxo completo de assinatura:** [`WORKFLOW.md`](../WORKFLOW.md).

**Mapa de resources:** [`SPEC.md`](../SPEC.md) · **Paginação:** [`PAGINATION.md`](../PAGINATION.md).

**Problemas comuns:** [`TROUBLESHOOTING.md`](../TROUBLESHOOTING.md) · **Logs/APM:** [`OBSERVABILITY.md`](../OBSERVABILITY.md).
