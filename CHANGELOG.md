# Changelog

Todas as mudanças relevantes neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.2] - 2026-05-21

### Adicionado

- CI: workflow `publish-testpypi.yml` — publica no TestPyPI em push para `release/<version>`
- Documentação de release em `docs/RELEASE.md`

### Corrigido

- Trusted Publishing: workflow sem GitHub Environment (evita `invalid-publisher` no TestPyPI)

---

## [0.1.1] - 2026-05-21

### Alterado

- Nome do pacote no PyPI/TestPyPI: `clicksign-python-sdk` (`pip install clicksign-python-sdk`; import permanece `clicksign`)

### Corrigido

- `clicksign.__version__` após `pip install`: lê versão dos metadados do pacote (antes dependia de `REVISION`, ausente no wheel)

---

## [0.1.0] - 2026-05-21

Primeira release do SDK Python para a API Clicksign v3 (JSON:API). Versão alinhada a `REVISION`.

### Adicionado

- SDK Python para API v3: resources notariais (`Envelope`, `Document`, `Signer`, `Requirement`, `BulkRequirement`, `SignatureWatcher`, eventos aninhados) e administrativos (`Webhook`, `Folder`, `User`, `Template`, `TemplateField`, `Membership`, `Group`, e parciais)
- `configure()` + resources, `ClicksignClient` / `AsyncClicksignClient`, `Services`, webhooks HMAC (`construct_event`, `verify_signature`)
- HTTP stdlib (`UrllibHTTPClient`) e opcional `httpx` / `HttpxAsyncHTTPClient` para sync e async
- Retry com jitter, header `Retry-After`, mapeamento de erros JSON:API, `RequestOptions`, correlation id
- Paginação via `QueryProxy`, `with_includes`, bulk atômico (`BulkRequirement`)
- TypedDicts em `clicksign.types` para resources principais
- Documentação em `docs/` (contrato, workflow, spec, troubleshooting, 11 receitas)
- Suíte de testes com mocks HTTP (483+ testes), CI com ruff, mypy e cobertura mínima 88%

### Alterado

- N/A (release inicial)

### Corrigido

- N/A (release inicial)

### Notas de breaking (desde pré-release interna)

- `Signer.notify(envelope_id, signer_id, message, ...)` — classmethod com rota aninhada; não há `POST /signers/:id/notifications`
- Eventos apenas em rotas aninhadas (`Envelope.list_events`, `Document.list_events`, `Event.create_for_document`)
