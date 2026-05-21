# Cookbook — Clicksign Ruby SDK

Receitas curtas e copiáveis por cenário de integração. Cada página assume `require 'clicksign'` e configuração básica (ver [README](../../README.md#configuração)).

| Receita | Quando usar |
|---------|-------------|
| [Retries e timeouts](01-retries.md) | Produção, jobs, rate limit, falhas transitórias |
| [Bulk requirements](02-bulk-requirements.md) | Montar agree + evidência + rubrica em uma chamada |
| [Webhooks](03-webhooks.md) | Cadastrar endpoint na API, validar HMAC, processar eventos |
| [Vários clientes](04-multi-client.md) | Multi-tenant, Sidekiq, blocos aninhados, `Client` direto |
| [List vs filter](07-list-and-filter.md) | Quando usar `list` (Array) vs `filter` (QueryProxy) |
| [Limitações de produção](08-production-limitations.md) | Sem connection pool; `Thread.current` vs Fibers |

**Fluxo completo de assinatura:** [`WORKFLOW.md`](../WORKFLOW.md) — envelope → documento → signatário → requisitos → ativação → notificação.

**Mapa de resources e rotas:** [`SPEC.md`](../SPEC.md).

**Problemas comuns:** [`TROUBLESHOOTING.md`](../TROUBLESHOOTING.md) · **Arquitetura:** [`ARCHITECTURE.md`](../ARCHITECTURE.md) · **Logs/APM:** [`OBSERVABILITY.md`](../OBSERVABILITY.md).
