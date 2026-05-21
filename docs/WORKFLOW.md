# Fluxo completo de assinatura

Guia do ciclo de vida de um envelope na API 3.0 (Envelope): criação, documento, signatário, requisitos, ativação, notificação e monitoramento.

**Documentação relacionada:** [Examples](examples/) · [Troubleshooting](TROUBLESHOOTING.md) · [Arquitetura](ARCHITECTURE.md) · [Observabilidade](OBSERVABILITY.md) · [README do pacote](../README.md)

---

## Configuração inicial

```python
import os
import clicksign
from clicksign.resources.notarial.envelope import Envelope
from clicksign.resources.notarial.document import Document
from clicksign.resources.notarial.signer import Signer
from clicksign.resources.notarial.requirement import Requirement

clicksign.configure(api_key=os.environ["CLICKSIGN_API_KEY"], environment="sandbox")
```

---

## 1. Criar o envelope

O envelope é o contêiner do processo. Começa em `draft`.

```python
envelope = Envelope.create(
    name="Contrato de prestação de serviços",
    locale="pt-BR",
    auto_close=True,
    remind_interval=3,
)

print(envelope.id)      # uuid do envelope
print(envelope.status)  # draft
```

> **`auto_close=True`** fecha o envelope após todas as assinaturas.  
> **`remind_interval=3`** envia lembretes automáticos a cada 3 dias (conforme regras da conta).

---

## 2. Adicionar o documento

Envie o PDF em Base64 no formato `data:<mime>;base64,<conteúdo>`.

```python
import base64

pdf_bytes = open("contrato.pdf", "rb").read()
pdf_base64 = "data:application/pdf;base64," + base64.b64encode(pdf_bytes).decode()

document = Document.create(
    envelope.id,
    filename="contrato.pdf",
    content_base64=pdf_base64,
)

print(document.id)
print(document.status)  # draft
```

**Outros modos de criação** (mutuamente exclusivos na API — consulte [`SPEC.md`](SPEC.md)):

```python
# URL pública (quando suportado pela API)
Document.create(envelope.id, filename="contrato.pdf", content_url="https://...")

# Template (atributos conforme documentação Clicksign)
Document.create(envelope.id, filename="contrato.docx", template_key="uuid-do-template")
```

---

## 3. Adicionar o signatário

```python
signer = Signer.create(
    envelope.id,
    name="Maria Silva",
    email="maria.silva@example.com",
    phone_number="11999998888",
    has_documentation=True,
)

print(signer.id)
print(signer.envelope_id)
```

> Canais de notificação (`communicate_events`, etc.) seguem o contrato JSON:API da Clicksign — passe atributos adicionais suportados pela API se necessário.

---

## 4. Criar os requisitos de assinatura

Os requisitos definem **o que** o signatário deve fazer em cada documento.

### 4.1 Concordância (`agree`)

```python
agree = Requirement.create(
    envelope.id,
    signer_id=signer.id,
    document_id=document.id,
    action="agree",
    role="sign",
)

print(agree.id, agree.action)
```

### 4.2 Evidência de autenticação (`provide_evidence`)

```python
evidence = Requirement.create(
    envelope.id,
    signer_id=signer.id,
    document_id=document.id,
    action="provide_evidence",
    auth="email",
)

print(evidence.id, evidence.action)
```

**Valores comuns de `auth`:** `email`, `sms`, `whatsapp`, `pix`, `selfie`, `liveness`, `handwritten`, `official_document`, `facial_biometrics` (conforme conta/API).

---

## 5. Ativar o envelope

Com documentos, signatários e requisitos prontos, altere o status para `running` (PATCH). Isso inicia o fluxo de assinatura.

```python
envelope.update(status="running")
print(envelope.status)  # running
```

Alternativa explícita (POST `/activate`):

```python
envelope = Envelope.activate(envelope.id)
```

