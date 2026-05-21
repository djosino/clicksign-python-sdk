# Vários clientes (multi-conta / multi-tenant)

Quando cada conta, workspace ou job usa **token e ambiente diferentes**, evite depender só de `Clicksign.configure` global. Use `Clicksign::Services` para isolar o HTTP por contexto, ou `Clicksign::Client.new` para chamadas diretas.

---

## Dois clientes na mesma aplicação

```ruby
require 'clicksign'

# Config global opcional — fallback fora de #use (ex.: rake interno, console)
Clicksign.configure do |c|
  c.api_key     = ENV['CLICKSIGN_API_KEY_DEFAULT']
  c.environment = :sandbox
end

conta_producao = Clicksign::Services.new(
  api_key: ENV['CLICKSIGN_TOKEN_EMPRESA_A'],
  environment: :production,
  max_retries: 3,
  read_timeout: 30
)

conta_homolog = Clicksign::Services.new(
  api_key: ENV['CLICKSIGN_TOKEN_EMPRESA_B'],
  environment: :sandbox,
  max_retries: 1
)

Envelope = Clicksign::Resources::Notarial::Envelope

conta_producao.use do
  Envelope.create(name: 'Contrato — Empresa A')
end

conta_homolog.use do
  Envelope.filter(status: 'draft').to_a
end
```

Dentro de cada `use`, **todos** os `Clicksign::Resources::*` usam o token daquele service (`Authorization` do client isolado).

---

## Rails: um service por tenant

```ruby
# app/models/tenant.rb
class Tenant < ApplicationRecord
  def clicksign_service
    @clicksign_service ||= Clicksign::Services.new(
      api_key: clicksign_api_key,
      environment: clicksign_environment.to_sym, # :sandbox ou :production
      max_retries: 2
    )
  end
end

# app/controllers/envelopes_controller.rb
class EnvelopesController < ApplicationController
  def create
    current_tenant.clicksign_service.use do
      envelope = Clicksign::Resources::Notarial::Envelope.create(
        name: params[:name],
        locale: 'pt-BR'
      )
      render json: { id: envelope.id }
    end
  end
end
```

Guarde `clicksign_api_key` criptografado (credentials, attr_encrypted, etc.) — nunca em texto claro no banco sem proteção.

---

## Sidekiq: token por job

```ruby
class SyncEnvelopesJob < ApplicationJob
  def perform(tenant_id)
    tenant = Tenant.find(tenant_id)

    tenant.clicksign_service.use do
      Clicksign::Resources::Notarial::Envelope
        .filter(status: 'running')
        .each { |e| sync_envelope(e) }
    end
  end
end
```

Cada job define o client no `Thread.current` do worker; jobs paralelos de tenants diferentes não misturam tokens.

> **Falcon / async-ruby / Fibers:** `Thread.current` do `use` pode não propagar para Fibers filhos. Ver [08-production-limitations.md](08-production-limitations.md).

---

## Blocos aninhados

`use` restaura o client anterior ao sair — útil para impersonação ou suporte operando em conta do cliente:

```ruby
suporte = Clicksign::Services.new(api_key: ENV['SUPORTE_TOKEN'], environment: :production)
cliente = Clicksign::Services.new(api_key: cliente_token, environment: :production)

suporte.use do
  # chamadas com token de suporte
  cliente.use do
    # chamadas com token do cliente
  end
  # volta ao token de suporte
end
# Thread.current[:clicksign_client] => nil
```

Se o bloco interno **levantar exceção**, o client externo ainda é restaurado no `ensure`.

---

## `Client` HTTP direto (sem resources)

Quando não passa por `Resources::*`, instancie o client explicitamente — **não** usa `Thread.current`:

```ruby
client_a = Clicksign::Client.new(
  api_key: ENV['TOKEN_A'],
  base_url: Clicksign::Configuration::ENVIRONMENTS[:production],
  max_retries: 2
)

# Client não aceita environment: — use base_url (ou prefira Services)
client_b = Clicksign::Client.new(
  api_key: ENV['TOKEN_B'],
  base_url: Clicksign::Configuration::ENVIRONMENTS[:sandbox]
)

client_a.get('/envelopes', params: { 'filter[status]' => 'draft' })
```

| API | Isolamento |
|-----|------------|
| `Services#use` + Resources | Automático via thread-local |
| `Client.new` | Você guarda a instância (hash por tenant, etc.) |

---

## Bulk requirements e config global

`BulkRequirement.create` chama `Clicksign.bulk_operations_client`, montado na **config global**. Em multi-tenant:

- defina `max_retries` / timeouts no `Clicksign.configure` do processo, **ou**
- execute bulk apenas dentro de jobs já isolados por tenant, com política global aceitável para todos.

Resources normais (envelope, document, signer) respeitam o `use` do tenant; bulk é a exceção que usa o client global memoizado.

---

## Escolha rápida

| Cenário | Abordagem |
|---------|-----------|
| Um token por app | `Clicksign.configure` |
| SaaS, N tokens, Rails/Sidekiq | `Services#use` por request/job |
| Script com 2 contas no mesmo processo | Dois `Services.new` + `use` |
| HTTP custom / proxy | `Client.new` por instância |

---

## Referência

- README: [Multi-conta e cliente instanciável](../../README.md#multi-conta-e-cliente-instantiável)
- Implementação: `lib/clicksign/services.rb`, `lib/clicksign/resource.rb` (`Resource.client`)
- Retries por tenant: [01-retries.md](01-retries.md)
