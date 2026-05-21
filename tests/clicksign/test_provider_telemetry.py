import clicksign
from clicksign.client import Client
from clicksign.instrumentation import Instrumentation
from clicksign.provider_telemetry import (
    ProviderTelemetry,
    default_telemetry_url,
    normalize_telemetry_path,
)
from tests.support.fake_http_client import FakeHTTPClient, http_response

BASE = "http://test.clicksign.com/api/v3"
UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_default_telemetry_url_from_api_base():
    assert default_telemetry_url(BASE) == "http://test.clicksign.com/sdk/telemetry/v1/events"


def test_normalize_telemetry_path_masks_ids():
    path = f"/envelopes/{UUID}/documents/{UUID}"
    assert normalize_telemetry_path(path) == "/envelopes/{id}/documents/{id}"


def test_telemetry_disabled_by_default():
    captured: list[dict[str, object]] = []

    def send_fn(_url: str, payload: dict[str, object]) -> None:
        captured.append(payload)

    client = Client(
        api_key="key",
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=FakeHTTPClient(http_response(200, {"data": []})),
        enable_telemetry=False,
        provider_telemetry=ProviderTelemetry(
            enabled=False,
            telemetry_url=default_telemetry_url(BASE),
            send_fn=send_fn,
        ),
    )
    client.get("/envelopes")
    client._provider_telemetry.flush()
    assert captured == []


def test_telemetry_records_request_metadata_without_secrets():
    captured: list[tuple[str, dict[str, object]]] = []

    def send_fn(url: str, payload: dict[str, object]) -> None:
        captured.append((url, payload))

    telemetry = ProviderTelemetry(
        enabled=True,
        telemetry_url=default_telemetry_url(BASE),
        send_fn=send_fn,
    )
    client = Client(
        api_key="super-secret-key",
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=FakeHTTPClient(http_response(200, {"data": []})),
        provider_telemetry=telemetry,
    )
    client.get(f"/envelopes/{UUID}")
    telemetry.flush()

    assert len(captured) == 1
    url, payload = captured[0]
    assert url == "http://test.clicksign.com/sdk/telemetry/v1/events"
    assert payload["method"] == "get"
    assert payload["path"] == "/envelopes/{id}"
    assert payload["status"] == 200
    assert "super-secret" not in str(payload)
    assert "Authorization" not in payload


def test_configure_enable_telemetry_opt_in():
    clicksign.configure(enable_telemetry=True)
    assert clicksign.get_enable_telemetry() is True
    clicksign.set_enable_telemetry(False)
    assert clicksign.get_enable_telemetry() is False


def test_telemetry_on_http_error_status():
    captured: list[dict[str, object]] = []

    def send_fn(_url: str, payload: dict[str, object]) -> None:
        captured.append(payload)

    telemetry = ProviderTelemetry(
        enabled=True,
        telemetry_url=default_telemetry_url(BASE),
        send_fn=send_fn,
    )
    client = Client(
        api_key="key",
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=FakeHTTPClient(
            http_response(404, {"errors": [{"detail": "missing"}]})
        ),
        provider_telemetry=telemetry,
    )
    try:
        client.get("/missing")
    except Exception:
        pass
    telemetry.flush()
    assert captured[0]["status"] == 404
