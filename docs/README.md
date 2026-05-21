# Documentação — Clicksign Python SDK

Índice por tema. A implementação costuma estar **à frente** dos checklists legados — use este mapa em vez de um único arquivo monolítico.

---

## Começar aqui

| Documento | Para quê |
|-----------|----------|
| [`SDK_CONTRACT.md`](SDK_CONTRACT.md) | Contrato de comportamento (timeouts, retry, JSON:API, erros) |
| [`WORKFLOW.md`](WORKFLOW.md) | Fluxo envelope → documento → signatário → ativação |
| [`SPEC.md`](SPEC.md) | Rotas da API e mapa de resources |
| [`../README.md`](../README.md) | Instalação, exemplos rápidos, padrões de uso |

---

## SDK (infraestrutura e gaps)

| Documento | Para quê |
|-----------|----------|
| [`SDK_ROADMAP.md`](SDK_ROADMAP.md) | Checklist histórico de features do SDK + decisões de design |
| [`SDK_CLIENT_GAPS.md`](SDK_CLIENT_GAPS.md) | Gaps **somente no cliente** (sem mudança na API) — status por § |
| [`SDK_TEST_MATRIX.md`](SDK_TEST_MATRIX.md) | Cobertura de testes comportamentais (`tests/clicksign/`) |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Diagramas: request típico, bulk, webhooks |

---

## Uso diário

| Documento | Para quê |
|-----------|----------|
| [`TYPES.md`](TYPES.md) | TypedDict, properties, `generate_resource_types.py` |
| [`PAGINATION.md`](PAGINATION.md) | `QueryProxy`, `links.next`, `per()`, `on_page` |
| [`OBSERVABILITY.md`](OBSERVABILITY.md) | `CLICKSIGN_LOG`, hooks, correlation id, PII |

---

## Examples (receitas Python)

| Receita | Tema |
|---------|------|
| [`examples/01-retries.md`](examples/01-retries.md) | Timeouts, `max_retries`, bulk vs client |
| [`examples/02-bulk-requirements.md`](examples/02-bulk-requirements.md) | Operações atômicas |
| [`examples/03-webhooks.md`](examples/03-webhooks.md) | HMAC, `construct_event` |
| [`examples/04-multi-client.md`](examples/04-multi-client.md) | Multi-tenant, `Services`, `ClicksignClient` |
| [`examples/07-list-and-filter.md`](examples/07-list-and-filter.md) | `list` vs `filter` |
| [`examples/08-production-limitations.md`](examples/08-production-limitations.md) | Sem pool no default, asyncio |
| [`examples/09-observability-structlog.md`](examples/09-observability-structlog.md) | structlog |
| [`examples/10-observability-opentelemetry.md`](examples/10-observability-opentelemetry.md) | OpenTelemetry manual |
| [`examples/11-observability-metrics.md`](examples/11-observability-metrics.md) | Prometheus / StatsD |
| [`examples/12-http-connection-pool.md`](examples/12-http-connection-pool.md) | `HttpxHTTPClient` singleton |

Índice do examples: [`examples/README.md`](examples/README.md).

---

## Manutenção da doc

1. Comportamento novo → atualizar `SDK_CONTRACT.md` + teste em `tests/clicksign/` + linha em `SDK_TEST_MATRIX.md`.
2. Gap só no cliente → `SDK_CLIENT_GAPS.md`; depende da API → `SDK_ROADMAP.md` §15–18.
3. Receita copiável → novo arquivo em `examples/` e linha neste README + `examples/README.md`.

**Última revisão geral:** maio/2026 (§9 SDK_CLIENT_GAPS).
