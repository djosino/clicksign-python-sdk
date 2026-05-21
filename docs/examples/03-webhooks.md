# Webhooks

Dois papéis no SDK:

1. **`clicksign.resources.webhook.Webhook`** — cadastro e gestão de webhooks na API Clicksign.
2. **`clicksign.webhook`** — validação HMAC do payload no **seu** servidor ao receber callbacks.

---

## 1. Cadastrar webhook na Clicksign

```python
import os

from clicksign import ClicksignClient

client = ClicksignClient(
    api_key=os.environ["CLICKSIGN_API_KEY"],
    environment="production",
)

hook = client.webhooks.create(
    endpoint="https://minhaapp.com/webhooks/clicksign",
    events=["sign", "close", "cancel", "add_signer"],
    status="active",
)

# Guarde o secret com segurança — necessário para validar callbacks
# settings.CLICKSIGN_WEBHOOK_SECRETS[hook.id] = hook.secret
```

Listar, filtrar e desativar:

```python
for w in client.webhooks.filter(status="active"):
    print(f"{w.id} → {w.endpoint}")

hook = client.webhooks.retrieve(hook.id)
hook.update(status="inactive")
hook.delete()
```

Atributos típicos: `endpoint`, `events`, `status`, `secret` (retornado na criação).

Import direto (sem facade):

```python
from clicksign.resources.webhook import Webhook

hook = Webhook.create(endpoint="https://...", events=["sign"], status="active")
```

---

## 2. Validar assinatura no handler HTTP

Use o **corpo bruto** da requisição (bytes exatos enviados pela Clicksign). O header esperado é `Content-HMAC` com valor no formato `sha256=<hex>`.

### Flask

```python
import os

from flask import Response, request

from clicksign import WebhookPayloadError, WebhookSignatureError, construct_event


@app.post("/webhooks/clicksign")
def clicksign_webhook():
    payload = request.get_data()
    signature = request.headers.get("Content-HMAC", "")
    secret = os.environ["CLICKSIGN_WEBHOOK_SECRET"]

    try:
        event = construct_event(payload, signature, secret, tolerance=300)
    except (WebhookSignatureError, WebhookPayloadError):
        return Response(status=401)

    process_event.delay(event.payload)
    return Response(status=200)
```

### Django

```python
import os

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from clicksign import construct_event, WebhookPayloadError, WebhookSignatureError


@csrf_exempt
def clicksign_webhook(request):
    payload = request.body
    signature = request.headers.get("Content-HMAC", "")
    secret = os.environ["CLICKSIGN_WEBHOOK_SECRET"]

    try:
        event = construct_event(payload, signature, secret, tolerance=300)
    except (WebhookSignatureError, WebhookPayloadError):
        return HttpResponse(status=401)

    process_event.delay(event.payload)
    return HttpResponse(status=200)
```

Variante em duas etapas (validação manual):

```python
from clicksign import compute_signature, verify_signature

expected = compute_signature(payload, secret)
if not verify_signature(payload, signature, secret):
    return Response(status=401)
```

Ou com exceção explícita:

```python
from clicksign.webhook import verify_signature_or_raise

verify_signature_or_raise(payload, signature, secret)
```

---

## 3. Testar no REPL

```python
from clicksign import compute_signature, verify_signature

secret = "my-webhook-secret"
payload = b'{"event":"sign","data":{}}'
sig = compute_signature(payload, secret)

assert verify_signature(payload, sig, secret)
assert not verify_signature(payload, "sha256=invalid", secret)
```

---

## Checklist de produção

- [ ] `endpoint` em HTTPS público
- [ ] `secret` em cofre (variável de ambiente, secrets manager) — nunca no repositório
- [ ] Responder **200** rapidamente; processamento pesado em fila assíncrona
- [ ] **Idempotência** — a Clicksign pode reenviar o mesmo evento
- [ ] Validar HMAC **antes** de confiar no JSON parseado
- [ ] Logar falhas de verificação sem vazar o secret

---

## Eventos

Os valores de `events` no cadastro dependem do que a API Clicksign expõe para sua conta (ex.: `sign`, `close`, `cancel`, `add_signer`). Consulte a [documentação oficial](https://developers.clicksign.com/).

---

## Referência

- README: [Webhooks](../../README.md)
- Implementação: `src/clicksign/webhook.py`, `src/clicksign/resources/webhook.py`
