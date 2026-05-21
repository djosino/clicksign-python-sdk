"""
Smoke script para o clicksign-python-sdk.

Exercita a API pública sem rede real — usa FakeHTTPClient injetado.
Execute a partir da raiz do repo:

    PYTHONPATH=src python3 .claude/skills/run-clicksign-python-sdk/smoke.py
"""

from __future__ import annotations

import json
import sys
import traceback

# ---------------------------------------------------------------------------
# Bootstrap: adiciona tests/support ao path para FakeHTTPClient
# ---------------------------------------------------------------------------
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
# src must come before tests — tests/clicksign/ would shadow src/clicksign/ otherwise
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "src"))

from support.fake_http_client import FakeHTTPClient, connection_error, http_error, http_response

import clicksign
from clicksign import (
    ApiError,
    AuthenticationError,
    ClicksignClient,
    NotFoundError,
    RateLimitError,
    RequestOptions,
    ServerError,
)
from clicksign.resources.notarial.envelope import Envelope
from clicksign.resources.notarial.signer import Signer

PASS = "\033[32mOK\033[0m"
FAIL = "\033[31mFAIL\033[0m"

results: list[tuple[str, bool, str]] = []


def check(name: str, fn):
    try:
        fn()
        results.append((name, True, ""))
        print(f"  {PASS}  {name}")
    except Exception as exc:
        results.append((name, False, traceback.format_exc()))
        print(f"  {FAIL}  {name}: {exc}")


# ---------------------------------------------------------------------------
# Helper: JSON:API envelope response
# ---------------------------------------------------------------------------
def envelope_body(env_id: str = "aaa-111", status: str = "draft") -> dict:
    return {
        "data": {
            "id": env_id,
            "type": "envelopes",
            "attributes": {"status": status, "name": "Smoke Envelope"},
            "relationships": {},
        }
    }


def signer_body(sig_id: str = "bbb-222") -> dict:
    return {
        "data": {
            "id": sig_id,
            "type": "signers",
            "attributes": {"name": "Smoke Signer", "email": "smoke@example.com"},
            "relationships": {},
        }
    }


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------
print("\n=== clicksign-python-sdk smoke ===\n")

# 1. Importação e versão
check("versão importada corretamente", lambda: (
    None if clicksign.__version__ else (_ for _ in ()).throw(AssertionError("sem versão"))
))

# 2. configure() — estado global
def _global_configure():
    clicksign.configure(api_key="smoke-key", environment="sandbox")
    assert clicksign._config.api_key == "smoke-key"
    assert clicksign._config.environment == "sandbox"

check("configure() define estado global", _global_configure)

# 3. ClicksignClient — cliente explícito
def _explicit_client():
    client = ClicksignClient(api_key="explicit-key", environment="sandbox")
    assert client is not None

check("ClicksignClient instanciado sem erro", _explicit_client)

# 4. Envelope.list() via FakeHTTPClient
def _envelope_list():
    fake = FakeHTTPClient(
        http_response(200, {"data": [], "meta": {}, "links": {}})
    )
    clicksign.configure(api_key="smoke-key", environment="sandbox", http_client=fake)
    envelopes = Envelope.list()
    assert envelopes == []
    assert fake.calls[0]["method"] == "GET"
    assert "/envelopes" in fake.calls[0]["url"]

check("Envelope.list() emite GET /envelopes", _envelope_list)

# 5. Envelope.create() via FakeHTTPClient
def _envelope_create():
    fake = FakeHTTPClient(http_response(201, envelope_body()))
    clicksign.configure(api_key="smoke-key", environment="sandbox", http_client=fake)
    env = Envelope.create(name="Smoke Envelope")
    assert env.id == "aaa-111"
    assert env.status == "draft"
    assert fake.calls[0]["method"] == "POST"

check("Envelope.create() retorna Envelope com id e status", _envelope_create)

# 6. Envelope.retrieve()
def _envelope_retrieve():
    fake = FakeHTTPClient(http_response(200, envelope_body("ccc-333", "running")))
    clicksign.configure(api_key="smoke-key", environment="sandbox", http_client=fake)
    env = Envelope.retrieve("ccc-333")
    assert env.id == "ccc-333"
    assert env.status == "running"

check("Envelope.retrieve() retorna Envelope correto", _envelope_retrieve)

# 7. NotFoundError em retrieve()
def _not_found():
    fake = FakeHTTPClient(
        http_error(404, {"errors": [{"detail": "not found"}]})
    )
    clicksign.configure(api_key="smoke-key", environment="sandbox", http_client=fake)
    try:
        Envelope.retrieve("nonexistent")
        raise AssertionError("deveria ter levantado NotFoundError")
    except NotFoundError as e:
        assert e.status_code == 404

