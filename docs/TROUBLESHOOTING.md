# Troubleshooting

Erros comuns ao integrar o SDK Python com a API 3.0 (Envelope).

---

## ValidationError (400 / 422)

A API devolve `ValidationError` quando o payload ou o estado do recurso é inválido.

**Exemplos frequentes:**

- Adicionar requisitos ou documentos depois que o envelope saiu de `draft`
- Atributos obrigatórios ausentes em `create` / `update`
- Conflito de regras de negócio (signatário já assinou, documento fechado, etc.)

```python
from clicksign import ValidationError

try:
    envelope.update(status="running")
except ValidationError as exc:
    print(exc.message)
    for err in exc.api_errors:
        print(err.detail, err.source)
```

Consulte também [`SDK_CONTRACT.md`](SDK_CONTRACT.md) (mapeamento HTTP → exceções).

---

## BulkRequirement — falha parcial sem exceção

`BulkRequirement.create` pode responder **HTTP 200** com slots com erro em `atomic:results`. O SDK **não** lança exceção nesse caso.

```python
from clicksign.resources.notarial.bulk_requirement import BulkRequirement

response = BulkRequirement.create(
    envelope_id,
    block=lambda ops: ops.add_agree(
        signer_id=signer.id,
        document_id=doc.id,
        role="sign",
    ),
)

if not response.success():
    for failure in response.failures:
        print(failure.index, failure.op, failure.errors)
    raise RuntimeError("bulk incompleto — não ative o envelope")
```

Detalhes: [`examples/02-bulk-requirements.md`](examples/02-bulk-requirements.md).

---

## Instrumentação some (erro do callback)

Hooks `on_request`, `on_retry` e `on_error` rodam **síncronos** no thread da requisição. Se o callback levantar exceção, o comportamento depende do ponto da pilha — trate erros **dentro** do handler.

```python
def safe_on_error(payload: dict) -> None:
    try:
        metrics.increment("clicksign.errors", tags={"status": payload.get("status")})
    except Exception:
        logger.exception("metrics callback failed")

client.http.on_error(safe_on_error)
```

Não use `Services.use()` dentro de corrotinas; prefira `AsyncClicksignClient` explícito — veja [`examples/08-production-limitations.md`](examples/08-production-limitations.md).

---

## RateLimitError (429)

O `Client` faz retry automático com jitter e respeita `Retry-After` quando presente. Se esgotar `max_retries`, propaga `RateLimitError` (`retryable=True`).

Mitigação: reduzir concorrência, cachear listagens, ou backoff no aplicativo.

---

## TimeoutError

Timeouts separados: `open_timeout`, `read_timeout`, `write_timeout` (global ou por `RequestOptions`). Falhas de rede também disparam retry quando `retryable`.

Bulk: apenas **timeout de rede** é retransmitido — não 5xx/429. Ver [`examples/01-retries.md`](examples/01-retries.md).

---

## WebhookSignatureError

Valide o corpo **bruto** (bytes) antes de parsear JSON. Header: `Content-HMAC` no formato `sha256=<hex>`.

```python
from clicksign import construct_event, WebhookSignatureError

try:
    event = construct_event(request.body, request.headers.get("Content-HMAC", ""), secret)
except WebhookSignatureError:
    return Response(status=401)
```

Receita completa: [`examples/03-webhooks.md`](examples/03-webhooks.md).

---

## Signer.notify — envelope_id e signer_id obrigatórios

`Signer.notify` é um **classmethod**: sempre informe `envelope_id` e `signer_id` (não há rota na raiz `/signers/{id}/notifications`).

```python
Signer.notify(envelope.id, signer.id, message="Lembrete")

# após retrieve — ainda precisa do envelope_id
signer = Signer.retrieve(signer_id)  # rota raiz; envelope_id vem de envelope.id ou relationships
Signer.notify(envelope.id, signer.id, message="Lembrete")
```

Na facade: `client.notarial.signers.notify(envelope_id, signer_id, message="...")`.

---

## Document / Signer `create` na facade

`Document.create` e `Signer.create` recebem o **id do envelope como primeiro argumento posicional**, não como `envelope_id=`:

```python
# correto
Document.create(envelope.id, filename="a.pdf", content_base64="...")
Signer.create(envelope.id, name="...", email="...")

# incorreto — envelope_id vira atributo do JSON por engano
Document.create(envelope_id=envelope.id, filename="a.pdf")
```

---

## Paginação — `page(n)` não fixa a página em `to_list()`

`Envelope.filter(...).page(3).per(25).to_list()` **não** retorna só a página 3: a auto-paginação começa em `page[number]=1` e segue até o fim.

Para uma página específica:

```python
Envelope.filter(status="draft").page(3).per(25).first()   # uma requisição, página 3
```

Detalhes e listagens aninhadas: [`PAGINATION.md`](PAGINATION.md).

---

## Eventos de envelope/documento

Não existe `GET /events` na raiz da conta. Use rotas aninhadas:

```python
from clicksign.resources.notarial.envelope import Envelope
from clicksign.resources.notarial.document import Document
from clicksign.resources.notarial.event import Event

Envelope.list_events(envelope_id)
Document.list_events(document_id, envelope_id=envelope_id)
Event.create_for_document(envelope_id, document_id, name="read")
```

---

## Referência

- Contrato: [`SDK_CONTRACT.md`](SDK_CONTRACT.md)
- Fluxo: [`WORKFLOW.md`](WORKFLOW.md) · [`README.md`](../README.md)
- Matriz de testes: [`SDK_TEST_MATRIX.md`](SDK_TEST_MATRIX.md)
