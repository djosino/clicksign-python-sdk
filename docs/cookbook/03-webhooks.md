# Webhooks

Dois papéis na gem:

1. **`Clicksign::Resources::Webhook`** — cadastro e gestão de webhooks na API Clicksign.
2. **`Clicksign::Webhook`** (módulo) — validação HMAC do payload no **seu** servidor ao receber callbacks.

---

## 1. Cadastrar webhook na Clicksign

```ruby
require 'clicksign'

Clicksign.configure do |c|
  c.api_key     = ENV.fetch('CLICKSIGN_API_KEY')
  c.environment = :production
end

Webhook = Clicksign::Resources::Webhook

hook = Webhook.create(
  endpoint: 'https://minhaapp.com/webhooks/clicksign',
  events: %w[sign close cancel add_signer],
  status: 'active'
)

# Guarde o secret com segurança — necessário para validar callbacks
# Rails.application.credentials.clicksign_webhook_secrets[hook.id] = hook.secret
```

Listar, filtrar e desativar:

```ruby
Webhook.filter(status: 'active').each { |w| puts "#{w.id} → #{w.endpoint}" }

hook = Webhook.retrieve(hook.id)
hook.update(status: 'inactive')
hook.delete
```

Atributos típicos: `endpoint`, `events`, `status`, `secret` (retornado na criação).

---

## 2. Validar assinatura no controller (Rails)

Use o **corpo bruto** da requisição (bytes exatos enviados pela Clicksign). O header esperado é `Content-HMAC` com valor no formato `sha256=<hex>` (o mesmo formato de `Clicksign::Webhook.compute_signature`).

```ruby
class ClicksignWebhooksController < ApplicationController
  skip_before_action :verify_authenticity_token

  def create
    payload   = request.raw_post
    signature = request.headers['Content-HMAC']
    secret    = ENV.fetch('CLICKSIGN_WEBHOOK_SECRET')

    Clicksign::Webhook.verify_signature!(payload, signature, secret: secret)

    event = JSON.parse(payload)
    WebhookProcessorJob.perform_later(event)

    head :ok
  rescue Clicksign::WebhookSignatureError
    head :unauthorized
  end
end
```

Equivalente em Python (validação + parse em um passo):

```python
import os

from clicksign import WebhookPayloadError, WebhookSignatureError, construct_event

def handle_webhook(request):
    payload = request.body  # bytes brutos, sem reformatar JSON
    signature = request.headers.get("Content-HMAC", "")
    secret = os.environ["CLICKSIGN_WEBHOOK_SECRET"]

    try:
        event = construct_event(payload, signature, secret, tolerance=300)
    except (WebhookSignatureError, WebhookPayloadError):
        return Response(status=401)

    process_event.delay(event.payload)
    return Response(status=200)
```

Variante em duas etapas (validação manual):

```ruby
unless Clicksign::Webhook.verify_signature(payload, signature, secret: secret)
  return head :unauthorized
end
```

---

## 3. Testar no console

```ruby
secret  = 'my-webhook-secret'
payload = '{"event":"sign","data":{}}'
sig     = Clicksign::Webhook.compute_signature(payload, secret: secret)

Clicksign::Webhook.verify_signature!(payload, sig, secret: secret)  # => true
Clicksign::Webhook.verify_signature(payload, 'sha256=invalid', secret: secret) # => false
```

---

## Checklist de produção

- [ ] `endpoint` em HTTPS público
- [ ] `secret` em cofre (variável de ambiente, credentials) — nunca no repositório
- [ ] Responder **200** rapidamente; processamento pesado em job assíncrono
- [ ] **Idempotência** — a Clicksign pode reenviar o mesmo evento
- [ ] Validar HMAC **antes** de confiar no JSON parseado
- [ ] Logar falhas de verificação sem vazar o secret

---

## Eventos

Os valores de `events` no cadastro dependem do que a API Clicksign expõe para sua conta (ex.: `sign`, `close`, `cancel`, `add_signer`). Consulte a [documentação oficial](https://developers.clicksign.com/).

---

## Referência

- README: [Outros recursos — Webhook](../../README.md#outros-recursos)
- Implementação: `lib/clicksign/webhook.rb`, `lib/clicksign/resources/webhook.rb`
