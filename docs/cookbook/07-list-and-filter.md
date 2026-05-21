# List vs filter — consultas

Dois jeitos de listar recursos na API. Contratos **diferentes** de propósito.

---

## Regra rápida

| Precisa de | Use | Retorno |
|------------|-----|---------|
| Primeira página, sem filtros na chain | `Resource.list` | `Array` (já materializado) |
| Filtros, ordenação, página, includes, auto-pagination | `Resource.filter(...)` | `QueryProxy` até o terminal |

**Não use** `list` com argumentos — filtros vão em `filter`.

---

## `list` — primeira página simples

```ruby
Webhook = Clicksign::Resources::Webhook

hooks = Webhook.list   # => Array<Clicksign::Resources::Webhook>
hooks.each { |w| puts w.endpoint }
```

- Uma requisição GET na collection (parâmetros de paginação padrão da API).
- Não aceita `**filters` — `Webhook.list(status: 'active')` levanta `ArgumentError`.

---

## `filter` — query chainable

```ruby
Envelope = Clicksign::Resources::Notarial::Envelope

# Materializar primeira página com filtros
drafts = Envelope.filter(status: 'draft').to_a

# Chain completa
running = Envelope
  .filter(status: 'running', name: 'Contrato')
  .with_includes('folder')
  .order('-created')
  .page(1)
  .per(20)
  .to_a

# Atalhos (carregam uma página via to_a internamente)
Envelope.filter(status: 'draft').first
Envelope.filter(status: 'draft').count

# Todas as páginas
Envelope.filter(status: 'running').auto_paging_each { |e| process(e) }
```

Terminais comuns: `.to_a`, `.first`, `.last`, `.count`, `.each`, `.auto_paging_each`, `.each_page`, `.auto_paging`.

---

## Equivalências

| Antes (não suportado) | Agora |
|----------------------|--------|
| `Envelope.list(status: 'draft')` | `Envelope.filter(status: 'draft').to_a` |
| `Template.list(name: 'NDA')` | `Template.filter(name: 'NDA').to_a` |

---

## Listagens aninhadas (outro padrão)

Métodos como `Envelope.list_documents(envelope_id)` ou `Envelope.list_requirements(id, **filters)` são **rotas aninhadas** na API — não passam por `list` / `filter` da collection raiz. Consulte [`SPEC.md`](../SPEC.md).

---

## Referência

- README: [Filtros, ordenação e paginação](../../README.md#filtros-ordenação-e-paginação)
- Paginação `links.next`: [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