check("NotFoundError levantado em 404", _not_found)

# 8. AuthenticationError em 401
def _auth_error():
    fake = FakeHTTPClient(
        http_error(401, {"errors": [{"detail": "unauthorized"}]})
    )
    clicksign.configure(api_key="smoke-key", environment="sandbox", http_client=fake)
    try:
        Envelope.list()
        raise AssertionError("deveria ter levantado AuthenticationError")
    except AuthenticationError as e:
        assert e.status_code == 401

check("AuthenticationError levantado em 401", _auth_error)

# 9. ServerError em 500
# max_retries=0: ServerError é retryable, sem isso o FakeHTTPClient esgota a queue
def _server_error():
    fake = FakeHTTPClient(
        http_error(500, {"errors": [{"detail": "internal error"}]})
    )
    clicksign.configure(api_key="smoke-key", environment="sandbox", http_client=fake, max_retries=0)
    try:
        Envelope.list()
        raise AssertionError("deveria ter levantado ServerError")
    except ServerError as e:
        assert e.status_code == 500

check("ServerError levantado em 500", _server_error)

# 10. RateLimitError em 429
# max_retries=0: RateLimitError também é retryable
def _rate_limit():
    fake = FakeHTTPClient(
        http_error(429, {"errors": [{"detail": "rate limit"}]}, {"X-RateLimit-Remaining": "0"})
    )
    clicksign.configure(api_key="smoke-key", environment="sandbox", http_client=fake, max_retries=0)
    try:
        Envelope.list()
        raise AssertionError("deveria ter levantado RateLimitError")
    except RateLimitError as e:
        assert e.status_code == 429
        assert e.rate_limit_remaining == "0"  # header é string

check("RateLimitError levantado em 429 com rate_limit_remaining", _rate_limit)

# 11. Instrumentação — on_request callback
def _instrumentation():
    events: list[dict] = []
    clicksign.on_request(lambda e: events.append(e))
    fake = FakeHTTPClient(http_response(200, {"data": [], "meta": {}, "links": {}}))
    clicksign.configure(api_key="smoke-key", environment="sandbox", http_client=fake)
    Envelope.list()
    assert len(events) >= 1
    assert "method" in events[0]
    assert "duration_ms" in events[0]
    # limpa callback
    clicksign.instrumentation.clear()

check("on_request callback disparado com method e duration_ms", _instrumentation)

# 12. RequestOptions por chamada
def _request_options():
    fake = FakeHTTPClient(http_response(200, {"data": [], "meta": {}, "links": {}}))
    clicksign.configure(api_key="smoke-key", environment="sandbox", http_client=fake)
    Envelope.list(options=RequestOptions(api_key="override-key"))
    auth = fake.calls[0]["headers"].get("Authorization", "")
    assert auth == "override-key", f"esperado 'override-key', obtido '{auth}'"

check("RequestOptions por chamada sobrescreve api_key no header", _request_options)

# 13. ClicksignClient — namespace notarial
def _client_namespace():
    fake = FakeHTTPClient(http_response(200, {"data": [], "meta": {}, "links": {}}))
    client = ClicksignClient(api_key="client-key", environment="sandbox", http_client=fake)
    envelopes = client.notarial.envelopes.list()
    assert envelopes == []
    assert "/envelopes" in fake.calls[0]["url"]

check("ClicksignClient.notarial.envelopes.list() emite GET correto", _client_namespace)

# 14. ApiError.detail acessível em erros estruturados
def _api_error_detail():
    fake = FakeHTTPClient(
        http_error(422, {"errors": [{"detail": "campo obrigatório", "title": "Validation"}]})
    )
    clicksign.configure(api_key="smoke-key", environment="sandbox", http_client=fake)
    try:
        Envelope.create(name="x")
        raise AssertionError("deveria ter levantado erro")
    except clicksign.ClicksignError as e:
        assert len(e.errors) >= 1
        assert e.api_errors[0].detail == "campo obrigatório"

check("ApiError.detail acessível em erros 422 estruturados", _api_error_detail)

# 15. Webhook — compute_signature e verify_signature
def _webhook_sig():
    import hmac
    import hashlib
    secret = "webhook-secret"
    payload = b'{"event":"envelope.signed"}'
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    # deve não levantar
    clicksign.verify_signature(payload, sig, secret)

check("verify_signature valida HMAC SHA-256 corretamente", _webhook_sig)

# ---------------------------------------------------------------------------
# Resultado final
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)

print(f"\n{'='*40}")
print(f"Resultado: {passed} OK, {failed} FAIL\n")

if failed:
    for name, ok, tb in results:
        if not ok:
            print(f"--- {name} ---")
            print(tb)
    sys.exit(1)