> **Atenção:** após ativado, novos requisitos em `draft` falham com `ValidationError`. Ver [Troubleshooting](TROUBLESHOOTING.md#validationerror-400-422).

---

## 6. Notificar signatários

Com o envelope em `running`, dispare o link de assinatura.

### Todos os signatários pendentes (envelope)

```python
envelope.notify(message="Seu contrato está disponível para assinatura.")
```

### Um signatário

```python
Signer.notify(envelope.id, signer.id, message="Lembrete: seu documento aguarda assinatura.")
Signer.notify(
    envelope.id,
    signer.id,
    message="Por favor, assine até sexta-feira.",
    subject="Ação necessária: assinatura pendente",
)
```

---

## Fluxo completo (resumo)

```python
import base64
import os
import clicksign
from clicksign.resources.notarial.envelope import Envelope
from clicksign.resources.notarial.document import Document
from clicksign.resources.notarial.signer import Signer
from clicksign.resources.notarial.requirement import Requirement

clicksign.configure(api_key=os.environ["CLICKSIGN_API_KEY"], environment="sandbox")

# 1. Envelope
envelope = Envelope.create(name="Contrato ACME", locale="pt-BR", auto_close=True)

# 2. Documento
pdf_b64 = "data:application/pdf;base64," + base64.b64encode(
    open("contrato.pdf", "rb").read()
).decode()
document = Document.create(envelope.id, filename="contrato.pdf", content_base64=pdf_b64)

# 3. Signatário
signer = Signer.create(envelope.id, name="Maria Silva", email="maria@example.com")

# 4. Requisitos
Requirement.create(envelope.id, signer_id=signer.id, document_id=document.id, action="agree", role="sign")
Requirement.create(envelope.id, signer_id=signer.id, document_id=document.id, action="provide_evidence", auth="email")

# 5. Ativar
envelope.update(status="running")

# 6. Notificar
Signer.notify(envelope.id, signer.id, message="Seu contrato ACME está disponível para assinatura.")

print(f"Envelope {envelope.id} ativo e signatário notificado.")
```

---

## Alternativa: requisitos em lote

Uma única requisição HTTP para vários requisitos (`BulkRequirement`):

```python
from clicksign.resources.notarial.bulk_requirement import BulkRequirement

response = BulkRequirement.create(
    envelope.id,
    block=lambda ops: (
        ops.add_agree(signer_id=signer.id, document_id=document.id, role="sign"),
        ops.add_provide_evidence(signer_id=signer.id, document_id=document.id, auth="email"),
    ),
)

if response.success():
    print(len(response.requirements), "requisitos criados")
else:
    for failure in response.failures:
        print(failure.index, failure.op, failure.errors)
```

Detalhes: [examples/02-bulk-requirements.md](examples/02-bulk-requirements.md). Falha parcial: [TROUBLESHOOTING.md](TROUBLESHOOTING.md#bulkrequirement--falha-parcial-sem-exceção).

---

## Monitorar o progresso

### Eventos e estado (API)

```python
for event in Envelope.list_events(envelope.id):
    print(event.name, event.created)

for event in Document.list_events(document.id, envelope_id=envelope.id):
    print(event.name, event.data)

for s in Envelope.list_signers(envelope.id):
    print(s.name, s.email)

envelope = Envelope.retrieve(envelope.id)
print(envelope.status)  # running, closed, cancelled, ...
```

### Webhooks (tempo real)

Callbacks HTTP na sua aplicação — não confundir com o resource `Event` acima. Ver [examples/03-webhooks.md](examples/03-webhooks.md).

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
| Multi-conta / workers | [examples/04-multi-client.md](examples/04-multi-client.md) |
| Retries e timeouts | [examples/01-retries.md](examples/01-retries.md) |
| Webhooks | [examples/03-webhooks.md](examples/03-webhooks.md) |
| Logs e métricas | [OBSERVABILITY.md](OBSERVABILITY.md) |
| Erros comuns | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Async / FastAPI | [README § Async](../README.md#async-fastapi-asyncio) |
