# Release — TestPyPI → PyPI

Uma branch **`release/<version>`** dispara o CI completo: testes → TestPyPI → PyPI (mesmo artefato `dist/`).

---

## Pré-requisitos

| Item | Onde |
|------|------|
| `REVISION` | Raiz do repo (ex.: `0.1.2`) |
| `CHANGELOG.md` | Seção `[X.Y.Z] - AAAA-MM-DD` |
| `TEST_PYPI_API_TOKEN` | GitHub Secrets — token de **https://test.pypi.org** |
| `PYPI_API_TOKEN` | GitHub Secrets — token de **https://pypi.org** (2FA na conta) |

Tokens são **diferentes**; o de TestPyPI não funciona em produção.

---

## Publicar (automático)

```bash
# 1. main com REVISION + CHANGELOG atualizados
git checkout main
git pull origin main

# 2. Branch de release (nome = versão em REVISION)
git checkout -b release/0.1.2
git push -u origin release/0.1.2
```

Workflow: [publish-testpypi.yml](../.github/workflows/publish-testpypi.yml) (*Publish release (TestPyPI → PyPI)*)

| Job | O que faz |
|-----|-----------|
| `validate` | `release/X.Y.Z` = `REVISION`, ruff, pytest |
| `build` | `python -m build` → artifact `dist/` |
| `publish-testpypi` | Upload TestPyPI (`TEST_PYPI_API_TOKEN`) |
| `publish-pypi` | Upload PyPI (`PYPI_API_TOKEN`) — só se TestPyPI OK |

**Re-run:** Actions → *Publish release (TestPyPI → PyPI)* → *Run workflow*.

Depois do CI, faça merge da branch no `main`:

```bash
git checkout main
git merge release/0.1.2
git push origin main
```

---

## Validar instalação

**TestPyPI:**

```bash
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  clicksign-python-sdk==0.1.2
```

**PyPI produção:**

```bash
pip install clicksign-python-sdk==0.1.2
python -c "import clicksign; print(clicksign.__version__)"
```

---

## Manual (`twine`) — fallback

```bash
python -m build

# TestPyPI
TWINE_USERNAME=__token__ TWINE_PASSWORD='pypi-TEST...' \
  twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# PyPI (após validar no TestPyPI)
TWINE_USERNAME=__token__ TWINE_PASSWORD='pypi-PROD...' \
  twine upload dist/*
```

---

## Tag Git (opcional)

```bash
git tag 0.1.2
git push origin 0.1.2
```

Tags não disparam o workflow.
