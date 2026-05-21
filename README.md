# Clicksign Python SDK

Python client for the [Clicksign API v3](https://developers.clicksign.com/) (JSON:API).

**Status:** work in progress — see `docs/SDK_CONTRACT.md` for the full specification.

**Reference implementation:** [`../clicksign-ruby-sdk`](../clicksign-ruby-sdk)

---

## Documentation

- [`docs/SDK_CONTRACT.md`](docs/SDK_CONTRACT.md) — complete behavioral specification (start here)
- [`docs/SDK_TEST_MATRIX.md`](docs/SDK_TEST_MATRIX.md) — required test coverage
- [`docs/SPEC.md`](docs/SPEC.md) — API routes and resource map
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) — end-to-end signing workflow
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — architecture diagrams
- [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md) — instrumentation hooks
- [`docs/cookbook/`](docs/cookbook/) — recipes by scenario

---

## Requirements

- Python >= 3.10
- No runtime dependencies (stdlib only)

---

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src/
```
