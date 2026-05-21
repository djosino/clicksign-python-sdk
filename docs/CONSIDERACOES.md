# Considerações — Python SDK (uso interno)

> **Não linkar** em README nem em `docs/README.md`. Backlog da equipe; matriz de testes em [`SDK_TEST_MATRIX.md`](SDK_TEST_MATRIX.md).

**Última revisão:** maio/2026 (6ª passagem — refinamento da doc pública).

---

## Snapshot

| | |
|---|---|
| Testes | **517** · cobertura **93%** · CI OK |
| Qualidade | ruff + mypy |
| Doc pública | Refinada (async, paginação, listagens, imports) |
| Crítico | **Nada** |

```bash
pytest -q && pytest --cov=clicksign --cov-fail-under=88 -q
ruff check src tests && ruff format --check src tests && mypy
```

---

## Backlog aberto

| Item | Prioridade |
|------|------------|
| Tag git `v0.1.0` ao publicar PyPI | Release |
| `resource_type_spec.json` vs API | P2 |
| TypedDicts admin restantes (`AccessControlList`, …) | P2 |
| CI: install mínimo sem `[dev]` | P3 |
| Cobertura admin (`webhook` resource ~76%) | P3 |
| Smoke E2E sandbox | Manual |

---

## Comportamento a não esquecer

- `Signer.notify(envelope_id, signer_id, ...)` — classmethod.
- Eventos só aninhados; facade `create` com envelope id posicional.
- `page(n)` + `.to_list()` → auto-pagina desde p.1; use `.first()` para página fixa.

---

## Referência (público)

`SDK_CONTRACT` · `WORKFLOW` · `SPEC` · `PAGINATION` · `TROUBLESHOOTING` · `examples/`
