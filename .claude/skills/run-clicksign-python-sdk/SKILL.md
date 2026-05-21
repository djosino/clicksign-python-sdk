---
name: run-clicksign-python-sdk
description: Run, smoke-test, and drive the clicksign-python-sdk library. Use when asked to run, start, smoke-test, verify, or screenshot the SDK. Covers: configure(), ClicksignClient, Envelope CRUD, error hierarchy, instrumentation, webhook, RequestOptions.
---

SDK Python puro (sem servidor, sem GUI). Driver é `smoke.py` — importa o pacote diretamente via `FakeHTTPClient`, sem rede real.

## Pré-requisitos

Python 3.10+ disponível como `python3`. Sem dependências extras além das do próprio repo.

```bash
# Verificar
python3 --version   # Python 3.10+
```

## Run (caminho do agente)

Execute sempre a partir da raiz do repo:

```bash
python3 .claude/skills/run-clicksign-python-sdk/smoke.py
```

Sem `PYTHONPATH` — o script injeta `src/` e `tests/` no `sys.path` automaticamente.

Saída esperada:

```
=== clicksign-python-sdk smoke ===

  OK  versão importada corretamente
  OK  configure() define estado global
  ...
  OK  verify_signature valida HMAC SHA-256 corretamente

========================================
Resultado: 15 OK, 0 FAIL
```

Exit code 0 = tudo verde. Exit code 1 = algum caso falhou (traceback impresso).

## O que o smoke cobre

| Caso | O que valida |
|------|--------------|
| Versão | `clicksign.__version__` não vazio |
| `configure()` | estado global definido corretamente |
| `ClicksignClient` | instância explícita sem erro |
| `Envelope.list()` | emite `GET /envelopes` |
| `Envelope.create()` | retorna `Envelope` com `id` e `status` |
| `Envelope.retrieve()` | retorna instância com id correto |
| `NotFoundError` | levantado em 404 |
| `AuthenticationError` | levantado em 401 |
| `ServerError` | levantado em 500 (com `max_retries=0`) |
| `RateLimitError` | levantado em 429; `rate_limit_remaining` é string do header |
| Instrumentação | `on_request` callback recebe `method` e `duration_ms` |
| `RequestOptions` | `api_key` por chamada sobrescreve header `Authorization` |
| `ClicksignClient` namespace | `client.notarial.envelopes.list()` |
| `api_errors` | `e.api_errors[0].detail` acessível em erro 422 |
| Webhook | `verify_signature` valida HMAC-SHA256 |

## Invocar código interno diretamente

Para testar uma função isolada sem passar pelo smoke inteiro:

```bash
PYTHONPATH=src python3 - <<'EOF'
from clicksign import ClicksignClient
from clicksign._http.transport import HTTPResponse

class Stub:
    name = "stub"
    def request(self, method, url, **kw):
        return HTTPResponse(200, '{"data":[],"meta":{},"links":{}}', {})

client = ClicksignClient(api_key="test", environment="sandbox", http_client=Stub())
result = client.notarial.envelopes.list()
print("OK:", result)
EOF
```

## Gotchas

- **`src/` deve vir antes de `tests/` no `sys.path`** — `tests/clicksign/` é um pacote que shadowa `src/clicksign/` se `tests/` vier primeiro.
- **`ServerError` e `RateLimitError` são `retryable=True`** — com `max_retries=3` (padrão), o `FakeHTTPClient` esgota a fila após a 1ª resposta. Use `configure(..., max_retries=0)` em testes de erro retryable.
- **`rate_limit_remaining` é `str`**, não `int` — vem direto do header HTTP sem conversão.
- **`e.errors` é `list[dict]`** — para acessar `ApiError.detail`, use `e.api_errors[0].detail` (propriedade que converte).
- **`clicksign.instrumentation.clear()`** — único jeito de limpar callbacks entre testes; `clicksign._config` não tem atributo `_instrumentation`.

## Troubleshooting

| Sintoma | Causa | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'clicksign._http'` | `tests/` inserido antes de `src/` | `sys.path.insert(0, "src")` deve ser o último insert (fica em [0]) |
| `FakeHTTPClient: no more responses queued` | erro retryable com múltiplas tentativas | Adicionar `max_retries=0` no `configure()` desse teste |
| `AttributeError: 'dict' object has no attribute 'detail'` | usando `e.errors[0]` em vez de `e.api_errors[0]` | Trocar para `e.api_errors[0].detail` |
