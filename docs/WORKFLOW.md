# Fluxo completo de assinatura

Este guia percorre o ciclo de vida completo de um envelope: criação, adição de documento e signatário, configuração dos requisitos de assinatura, ativação e notificação.

**Documentação relacionada:** [Cookbook](cookbook/) (receitas) · [Troubleshooting](TROUBLESHOOTING.md) (erros comuns) · [Arquitetura](ARCHITECTURE.md) · [Observabilidade](OBSERVABILITY.md)

---

## Configuração inicial

```ruby
require 'clicksign'

Clicksign.configure do |c|
  c.api_key     = ENV.fetch('CLICKSIGN_API_KEY')
  c.environment = :sandbox   # ou :production
  # c.base_url = ENV['CLICKSIGN_API_BASE_URL']  # opcional: sobrescreve environment
end

Envelope          = Clicksign::Resources::Notarial::Envelope
Document          = Clicksign::Resources::Notarial::Document
Signer            = Clicksign::Resources::Notarial::Signer
Requirement       = Clicksign::Resources::Notarial::Requirement
```

---

## 1. Criar o envelope

O envelope é o contêiner do processo de assinatura. Começa com status `draft`.

```ruby
envelope = Envelope.create(
  name:            'Contrato de prestação de serviços',
  locale:          'pt-BR',
  auto_close:      true,
  remind_interval: 3,
  default_subject: 'Documentos aguardando sua assinatura',
  default_message: 'Por favor, revise e assine os documentos em anexo.',
)

puts envelope.id     # => "uuid-do-envelope"
puts envelope.status # => "draft"
```

> **`auto_close: true`** fecha o envelope automaticamente após todas as assinaturas.
> **`remind_interval: 3`** envia lembretes automáticos a cada 3 dias.

---

## 2. Adicionar o documento

Envie o PDF em Base64. O arquivo deve estar no formato `data:<mime>;base64,<conteúdo>`.

```ruby
pdf_base64 = "data:application/pdf;base64,#{Base64.strict_encode64(File.read('contrato.pdf'))}"

document = Document.create(
  envelope_id:  envelope.id,
  filename:     'contrato.pdf',
  content_base64: pdf_base64,
)

puts document.id       # => "uuid-do-documento"
puts document.status   # => "draft"
```

**Alternativas ao `content_base64`** (mutuamente exclusivas):

```ruby
# A partir de URL pública:
Document.create(envelope_id: envelope.id, filename: 'contrato.pdf',
                content_url: 'https://meusite.com/contrato.pdf')

# A partir de template:
Document.create(envelope_id: envelope.id, filename: 'contrato.docx',
                template: { key: 'uuid-do-template', data: { cliente: 'ACME' } })
```

---

## 3. Adicionar o signatário

```ruby
signer = Signer.create(
  envelope_id:  envelope.id,
  name:         'Maria Silva',
  email:        'maria.silva@example.com',
  phone_number: '11999998888',
  refusable:    true,
  communicate_events: {
    signature_request:  'email',  # avisa o signatário quando enviado para assinar
    signature_reminder: 'email',  # lembrete automático se não assinar
    document_signed:    'email',  # confirmação após assinar
  },
)

puts signer.id          # => "uuid-do-signer"
puts signer.envelope_id # => "uuid-do-envelope"
```

> **`refusable: true`** permite que o signatário recuse o documento.
> **`communicate_events`** define o canal por tipo de evento (`signature_request`, `signature_reminder`, `document_signed`).

---

## 4. Criar os requisitos de assinatura

Os requisitos definem **o que** o signatário deve fazer no documento.

### 4.1 Requisito de concordância (`agree`)

Exige que o signatário assine o documento.

```ruby
agree = Requirement.create(
  envelope_id: envelope.id,
  action:      'agree',
  role:        'sign',
  relationships: {
    document: { data: { type: 'documents', id: document.id } },
    signer:   { data: { type: 'signers',   id: signer.id } },
  },
)

puts agree.id     # => "uuid-do-requisito-agree"
puts agree.action # => "agree"
```

### 4.2 Requisito de evidência de autenticação (`provide_evidence`)

Exige autenticação do signatário (e-mail, SMS, selfie, etc.).

```ruby
evidence = Requirement.create(
  envelope_id: envelope.id,
  action:      'provide_evidence',
  auth:        'email',
  relationships: {
    document: { data: { type: 'documents', id: document.id } },
    signer:   { data: { type: 'signers',   id: signer.id } },
  },
)

puts evidence.id     # => "uuid-do-requisito-evidence"
puts evidence.action # => "provide_evidence"
puts evidence.auth   # => "email"
```

**Valores suportados para `auth`:** `email`, `sms`, `whatsapp`, `pix`, `selfie`, `liveness`, `handwritten`, `official_document`, `facial_biometrics`.

---

## 5. Ativar o envelope

