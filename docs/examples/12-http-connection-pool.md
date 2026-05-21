# HTTP — connection pool com httpx

O transporte padrão (`UrllibHTTPClient`) abre e fecha a conexão a cada request. Para **muitas chamadas por processo**, use `HttpxHTTPClient` com **uma instância compartilhada** por worker.

```bash
pip install clicksign-python-sdk[httpx]
```

## Singleton por processo (recomendado)

```python
from __future__ import annotations

import os
from functools import lru_cache

from clicksign import ClicksignClient, HttpxHTTPClient

@lru_cache(maxsize=1)
def clicksign_client() -> ClicksignClient:
    """One pooled HTTP client per worker process."""
    return ClicksignClient(
        api_key=os.environ["CLICKSIGN_API_KEY"],
        environment=os.environ.get("CLICKSIGN_ENV", "production"),
        http_client=HttpxHTTPClient(),
    )


def list_draft_envelopes():
    return clicksign_client().envelopes.filter(status="draft").to_list()
```

**Gunicorn / uvicorn workers:** cada processo forkado tem seu próprio `@lru_cache` — correto (pool não é compartilhado entre processos).

**Não** crie `HttpxHTTPClient()` dentro de cada request handler — isso anula o pool.

## `configure()` global

```python
import clicksign
from clicksign import HttpxHTTPClient

_http = HttpxHTTPClient()

clicksign.configure(
    api_key="...",
    environment="production",
    http_client=_http,
)

# Resource class methods use the pooled transport
from clicksign import Envelope

Envelope.list()
```

## Async (FastAPI)

`AsyncClicksignClient` já usa `httpx.AsyncClient` com pool — um client async por app:

```python
from clicksign import AsyncClicksignClient

# app.state.clicksign = AsyncClicksignClient(...) no startup
# await app.state.clicksign.aclose() no shutdown
```

## Shutdown

`HttpxHTTPClient` fecha o pool no `__del__` / GC. Em apps de longa vida, opcionalmente guarde a referência e chame `http._client.close()` no teardown do worker se você acessar o client httpx interno — na maioria dos deploys, deixar o processo encerrar é suficiente.

## Quando o default stdlib basta

- Scripts pontuais, CI, poucas chamadas por minuto
- Prototipação sem extra `httpx`

## Referência

- Limitações: [`08-production-limitations.md`](08-production-limitations.md)
- README: [HTTP transport and connection pool](../../README.md#http-transport-and-connection-pool)
