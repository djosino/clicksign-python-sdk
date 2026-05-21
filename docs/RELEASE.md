# Release — TestPyPI e PyPI

Fluxo de versão do SDK. Branches de release: **`release/<version>`** (ex.: `release/0.1.2`).

---

## Pré-requisitos

| Item | Onde |
|------|------|
| `REVISION` | Arquivo na raiz — só o número (ex.: `0.1.2`) |
| `CHANGELOG.md` | Seção `[X.Y.Z] - AAAA-MM-DD` |
| Secret `TEST_PYPI_API_TOKEN` | GitHub → Settings → Secrets → Actions (token de **test.pypi.org**) |

### Secret no GitHub (padrão do CI)

1. Crie token em https://test.pypi.org/manage/account/token/ (escopo: projeto `clicksign-python-sdk`)
2. No repositório: **Settings → Secrets and variables → Actions → New repository secret**
3. Nome: `TEST_PYPI_API_TOKEN` | Valor: `pypi-...` (token completo)

O workflow usa `username: __token__` + esse secret (mesmo fluxo do `twine upload` manual).

### Trusted Publishing (opcional, sem secret)

Só se quiser OIDC em vez de token — em [Publishing settings](https://test.pypi.org/manage/project/clicksign-python-sdk/settings/publishing/):

| Campo | Valor |
|--------|--------|
| Owner | `djosino` |
| Repository | `clicksign-python-sdk` |
| Workflow | `publish-testpypi.yml` |
| Environment | *(vazio)* |

Apague publishers antigos com Environment `testpypi`. Remova `username`/`password` do workflow para voltar ao OIDC.

**`invalid-publisher`:** o claim `sub` deve ser `repo:djosino/clicksign-python-sdk:ref:refs/heads/release/X.Y.Z` — confira owner/repo/workflow no TestPyPI (não em pypi.org).

---

## Publicar no TestPyPI (automático)

```bash
# 1. No main: atualizar REVISION + CHANGELOG, commit, push
git checkout main
git pull origin main

# 2. Branch de release (nome = versão em REVISION)
git checkout -b release/0.1.2
git push -u origin release/0.1.2
```

Isso dispara [publish-testpypi.yml](../.github/workflows/publish-testpypi.yml): valida (ruff + pytest), build e upload.

**Re-run:** Actions → *Publish to TestPyPI* → *Run workflow* (em `workflow_dispatch`).

### Instalar do TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  clicksign-python-sdk==0.1.2

python -c "import clicksign; print(clicksign.__version__)"
```

---

## Publicar no PyPI (produção) — manual

Token em **https://pypi.org** (não TestPyPI):

```bash
rm -rf dist/* && python -m build

export TWINE_USERNAME=__token__
export TWINE_PASSWORD='pypi-TOKEN_DE_PRODUCAO'

twine upload dist/*
```

---

## Tag Git (opcional)

```bash
git tag 0.1.2
git push origin 0.1.2
```

Tags não disparam o workflow; apenas marcam o commit na branch `release/<version>` ou no `main` após merge.
