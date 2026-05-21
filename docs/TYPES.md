# Tipagem estática nos resources

Este documento descreve como a SDK expõe tipos para resources e como evoluir o catálogo sem quebrar consumidores.

## O que está tipado hoje

Resources com **TypedDict** de params e **properties** explícitas nos atributos conhecidos:

| Resource | Create / update / filter |
|----------|-------------------------|
| **Notarial** | `Envelope`, `Document`, `Signer`, `Requirement`, `SignatureWatcher`, `NotarialEvent` |
| **Conta** | `Webhook`, `Folder`, `User`, `Template`, `TemplateField`, `Membership`, `Group`, `AccountEvent` |

Import:

```python
from clicksign.types import EnvelopeCreateParams, UserCreateParams
from clicksign import Envelope, User

envelope = Envelope.create(name="Contract", locale="pt-BR")
user = User.create(name="Alice", email="alice@example.com")
assert envelope.name == "Contract"
```

`create(**attrs)` e `update(**attrs)` aceitam `typing_extensions.Unpack[...CreateParams]` / `UpdateParams` para autocomplete e checagem estática.

`filter(**kwargs)` retorna `QueryProxy[T]` (genérico), então `to_list()` é `list[T]`.

### Eventos (dois TypedDicts)

A API usa o mesmo `type: events` em rotas diferentes. O spec distingue:

- **`AccountEvent*`** — `clicksign.resources.event.Event` (`GET /events`)
- **`NotarialEvent*`** — `clicksign.resources.notarial.event.Event` (ex.: `Envelope.list_events`)

### Membership: filtro `user.id`

O filtro JSON:API `user.id` não é um identificador Python válido em `TypedDict`. Use:

```python
Membership.filter_for_user(user_id="uuid", role="admin")
# ou, sem tipagem estrita no filtro:
Membership.filter(**{"user.id": "uuid"})
```

## Fonte dos types

Os TypedDicts vivem em `src/clicksign/types/resources.py`, gerados a partir de `scripts/resource_type_spec.json`:

```bash
python scripts/generate_resource_types.py
```

O spec é **manual incremental** (não há OpenAPI publicado no repositório). Novos campos da API Clicksign entram no JSON e o script regenera os stubs.

## Versionamento

| Mudança na API | Estratégia no SDK |
|----------------|-------------------|
| Campo **opcional** novo | Adicionar ao spec com `total=False`; minor release |
| Campo **obrigatório** novo em create | Adicionar ao spec; pode exigir major se quebrar callers que mockam types |
| Campo removido | Manter no TypedDict como deprecated por 1 major, depois remover |
| Resource novo | Adicionar entrada no spec + classe + export opcional no root |

Regra prática: **TypedDicts só crescem em minors**; remoções ou renomeações só em major.

Atributos desconhecidos continuam acessíveis via `resource["custom_field"]` ou `__getattr__` em runtime — a tipagem cobre o subset documentado, não bloqueia campos extras da API.

## Checagem estática (CI)

```bash
pip install -e ".[dev]"
mypy
pytest -q
```

`pyproject.toml` usa `strict = true` nos módulos listados em `[tool.mypy] files`; resources tipados devem passar mypy sem `# type: ignore` desnecessários.

## Próximos passos (fora do §4)

- Resources admin restantes (`AccessControlList`, `EnvelopeBulkCreation`, …) conforme [`SDK_CLIENT_GAPS.md`](SDK_CLIENT_GAPS.md) §3
- `Required[...]` em create params quando a API publicar obrigatoriedade
- Integrar OpenAPI da Clicksign no gerador quando disponível
