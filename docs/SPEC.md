# Especificação Técnica — Clicksign Ruby SDK

**Versão do documento:** 2.0
**Data:** 2026-05-20
**Fonte:** Clicksign API v3 (JSON:API)
**Método:** leitura de rotas, resources e schema validators da API

---

## 1. VISÃO GERAL DO SISTEMA

### Objetivo do Negócio

O **Clicksign Ruby SDK** é uma gem Ruby que expõe a API REST da Clicksign de forma idiomática em Ruby. É um **cliente HTTP/SDK** que permite que aplicações Ruby integrem assinatura digital de documentos, gestão de envelopes, signatários, webhooks e demais funcionalidades da plataforma Clicksign sem implementar manualmente serialização JSON:API, autenticação, paginação e mapeamento de respostas.

**Problema que resolve:**

- Abstrair a comunicação HTTPS com a API JSON:API da Clicksign (`sandbox.clicksign.com/api/v3`, `app.clicksign.com/api/v3`).
- Materializar respostas JSON:API em objetos Ruby tipados.
- Oferecer API fluente e idiomática (`Envelope.filter`, `.list`, `.create`, `.retrieve`, `#update`, `#delete`).
- Tratar erros, validações e mapeamento de status HTTP de forma padronizada.

### Principais Usuários/Personas

| Persona | Uso típico |
|--------|------------|
| **Desenvolvedor backend Ruby** | CRUD de recursos Clicksign (envelopes, signatários, documentos) em apps Rails/Sinatra/etc. |
| **Integrador de assinatura** | Criação de envelopes, adição de documentos e signatários, ativação e monitoramento do fluxo. |
| **Operador de webhooks** | Recebimento e processamento de eventos via webhooks configurados na plataforma. |
| **Administrador de conta** | Gestão de usuários, grupos, memberships e templates. |

---

## 2. ARQUITETURA E INTEGRAÇÕES

### Componentes do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│  Aplicação Ruby do consumidor (Rails, scripts, jobs, etc.)  │
└───────────────────────────┬─────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │  Clicksign::Resources::*  │
              │  (Envelope, Document, ...) │
              └─────────────┬─────────────┘
                            │
              ┌─────────────┴─────────────┐
              │    Clicksign::Resource    │
              │  (base: Net::HTTP, CRUD)  │
              └─────────────┬─────────────┘
                            │
              ┌─────────────┴─────────────┐
              │   Clicksign::Parser /     │
              │   Error handling          │
              └─────────────┬─────────────┘
                            │
              ┌─────────────┴─────────────┐
              │       HTTP / HTTPS        │
              │  sandbox.clicksign.com    │
              │  app.clicksign.com        │
              └───────────────────────────┘
