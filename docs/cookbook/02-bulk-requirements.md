# Bulk requirements

Cria ou remove vários requisitos de assinatura em **uma** requisição (`POST /envelopes/:id/bulk_requirements`). Use quando o setup do signatário no documento já está definido e o envelope está em **`draft`**.

---

## Setup completo em uma chamada

```ruby
require 'clicksign'

Clicksign.configure do |c|
  c.api_key     = ENV.fetch('CLICKSIGN_API_KEY')
  c.environment = :sandbox
end

BulkRequirement = Clicksign::Resources::Notarial::BulkRequirement

# envelope, document e signer já criados (status draft)
response = BulkRequirement.create(envelope_id: envelope.id) do |ops|
  ops.add_agree(
    signer_id: signer.id,
    document_id: document.id,
    role: 'sign'
  )
  ops.add_provide_evidence(
    signer_id: signer.id,
    document_id: document.id,
    auth: 'email'
  )
  ops.add_rubricate(
    signer_id: signer.id,
    document_id: document.id,
    pages: 'all'
  )
end
```

---

## Tratar sucesso parcial (`atomic:results`)

A API pode responder com HTTP 200 e slots com erro — **sem** lançar exceção Ruby. Inspecione `response.success?` e `response.failures`:

```ruby
if response.success?
  response.requirements.each do |r|
    puts "OK: #{r.id} (#{r.action})"
  end
else
  response.failures.each do |failure|
    puts "Falha no slot #{failure.index} op=#{failure.op}: #{failure.errors}"
  end
  # abortar ativação, compensar (rollback manual), alertar operador
end
```

Cada `failure` expõe `index`, `op`, `errors` e `raw` (slot bruto da API).

---

## Remover e adicionar no mesmo bulk

```ruby
response = BulkRequirement.create(envelope_id: envelope.id) do |ops|
  ops.remove(requirement_id: requisito_antigo.id)
  ops.add_agree(
    signer_id: signer.id,
    document_id: document.id,
    role: 'sign'
  )
end
```

---

## Rubrica em campo específico

```ruby
ops.add_rubricate(
  signer_id: signer.id,
  document_id: document.id,
  rubric_field: 'campo_rubrica_1',
  kind: 'initials'   # opcional: initials | manuscript
)
```

É obrigatório informar `pages` **ou** `rubric_field`.

---

## Erro no envelope inteiro (422)

Quando a API devolve erros **top-level** (sem `atomic:results`), a gem lança `Clicksign::ValidationError`:

```ruby
begin
  BulkRequirement.create(envelope_id: envelope.id) do |ops|
    ops.add_agree(signer_id: signer.id, document_id: document.id, role: 'sign')
  end
rescue Clicksign::ValidationError => e
  puts e.message
  puts e.response_body
end
```

---

## Bulk vs requirement individual

| | `Requirement.create` | `BulkRequirement.create` |
|--|----------------------|--------------------------|
| Chamadas HTTP | 1 por requisito | 1 para N operações |
| Falha parcial | Exceção por request | `response.failures` por slot |
| Retry em 5xx / 429 | Sim (`Client`) | Não — só timeout de rede no bulk client |
| Bloco obrigatório | Não | Sim (`ArgumentError` sem block) |

---

## Ativar o envelope depois do bulk

Só ative quando a política de negócio permitir (ex.: todos os slots OK):

```ruby
if response.success?
  envelope.update(status: 'running')
end
```

---

## Referência

- README: [Requisitos — operações em lote](../../README.md#42-operações-em-lote-bulk)
- Implementação: `lib/clicksign/resources/notarial/bulk_requirement.rb`, `lib/clicksign/json_api/operations/bulk_requirement.rb`
