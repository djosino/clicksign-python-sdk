# Limitações de produção

Comportamentos **esperados** do design atual (stdlib-only, sem deps de runtime). Não são bugs — planeje a arquitetura da app em cima deles.

---

## 1. Sem connection pool

Cada chamada HTTP usa `Net::HTTP.start` e encerra a conexão ao fim do bloco. Não há pool persistente entre requests.

### Impacto

| Cenário | Efeito |
|---------|--------|
| Scripts / jobs sequenciais | Geralmente aceitável |
| Puma com muitas threads e muitas chamadas Clicksign por request | Overhead de TCP/TLS repetido; latência e uso de file descriptors sobem |
| Burst de dezenas de requests paralelos | Pode virar gargalo visível antes da API limitar |

### Mitigações na aplicação

- Reduzir chamadas (batch `BulkRequirement`, menos round-trips).
- Cache leituras idempotentes no seu lado.
- Enfileirar trabalho pesado (Sidekiq) em vez de N chamadas síncronas no request cycle.
- Se precisar de pool persistente, use `Clicksign::Client` via adapter próprio (fora do escopo da gem hoje) — a gem não expõe hook de transporte customizado.

### Por que a gem é assim

Dependência de runtime **apenas stdlib** (`net/http`, `json`, `uri`) — troca simplicidade e zero deps por throughput máximo em alta concorrência.

---

## 2. `Thread.current` e runtimes com Fibers

`Clicksign::Services#use` guarda o client em `Thread.current[:clicksign_client]`. Resources resolvem o client assim:

```ruby
Thread.current[:clicksign_client] || Clicksign.client
```

### Onde funciona bem

- **Rails + Puma** (uma thread por request) com `tenant.clicksign_service.use` no controller/middleware.
- **Sidekiq** (uma thread por job).
- Scripts e consoles.

### Onde **não** funciona

- **Falcon**, **async-ruby**, ou código que cria **Fibers** filhos que chamam `Resources::*` **fora** do mesmo fluxo de `use` — o Fiber pode não ver o `Thread.current` definido no bloco pai.
- Corrotinas que alternam entre tenants sem `use` por contexto de execução.

### Mitigações

| Abordagem | Quando |
|-----------|--------|
| `Clicksign.configure` global por processo | Single-tenant ou um token por worker |
| `Clicksign::Client.new` explícito por task/fiber | Controle total; não passa por `Thread.current` |
| `Services#use` no **mesmo** Fiber/thread que faz as chamadas | Se o runtime propagar `Thread.current` (nem sempre) |
| Evitar `Services` em stack async-fiber | Preferir client explícito |

Exemplo com client explícito (não usa `Services`):

```ruby
client = Clicksign::Client.new(api_key: token, environment: :production)

# Chamadas HTTP diretas ou envolver Resources manualmente não é suportado —
# para fibers, single-tenant global configure costuma ser o caminho mais simples.
```

Para multi-tenant em runtime fiberizado: associe um `Client` (ou token) ao contexto da sua app (objeto Fiber-local customizado) e avalie contribuição futura de API `Fiber.storage` — **não disponível na gem hoje**.

---

## Checklist rápido

- [ ] Alta carga HTTP → medir latência; considerar fila de jobs
- [ ] Multi-tenant → `Services#use` por request/job em Puma/Sidekiq
- [ ] Falcon/async → não depender de `Services#use` sem validar; usar `configure` ou `Client.new`
- [ ] Observabilidade → `on_request` / `on_retry` para detectar volume e lentidão

---

## Referência

- README: [Limitações e produção](../../README.md#limitações-e-produção)
- Multi-conta: [04-multi-client.md](04-multi-client.md)
- Arquitetura: [ARCHITECTURE.md](../ARCHITECTURE.md)
