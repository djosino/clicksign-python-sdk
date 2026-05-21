# Limitações de produção (Python SDK)

Comportamentos **esperados** do design atual. Não são bugs — planeje a arquitetura em cima deles.

---

## 1. Connection pool (transporte HTTP)

### Default: sem pool

`UrllibHTTPClient` (padrão, zero deps) usa `http.client` e **fecha a conexão** ao fim de cada request. Não há reutilização de TCP/TLS entre chamadas.

### Impacto qualitativo

| Cenário | Efeito |
|---------|--------|
| Scripts / jobs sequenciais | Geralmente aceitável |
| API web com várias chamadas Clicksign por request | Overhead de handshake repetido; latência e file descriptors sobem |
| Burst paralelo (threads ou `asyncio.gather`) | Gargalo de conexão pode aparecer antes do rate limit da API |

Ordem de grandeza típica em bursts (mesmo host, TLS já “quente” no OS): **httpx com pool** costuma reduzir latência média por request frente ao stdlib quando há dezenas de chamadas seguidas no mesmo processo — meça no seu ambiente; não há benchmark oficial no repositório.

### Mitigação recomendada: `HttpxHTTPClient`

```bash
pip install clicksign[httpx]
```

```python
from clicksign import ClicksignClient, HttpxHTTPClient

http = HttpxHTTPClient()  # uma instância por processo/worker
client = ClicksignClient(api_key="...", environment="production", http_client=http)
```

Receita completa (singleton): [`12-http-connection-pool.md`](12-http-connection-pool.md).

Outras mitigações:

- Menos round-trips (`bulk_requirements`, includes, menos `retrieve` em loop).
- Cache de leituras idempotentes no seu lado.
- Fila de jobs (Celery, RQ) em vez de N chamadas síncronas no request cycle.

### Custom transport

Qualquer objeto que implemente `HTTPClient` pode ser injetado em `configure(http_client=...)` ou `ClicksignClient(http_client=...)`.

---

## 2. `Services.use()` e asyncio

`Services.use()` grava o client em `threading.local`. Resources resolvem o client assim:

```python
Thread.current_thread().__dict__["_clicksign_client"]  # simplificado
```

### Onde funciona bem

- **Django / Flask / FastAPI (sync views)** com um thread por request e `with tenant.use():`
- **Celery** (um thread por task)
- Scripts e consoles

### Onde não funciona bem

- **asyncio** com `Services.use()` — o contexto thread-local não segue corrotinas
- Código que chama `Envelope.list()` sem `use()` no mesmo thread

### Mitigações

| Abordagem | Quando |
|-----------|--------|
| `clicksign.configure()` global | Single-tenant por processo |
| `ClicksignClient` / `AsyncClicksignClient` explícito | Multi-tenant, FastAPI, controle total |
| `Services.use()` no mesmo thread que chama a SDK | Apps WSGI sync |

Async: [`README` — Async](../../README.md#async-fastapi-asyncio) · multi-conta: [`04-multi-client.md`](04-multi-client.md).

---

## 3. Bulk vs retry

`BulkOperationsClient` só retenta **timeout de rede**, não 429/5xx (POST atômico sem idempotência). Ver [`01-retries.md`](01-retries.md).

---

## Checklist rápido

- [ ] Alta carga HTTP → `pip install clicksign[httpx]` + `HttpxHTTPClient` compartilhado por worker
- [ ] Multi-tenant sync → `Services.use()` por request/job
- [ ] FastAPI/async → `AsyncClicksignClient`, não `Services.use()`
- [ ] Observabilidade → `on_request` / `CLICKSIGN_LOG` para volume e lentidão

---

## Referência

- README: [HTTP transport and connection pool](../../README.md#http-transport-and-connection-pool)
- Arquitetura: [`ARCHITECTURE.md`](../ARCHITECTURE.md)