Após configurar documentos, signatários e requisitos, atualize o `status` para `running` via PATCH. Isso inicia o fluxo de assinatura.

```ruby
running_envelope = envelope.update(status: 'running')

puts running_envelope.status # => "running"
```

> **Atenção:** após ativado, o envelope não pode mais receber novos requisitos. Qualquer tentativa retorna `ValidationError`. Ver [Troubleshooting — ValidationError](TROUBLESHOOTING.md#validationerror-400-422).

---

## 6. Enviar notificação ao signatário

Com o envelope em `running`, envie o link de assinatura por e-mail.

### Via envelope (notifica todos os signatários pendentes)

```ruby
envelope.notify(message: 'Seu contrato está disponível para assinatura.')
```

### Via signatário (notifica um signatário específico)

```ruby
signer.notify(message: 'Lembrete: seu documento aguarda assinatura.')
```

### Com personalização de e-mail

```ruby
signer.notify(
  message: 'Por favor, assine até sexta-feira.',
  subject: 'Ação necessária: assinatura pendente',
)
```

---

## Fluxo completo (resumo)

```ruby
require 'clicksign'

Clicksign.configure do |c|
  c.api_key     = ENV.fetch('CLICKSIGN_API_KEY')
  c.environment = :sandbox
end

Envelope    = Clicksign::Resources::Notarial::Envelope
Document    = Clicksign::Resources::Notarial::Document
Signer      = Clicksign::Resources::Notarial::Signer
Requirement = Clicksign::Resources::Notarial::Requirement

# 1. Envelope
envelope = Envelope.create(name: 'Contrato ACME', locale: 'pt-BR', auto_close: true)

# 2. Documento
pdf_base64 = "data:application/pdf;base64,#{Base64.strict_encode64(File.read('contrato.pdf'))}"
document = Document.create(envelope_id: envelope.id, filename: 'contrato.pdf',
                           content_base64: pdf_base64)

# 3. Signatário
signer = Signer.create(
  envelope_id: envelope.id,
  name:        'Maria Silva',
  email:       'maria@example.com',
  refusable:   true,
)

# 4. Requisitos
rels = {
  document: { data: { type: 'documents', id: document.id } },
  signer:   { data: { type: 'signers',   id: signer.id } },
}

Requirement.create(envelope_id: envelope.id, action: 'agree', role: 'sign',
                   relationships: rels)
Requirement.create(envelope_id: envelope.id, action: 'provide_evidence', auth: 'email',
                   relationships: rels)

# 5. Ativar — atualiza status para running via PATCH
envelope.update(status: 'running')

# 6. Notificar
signer.notify(message: 'Seu contrato ACME está disponível para assinatura.')

puts "Envelope #{envelope.id} ativo e signatário notificado."
```

---

## Alternativa: requisitos em lote

Para configurar todos os requisitos em uma única chamada HTTP, use `BulkRequirement`:

```ruby
BulkRequirement = Clicksign::Resources::Notarial::BulkRequirement

response = BulkRequirement.create(envelope_id: envelope.id) do |ops|
  ops.add_agree(signer_id: signer.id, document_id: document.id, role: 'sign')
  ops.add_provide_evidence(signer_id: signer.id, document_id: document.id, auth: 'email')
end

if response.success?
  puts "#{response.requirements.size} requisitos criados."
else
  response.failures.each { |f| puts "Erro: #{f.errors}" }
end
```

Detalhes: [cookbook/02-bulk-requirements.md](cookbook/02-bulk-requirements.md). Falha parcial sem exceção: [TROUBLESHOOTING.md](TROUBLESHOOTING.md#bulkrequirement--falha-parcial-sem-exceção).

---

## Monitorar o progresso

```ruby
# Listar eventos do envelope
Envelope.list_events(envelope.id).each do |event|
  puts "#{event.name} — #{event.created}"
end

# Listar signatários e status
Envelope.list_signers(envelope.id).each do |s|
  puts "#{s.name} <#{s.email}>"
end

# Recarregar estado atual do envelope
envelope = envelope.reload
puts envelope.status # "running", "closed", "cancelled"...
```

---

## Estados possíveis do envelope

| Status | Descrição |
|--------|-----------|
| `draft` | Em configuração — documentos e requisitos podem ser adicionados |
| `running` | Ativo — aguardando assinaturas |
| `closed` | Concluído — todos os requisitos cumpridos |
| `cancelled` | Cancelado manualmente |

---

## Próximos passos

| Necessidade | Documento |
|-------------|-----------|
| Multi-conta / Sidekiq | [cookbook/04-multi-client.md](cookbook/04-multi-client.md) |
| Retries e timeouts | [cookbook/01-retries.md](cookbook/01-retries.md) |
| Webhooks de eventos | [cookbook/03-webhooks.md](cookbook/03-webhooks.md) |
| Logs e métricas | [OBSERVABILITY.md](OBSERVABILITY.md) |
| Erro inesperado | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
