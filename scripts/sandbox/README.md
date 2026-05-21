# Scripts sandbox (local)

Testes manuais contra **sandbox** com o SDK do repositório. **Não commitar** `.env` nem `.last_run.json`.

## Setup

```bash
cd /caminho/clicksign-python-sdk
cp scripts/sandbox/.env.example scripts/sandbox/.env
# edite .env se necessário (já existe .env local com token)
```

## Rodar

```bash
# da raiz do repo
export PYTHONPATH=src

python scripts/sandbox/01_list_collections.py
python scripts/sandbox/02_create_notarial_draft.py
python scripts/sandbox/03_consult_envelope.py
# opcional — ativa e notifica (cuidado: e-mail real do signatário no passo 2)
python scripts/sandbox/04_activate_optional.py
```

## O que cada script faz

| Script | Ação |
|--------|------|
| `01_list_collections.py` | Lista envelopes, folders, webhooks, users |
| `02_create_notarial_draft.py` | Cria envelope + PDF mínimo + signatário + bulk (draft) |
| `03_consult_envelope.py` | Retrieve + listagens aninhadas + eventos |
| `04_activate_optional.py` | Ativa (`update` se `/activate` der 403) + `envelope.notify` |

IDs do último `02_*` ficam em `scripts/sandbox/.last_run.json`.