```

| Camada | Responsabilidade | Artefatos principais |
|--------|------------------|----------------------|
| **Ponto de entrada** | `require 'clicksign'`, config global | `lib/clicksign.rb` |
| **Configuração** | `api_key`, `base_url` | `lib/clicksign/configuration.rb` |
| **Resources** | Um resource por entidade da API | `lib/clicksign/resources/**` |
| **Base resource** | Métodos CRUD, QueryProxy, auto-paginação, `method_missing` para atributos | `lib/clicksign/resource.rb` |
| **Parser** | Deserialização JSON:API, filtra `included` sem `type` | `lib/clicksign/json_api/parser.rb` |
| **Bulk operations** | POST atomic (`atomic:operations` / `atomic:results`) | `lib/clicksign/json_api/bulk_operations_client.rb` |
| **Erros** | Hierarquia de exceções mapeadas de HTTP | `lib/clicksign/errors.rb` |

### Autenticação

A API usa o header `Authorization: <token>` **sem prefixo Bearer**. Configurado globalmente:

```ruby
Clicksign.configure do |c|
  c.api_key  = 'seu-token'
  c.base_url = 'https://sandbox.clicksign.com/api/v3'
end
```

### Stack principal

| Tecnologia | Papel |
|------------|-------|
| **Ruby** | Linguagem (>= 3.0) |
| **Net::HTTP** | Transporte HTTP (stdlib) |
| **JSON** | Serialização/deserialização (stdlib) |
| **RSpec + WebMock** | Testes com stubs HTTP (sem VCR, sem rede real) |

---

## 3. MAPA DE RECURSOS DA API (v3)

Baseado nas rotas da Clicksign API v3, namespace `:v3`.

### Namespacing no SDK

| Namespace Ruby | Resources | Motivo |
|----------------|-----------|--------|
| `Clicksign::Resources::Notarial` | Envelope, Document, Signer, Requirement, BulkRequirement, SignatureWatcher | Recursos do fluxo de assinatura (envelopes e ciclo de vida) |
| `Clicksign::Resources::AutoSignature` | Term | Namespace de rotas (`namespace :auto_signature`) |
| `Clicksign::Resources::AcceptanceTerm` | Whatsapp | Namespace de rotas (`namespace :acceptance_term`) |
| `Clicksign::Resources` (raiz) | Webhook, User, Membership, Group, Template, TemplateField, Folder, EnvelopeBulkCreation, AccessControlList, Event | Recursos gerais sem namespace específico |

---

### 3.1 Envelopes (`jsonapi_resources :envelopes`)

**Endpoint base:** `/api/v3/envelopes`

| Método | SDK | HTTP |
|--------|-----|------|
| Listar (1ª página) | `Envelope.list` | `GET /envelopes` |
| Listar (com filtros/chain) | `Envelope.filter(...).to_a` | `GET /envelopes?filter[...]` |
| Buscar | `Envelope.retrieve(id)` | `GET /envelopes/:id` |
| Criar | `Envelope.create(**attrs)` | `POST /envelopes` |
| Atualizar | `envelope.update(**attrs)` | `PATCH /envelopes/:id` |
| Deletar | `envelope.delete` | `DELETE /envelopes/:id` |
| Ativar | `Envelope.activate(id)` | `POST /envelopes/:id/activate` |

**Atributos (do resource):**
- `name`, `status`, `deadline_at`, `locale`, `auto_close`, `rubric_enabled`
- `remind_interval`, `block_after_refusal`, `deadline_partial_signature_action`
- `default_subject`, `default_message`, `metadata`, `migrated`, `registro_civil_kind`
- `created` (alias `created_at`), `modified` (alias `updated_at`)

**Filtros:** `status`, `name`, `created`, `modified`, `deadline_at`

**Ordenação:** `name`, `status`, `deadline_at`, `created`, `modified`

**Relacionamentos:** `folder` (has_one), `documents` (has_many), `signers` (has_many), `requirements` (has_many)

**Sub-resources:**
- `GET /envelopes/:id/events` → `Envelope.list_events(id)` (`EventResource`: `name`, `data`, `created`)
- `GET /envelopes/:id/requirements` → `Envelope.list_requirements(id, **filters)`
- `GET/POST/PATCH/DELETE /envelopes/:id/requirements` → `Requirement` (create, retrieve, update, delete)
- `POST /envelopes/:id/notifications` → `Envelope.notify(id, ...)`
- `GET/POST/PATCH/DELETE /envelopes/:id/documents` → `Document`
- `GET/POST/DELETE /envelopes/:id/signers` → `Signer` (exceto update)
- `GET/POST/DELETE /envelopes/:id/signature_watchers` → `SignatureWatcher`

---

### 3.2 Documentos (`jsonapi_resources :documents`)

**Endpoint base (nested):** `/api/v3/envelopes/:envelope_id/documents`

| Método | SDK | HTTP |
|--------|-----|------|
| Listar | `Document.list_for_envelope(envelope_id)` | `GET /envelopes/:id/documents` |
| Buscar | `Document.retrieve(id)` | `GET /envelopes/:envelope_id/documents/:id` |
| Criar | `Document.create(**attrs)` | `POST /envelopes/:envelope_id/documents` |
| Atualizar | `document.update(**attrs)` | `PATCH /envelopes/:envelope_id/documents/:id` |
| Deletar | `document.delete` | `DELETE /envelopes/:envelope_id/documents/:id` |

**Atributos:** `status`, `filename`, `content_base64`, `content_url`, `template`, `metadata`, `migrated`, `created`, `modified`

**Filtros:** `status`, `filename`

**Campos de criação (mutuamente exclusivos):**
- `content_base64` — upload direto
- `content_url` — via URL
- `template` — a partir de template
- `duplicate` — duplicar documento existente

**Sub-resources:**
- `GET/POST /envelopes/:id/documents/:id/events` → eventos do documento (`add_image`, `custom`)

---

### 3.3 Signatários (`jsonapi_resources :signers`)

**Endpoint base (nested):** `/api/v3/envelopes/:envelope_id/signers`

| Método | SDK | HTTP |
|--------|-----|------|
| Listar | `Signer.list_for_envelope(envelope_id)` | `GET /envelopes/:id/signers` |
| Criar | `Signer.create(**attrs)` | `POST /envelopes/:envelope_id/signers` |
| Deletar | `signer.delete` | `DELETE /envelopes/:envelope_id/signers/:id` |

**Atributos:** `name`, `birthday`, `email`, `phone_number`, `location_required_enabled`, `has_documentation`, `documentation`, `refusable`, `group`, `communicate_events`, `signature_host`, `created`, `modified`

**Relacionamentos:** `envelope` (has_one), `requirements` (has_many)

---

### 3.4 Requisições (requirements)

Disponíveis como nested de `Envelope` e como `index_related` em `Document`/`Signer`.

**Atributos:** `action`, `role`, `auth`, `pages`, `rubric_pages`, `kind`, `rubric_field`, `created`, `modified`

**Filtros:** `document.key`, `signer.key`, `requirement.action`

**Relacionamentos:** `envelope` (has_one), `document` (has_one), `signer` (has_one)

**Ações de `action`:** `agree`, `provide_evidence`, `rubricate`

#### 3.4.1 Endpoint padrão (`jsonapi_resources :requirements`)

Uma operação por requisição. Envelope em **draft** para create/delete.

| Método | SDK | HTTP |
|--------|-----|------|
| Listar (envelope) | `Envelope.list_requirements(envelope_id, **filters)` | `GET /envelopes/:id/requirements` |
| Listar (documento) | `Requirement.list_for_document(document_id, **filters)` | `GET /documents/:id/relationships/requirements` |
| Listar (signatário) | `Requirement.list_for_signer(signer_id, **filters)` | `GET /signers/:id/relationships/requirements` |
| Buscar | `Requirement.retrieve(id, envelope_id:)` | `GET /envelopes/:envelope_id/requirements/:id` |
| Criar | `Requirement.create(envelope_id:, **attrs)` | `POST /envelopes/:envelope_id/requirements` |
| Atualizar | `requirement.update(**attrs)` | `PATCH /envelopes/:envelope_id/requirements/:id` |
| Deletar | `requirement.delete` | `DELETE /envelopes/:envelope_id/requirements/:id` |

#### 3.4.2 Bulk (`resources :envelopes → :bulk_requirements`)

**Endpoint:** `POST /api/v3/envelopes/:envelope_id/bulk_requirements`

Operações em lote (JSON:API Atomic Operations). Request: `atomic:operations`; response: `atomic:results`.

**SDK:** `BulkRequirement.create(envelope_id:) { |ops| ... }` com `JsonApi::Operations::BulkRequirement`:

```ruby
response = BulkRequirement.create(envelope_id: envelope.id) do |ops|
  ops.add_agree(signer_id:, document_id:, role: 'sign')
  ops.add_provide_evidence(signer_id:, document_id:, auth: 'email')
  ops.add_rubricate(signer_id:, document_id:, pages: 'all')
  ops.remove(requirement_id:)
end

response.success?
response.requirements  # requirements criados (add com sucesso)
response.failures      # slots com errors
```

| Método do bloco | Uso |
|-----------------|-----|
| `add_agree` | `signer_id`, `document_id`, `role` |
| `add_provide_evidence` | `signer_id`, `document_id`, `auth` |
| `add_rubricate` | `signer_id`, `document_id`, `pages` e/ou `rubric_field`, opcional `kind` |
| `remove` | `requirement_id` |

---

### 3.5 Signature Watchers

**Endpoint base (nested):** `/api/v3/envelopes/:envelope_id/signature_watchers`

| Método | SDK | HTTP |
|--------|-----|------|
| Listar | `SignatureWatcher.list_for_envelope(id)` | `GET /envelopes/:id/signature_watchers` |
| Criar | `SignatureWatcher.create(**attrs)` | `POST /envelopes/:id/signature_watchers` |
| Buscar | `SignatureWatcher.retrieve(id)` | `GET /envelopes/:id/signature_watchers/:id` |
| Deletar | `signature_watcher.delete` | `DELETE /envelopes/:id/signature_watchers/:id` |

**Atributos:** `email`, `kind`, `communicate_events`, `attach_documents_enabled`, `created`, `modified`

---

### 3.6 Webhooks (`jsonapi_resources :webhooks`)

**Endpoint base:** `/api/v3/webhooks`

CRUD completo (list, retrieve, create, update, delete).

**Atributos:** `endpoint`, `secret`, `status`, `events`, `created`, `modified`

**Filtros:** `status`

---

### 3.7 Usuários (`jsonapi_resources :users, only: %i[index show create]`)

**Endpoint base:** `/api/v3/users`

| Método | SDK | HTTP |
|--------|-----|------|
| Listar | `User.list` | `GET /users` |
| Buscar | `User.retrieve(id)` | `GET /users/:id` |
| Criar | `User.create(**attrs)` | `POST /users` |
| Atual | `User.me` | `GET /users/me` |

**Atributos:** `name`, `email`, `phone_number`, `created`, `modified`

**Filtros:** `email`, `groups.key`

---

### 3.8 Memberships (`jsonapi_resources :memberships, only: %i[index create update destroy]`)

**Endpoint base:** `/api/v3/memberships`

**Atributos:** `role`, `consumption_accessible`, `tracking_accessible`, `folder_management_accessible`, `created`, `modified`

**Filtros:** `user.id`

**Relacionamentos:** `user` (has_one)

---

### 3.9 Grupos (`jsonapi_resources :groups`)

**Endpoint base:** `/api/v3/groups`

CRUD completo.

**Atributos:** `name`, `created`, `modified`

**Filtros:** `name`

**Ordenação:** `name`

**Relacionamentos:** `users` (has_many)

---

### 3.10 Templates (`jsonapi_resources :templates`)

**Endpoint base:** `/api/v3/templates`

CRUD completo.

**Atributos:** `name`, `color`, `content_base64`, `created`, `modified`

**Filtros:** `name`

**Relacionamentos:** `template_fields` (has_many)

**Sub-resources:**
- `GET /api/v3/template_fields` — listagem global de campos de template

---

### 3.11 Template Fields (`jsonapi_resources :template_fields, only: %i[index]`)

**Endpoint base:** `/api/v3/template_fields`

**Atributos:** `name`, `kind`, `created`, `modified`

**Relacionamentos:** `template` (has_one)

---

### 3.12 Folders (`jsonapi_resources :folders, only: %i[index create show]`)

**Endpoint base:** `/api/v3/folders`

| Método | SDK | HTTP |
|--------|-----|------|
| Listar | `Folder.list` | `GET /folders` |
| Buscar | `Folder.retrieve(id)` | `GET /folders/:id` |
| Criar | `Folder.create(**attrs)` | `POST /folders` |

**Atributos:** `name`, `path`, `in_root`, `created`, `modified`

**Filtros:** `in_root`

**Relacionamentos:** `folder` (has_one — pasta pai), `folders` (has_many — subpastas)

**Nota:** Folders são auto-referenciais. Requer `resolve_custom_type`.

---

### 3.13 Envelope Bulk Creations (`jsonapi_resources :envelope_bulk_creations, only: %i[create]`)

**Endpoint:** `POST /api/v3/envelope_bulk_creations`

**Atributos de resposta:** `job_id`, `enqueued_at`

---

### 3.14 Access Control Lists (`jsonapi_resource :access_control_lists, only: %i[create destroy]`)

**Endpoint base:** `/api/v3/access_control_lists`

Singular (não plural). Apenas criação e remoção.

| Método | SDK | HTTP |
|--------|-----|------|
| Criar | `AccessControlList.create(folder_id:, group_id:)` | `POST /access_control_lists` |
| Remover | `AccessControlList.destroy(folder_id:, group_id:)` | `DELETE /access_control_lists` (body com relationships) |

---

### 3.15 Auto Signature Terms (`namespace :auto_signature → jsonapi_resources :terms, only: :create`)

**Endpoint:** `POST /api/v3/auto_signature/terms`

**Atributos de criação:** `admin_email`, `api_email`, `signer` (objeto com `name`, `documentation`, `birthday`, `email`), `name`, `documentation`, `birthday`, `email`

**Atributos de resposta:** `name`, `documentation`, `birthday`, `email`, `created`, `modified`

---

### 3.16 Acceptance Term WhatsApps (`namespace :acceptance_term → jsonapi_resources :whatsapps, except: %i[destroy]`)

**Endpoint base:** `/api/v3/acceptance_term/whatsapps`

CRUD exceto destroy (list, retrieve, create, update).

**Atributos:** `sender_phone`, `signer_phone`, `signer_name`, `sender_name_option`, `sent_at`, `status`, `status_flow`, `title`, `message`, `created`, `modified`

**Filtros:** `status`

**Ordenação:** `created`

**Relacionamentos:** `messages` (has_many)

---

## 4. MAPEAMENTO DE ERROS

`Clicksign::ErrorHandler` inspeciona o status HTTP de toda resposta e levanta a exceção correta antes de retornar ao resource.

| HTTP | Exceção |
|------|---------|
| 401, 403 | `Clicksign::AuthenticationError` |
| 404 | `Clicksign::NotFoundError` |
| 400, 422 | `Clicksign::ValidationError` |
| 409 | `Clicksign::ConflictError` |
| 429 | `Clicksign::RateLimitError` |
| 5xx | `Clicksign::ServerError` |
| Falha de rede | `Clicksign::TimeoutError` |

Todos herdam de `Clicksign::Error < StandardError`. O resource não trata erros diretamente — delega ao `Client`.

---

## 5. CONVENÇÕES DE IMPLEMENTAÇÃO DO SDK

### Padrão de Resource

```ruby
module Clicksign
  module Resources
    module Notarial
      class Envelope < Clicksign::Resource
        self.resource_type = 'envelopes'

        # Relacionamentos via relationships hash
        def folder_id
          relationships.dig('folder', 'data', 'id')
        end

        # Criar com relacionamento
        def self.create(folder_id: nil, **attributes)
          rels = folder_id ? { folder: { data: { type: 'folders', id: folder_id } } } : {}
          super(**attributes, relationships: rels)
        end
      end
    end
  end
end
```

### Sub-resources (nested)

```ruby
def self.list_documents(envelope_id)
  nested_list(envelope_id, nested_type: 'documents')
end
```

### Nomenclatura de métodos

| Padrão SDK (usar) | Alternativas proibidas |
|----------------------|------------------------|
| `list` | `index`, `all`, `fetch` |
| `retrieve` | `show`, `get`, `find` |
| `create` | `new`, `build` |
| `update` | — |
| `delete` | `destroy`, `remove` |

### resource_type e endpoint

- `self.resource_type` — tipo JSON:API; default: nome da classe demodulado, underscored, pluralizado
- `self.endpoint` — caminho HTTP base; default: `"/#{resource_type}"`
- Definir explicitamente quando a rota não segue o padrão (ex: resources namespaceados nas rotas):

```ruby
self.resource_type = 'auto_signature_terms'
self.endpoint      = '/auto_signature/terms'
```

### Criação com relacionamentos

```ruby
resource = Notarial::Envelope.new(name: 'Meu Envelope')
resource.relationships[:folder] = { data: { type: 'folders', id: folder_id } }
resource.save
```

---

## 6. ESTRUTURA DE ARQUIVOS DO SDK

```
lib/
  clicksign.rb                    # ponto de entrada, require, configure
  clicksign/
    version.rb                    # VERSION
    configuration.rb              # api_key, base_url
    resource.rb                   # base com with_error_handling, raise_if_invalid
    parser.rb                     # deserialização JSON:API
    errors.rb                     # hierarquia de erros
    resources/
      notarial/                   # fluxo de assinatura (envelopes e ciclo de vida)
        envelope.rb
        document.rb
        signer.rb
        requirement.rb
        bulk_requirement.rb
        signature_watcher.rb
      auto_signature/             # namespace de rotas
        term.rb
      acceptance_term/            # namespace de rotas
        whatsapp.rb
      webhook.rb
      user.rb
      membership.rb
      group.rb
      template.rb
      template_field.rb
      folder.rb
      envelope_bulk_creation.rb
      access_control_list.rb
      event.rb

spec/
  spec_helper.rb
  clicksign/
    resources/
      notarial/
        envelope_spec.rb
        document_spec.rb
        signer_spec.rb
        requirement_spec.rb
        bulk_requirement_spec.rb
        signature_watcher_spec.rb
      # ... um spec por resource
  vcr_cassettes/               # gravados automaticamente na 1ª execução
```

---

## 7. PRIORIDADE DE IMPLEMENTAÇÃO

| Prioridade | Resource | Justificativa |
|-----------|----------|---------------|
| 1 | `Envelope` | Core do produto; todos os outros dependem dele |
| 2 | `Document` | Essencial para o fluxo de assinatura |
| 3 | `Signer` | Necessário junto com Document para ativar envelopes |
| 4 | `Requirement` | Define o que cada signatário deve fazer |
| 5 | `Webhook` | Fundamental para integrações orientadas a eventos |
| 6 | `Folder` | Organização de envelopes |
| 7 | `Template` + `TemplateField` | Fluxo avançado de criação de documentos |
| 8 | `User` + `Membership` + `Group` | Gestão de equipes |
| 9 | `SignatureWatcher` | Observadores de assinatura |
| 10 | `BulkRequirement` + `EnvelopeBulkCreation` | Operações em lote |
| 11 | `AutoSignature::Term` + `AcceptanceTerm::Whatsapp` | Funcionalidades específicas |
| 12 | `AccessControlList` | Controle de acesso a pastas por grupo |

---

## 8. REFERÊNCIAS

| Artefato | Descrição |
|----------|-----------|
| Rotas v3 | Clicksign API v3 (namespace :v3) |
| Resources | Recursos JSON:API v3 |
| Schema validators | Validadores de schema por operação |
| Controllers | Controllers da API v3 |
| Sandbox | `https://sandbox.clicksign.com/api/v3` |
| Produção | `https://app.clicksign.com/api/v3` |
