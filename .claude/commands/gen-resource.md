Gere um novo resource para o SDK em src/clicksign/resources/$ARGUMENTS.py.

## Passo 0 — Bootstrap (apenas se a infraestrutura não existir)

Verifique se `src/clicksign/resource.py` existe. Se **não existir**, implemente toda a
infraestrutura base antes de gerar o resource, seguindo rigorosamente `docs/SDK_CONTRACT.md`
e `docs/SDK_TEST_MATRIX.md`.

### Infraestrutura base

**`pyproject.toml`**
- `name = "clicksign"`
- `requires-python = ">=3.10"`
- Sem dependências de runtime (stdlib apenas, ou `httpx` se adotado)
- Dev: `pytest`, `pytest-cov`, `responses` (ou `pytest-httpx`), `ruff`, `mypy`

**`REVISION`**
- Arquivo com apenas a versão, ex: `0.1.0`

**`src/clicksign/version.py`**
```python
from pathlib import Path
VERSION = (Path(__file__).parent.parent.parent / "REVISION").read_text().strip()
```

**`src/clicksign/errors.py`**
Hierarquia completa conforme `docs/SDK_CONTRACT.md` seção 5.

**`src/clicksign/retry_backoff.py`**
Full jitter conforme seção 6 do contrato.

**`src/clicksign/instrumentation.py`**
Três eventos, callbacks isolados, logger opcional.

**`src/clicksign/error_handler.py`**
Mapeia status HTTP → exceção. Todas as regras de extração de mensagem da seção 5.

**`src/clicksign/json_api/`** — parser, serializer, query_builder, operations

**`src/clicksign/client.py`**
HTTP client com urllib, timeouts, retry, `RequestInstrumentation` mixin.

**`src/clicksign/resource.py`**
Base class: CRUD, QueryProxy, `__getattr__`, `__getitem__`, auto-pagination.

**`tests/conftest.py`**
```python
import pytest
import clicksign

BASE_URL = "https://test.clicksign.com/api/v3"

@pytest.fixture(autouse=True)
def configure_sdk():
    clicksign.configure(api_key="test-token", base_url=BASE_URL)
    yield
    clicksign.reset()
    clicksign.instrumentation.clear()
```

---

## Passo 1 — Fontes da verdade (ler nesta ordem)

1. **Rotas**: `~/workspace/harness/tavola/config/routes/api.rb` — `only:` determina métodos disponíveis
2. **Resource**: `~/workspace/harness/tavola/app/resources/api/v3/{name}_resource.rb` — atributos, relacionamentos, filtros
3. **Controller**: `~/workspace/harness/tavola/app/controllers/api/v3/{name}_controller.rb` — actions customizadas
4. **Schemas**: `~/workspace/harness/tavola/lib/schema_validator/api/v3/{name}/` — campos required/optional

---

## Passo 2 — Implementar o resource

### Namespace e caminho

| Resources | Módulo Python | Caminho |
|-----------|---------------|---------|
| Envelope, Document, Signer, Requirement, BulkRequirement, SignatureWatcher, Event | `clicksign.resources.notarial` | `src/clicksign/resources/notarial/{name}.py` |
| Term | `clicksign.resources.auto_signature` | `src/clicksign/resources/auto_signature/term.py` |
| Whatsapp | `clicksign.resources.acceptance_term` | `src/clicksign/resources/acceptance_term/whatsapp.py` |
| Demais | `clicksign.resources` | `src/clicksign/resources/{name}.py` |

### resource_type e endpoint

```python
class Envelope(Resource):
    resource_type = 'envelopes'
    # endpoint = '/envelopes'  # omitir se igual ao padrão
```

Namespaced (ex: Term):
```python
class Term(Resource):
    resource_type = 'auto_signature_terms'
    endpoint = '/auto_signature/terms'
```

### Métodos — implementar apenas os disponíveis nas rotas

```python
@classmethod
def list(cls): ...          # GET /resources

@classmethod
def retrieve(cls, id): ...  # GET /resources/:id

@classmethod
def create(cls, **attrs): ...  # POST /resources

def update(self, **attrs): ...   # PATCH /resources/:id

def delete(self): ...            # DELETE /resources/:id
```

### Rotas com except: [:update]

```python
def update(self, **kwargs):
    raise NotImplementedError("Resource does not support update")
```

### Relacionamentos

```python
@property
def folder_id(self):
    return self.relationships.get('folder', {}).get('data', {}).get('id')
```

---

## Passo 3 — Testes

Crie `tests/resources/{module}/{name}_test.py`.

### Regras

- **Idioma**: inglês em todos os `describe`/`context`/`it` equivalentes
- Use `pytest` com classes de teste ou funções prefixadas com `test_`
- Use `responses` (ou `pytest-httpx`) para stub HTTP — sem rede real
- Consulte `docs/SDK_TEST_MATRIX.md` seção "Resource specs" para cobertura obrigatória
- UUIDs: `'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'` — nunca UUIDs reais de sandbox

### Estrutura mínima

```python
import pytest
import responses as rsps_lib

from clicksign.resources.notarial.envelope import Envelope
from tests.support.json_api_fixtures import BASE_URL, single_resource, collection_resource, envelope_data

class TestResourceConfiguration:
    def test_resource_type(self):
        assert Envelope.resource_type == 'envelopes'

    def test_endpoint(self):
        assert Envelope.endpoint == '/envelopes'


class TestList:
    @rsps_lib.activate
    def test_returns_list_of_instances(self, envelope_fixture):
        rsps_lib.add(rsps_lib.GET, f"{BASE_URL}/envelopes",
                     json=collection_resource([envelope_fixture]), status=200)
        result = Envelope.list()
        assert isinstance(result, list)
        assert all(isinstance(e, Envelope) for e in result)


class TestCreate:
    @rsps_lib.activate
    def test_returns_new_instance(self, envelope_fixture):
        rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/envelopes",
                     json=single_resource(envelope_fixture), status=201)
        env = Envelope.create(name='Contract')
        assert isinstance(env, Envelope)

    @rsps_lib.activate
    def test_raises_validation_error_on_422(self):
        rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/envelopes",
                     json={'errors': [{'detail': 'name is blank'}]}, status=422)
        with pytest.raises(clicksign.ValidationError, match='name is blank'):
            Envelope.create(name='')
```
