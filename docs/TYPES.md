# Tipagem estática nos resources

Este documento descreve como o SDK expõe tipos para resources e como evoluir o catálogo sem quebrar consumidores.

## O que está tipado hoje

Resources com **TypedDict** de params e **properties** explícitas nos atributos conhecidos:

| Resource | Create / update / filter |
|----------|-------------------------|
| **Notarial** | `Envelope`, `Document`, `Signer`, `Requirement` (`auth` em create, ex. `"email"`), `SignatureWatcher`, `NotarialEvent` |
| **Conta** | `Webhook`, `Folder`, `User`, `Template`, `TemplateField`, `Membership`, `Group` |

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

- **`NotarialEvent*`** — `clicksign.resources.notarial.event.Event` (`Envelope.list_events`, `Document.list_events`, `Event.create_for_document`)

### Membership: filtro `user.id`

O filtro JSON:API `user.id` não é um identificador Python válido em `TypedDict`. Use:

```python
Membership.filter_for_user(user_id="uuid", role="admin")
# ou, sem tipagem estrita no filtro:
Membership.filter(**{"user.id": "uuid"})
```

## Fonte dos types

Os TypedDicts ficam em `src/clicksign/types/resources.py`, gerados a partir de `scripts/resource_type_spec.json`:

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

Regra prática: **TypedDicts só crescem em minors**; remoções ou renomeações apenas em major.

Atributos desconhecidos continuam acessíveis via `resource["custom_field"]` ou `__getattr__` em runtime — a tipagem cobre o subconjunto documentado, não bloqueia campos extras da API.

## Checagem estática (CI)

```bash
pip install -e ".[dev]"
mypy
pytest -q
```

`pyproject.toml` usa `strict = true` nos módulos listados em `[tool.mypy] files`; resources tipados devem passar no mypy sem `# type: ignore` desnecessários.

## Imports fora de `clicksign.__all__`

Alguns resources existem no pacote mas **não** são reexportados na raiz (`import clicksign`). Use submódulo:

```python
from clicksign.resources.notarial.event import Event
from clicksign.resources.user import User
from clicksign.resources.template import Template
from clicksign.resources.membership import Membership
from clicksign.resources.group import Group
from clicksign.resources.access_control_list import AccessControlList
```

Na raiz hoje: `Envelope`, `Document`, `Signer`, `Requirement`, `BulkRequirement`, `SignatureWatcher`, `Webhook`, `Folder` — ver `clicksign.__all__` em `src/clicksign/__init__.py`.

## Próximos passos (tipagem)

- Resources admin restantes (`AccessControlList`, `EnvelopeBulkCreation`, …) conforme [`SPEC.md`](SPEC.md)
- `Required[...]` em create params quando a API publicar obrigatoriedade
- Integrar OpenAPI da Clicksign no gerador quando disponível
