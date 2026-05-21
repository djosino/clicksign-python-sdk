# Release — TestPyPI e PyPI

Fluxo de versão do SDK. Branches de release: **`release/<version>`** (ex.: `release/0.1.2`).

---

## Pré-requisitos

| Item | Onde |
|------|------|
| `REVISION` | Arquivo na raiz — só o número (ex.: `0.1.2`) |
| `CHANGELOG.md` | Seção `[X.Y.Z] - AAAA-MM-DD` |
| Trusted Publisher (TestPyPI) | [Publishing settings](https://test.pypi.org/manage/project/clicksign-python-sdk/settings/publishing/) |

### Trusted Publishing (TestPyPI)

1. **Add publisher** → GitHub  
2. **Owner:** `djosino`  
3. **Repository:** `clicksign-python-sdk`  
4. **Workflow name:** `publish-testpypi.yml`  
5. **Environment name:** *(vazio — não preencher)*  

O workflow **não** usa `environment:` no GitHub. Se o publisher no TestPyPI tiver `testpypi` no environment, o upload falha com `invalid-publisher`.

**Fallback:** secret `TEST_PYPI_API_TOKEN` no repositório e linhas `username`/`password` descomentadas em `.github/workflows/publish-testpypi.yml`.

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
