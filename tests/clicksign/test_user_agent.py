import platform

import clicksign
from clicksign.app_info import AppInfo, clear_app_info
from clicksign.client import Client
from clicksign.instrumentation import Instrumentation
from clicksign.json_api.bulk_operations_client import BulkOperationsClient
from clicksign.user_agent import build_user_agent
from clicksign.version import __version__
from tests.support.fake_http_client import FakeHTTPClient, http_response

BASE = "http://test.clicksign.com/api/v3"


def make_client(http_client: FakeHTTPClient | None = None, **kwargs: object) -> Client:
    return Client(
        api_key="test-key",
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=http_client or FakeHTTPClient(http_response(200, {"data": []})),
        **kwargs,  # type: ignore[arg-type]
    )


def test_build_user_agent_includes_sdk_and_python():
    ua = build_user_agent()
    assert ua.startswith(f"clicksign-python/{__version__}")
    assert f"Python/{platform.python_version()}" in ua


def test_set_app_info_adds_host_app_to_user_agent():
    clicksign.set_app_info("My CRM", "2.1.0", "https://example.com")
    ua = build_user_agent()
    assert "My_CRM/2.1.0" in ua


def test_client_sends_user_agent_header():
    fake = FakeHTTPClient(http_response(200, {"data": []}))
    make_client(http_client=fake).get("/envelopes")
    assert fake.calls[0]["headers"]["User-Agent"].startswith(f"clicksign-python/{__version__}")


def test_global_set_app_info_applied_to_client_requests():
    fake = FakeHTTPClient(http_response(200, {"data": []}))
    clicksign.set_app_info("AcmeApp", "1.0.0")
    make_client(http_client=fake).get("/envelopes")
    assert "AcmeApp/1.0.0" in fake.calls[0]["headers"]["User-Agent"]


def test_per_client_app_info_override():
    fake = FakeHTTPClient(http_response(200, {"data": []}))
    clicksign.set_app_info("GlobalApp", "9.9.9")
    make_client(
        http_client=fake,
        app_info=AppInfo(name="TenantApp", version="3.0.0"),
    ).get("/envelopes")
    assert "TenantApp/3.0.0" in fake.calls[0]["headers"]["User-Agent"]
    assert "GlobalApp" not in fake.calls[0]["headers"]["User-Agent"]


def test_bulk_client_sends_user_agent_header():
    fake = FakeHTTPClient(http_response(200, {"atomic:results": []}))
    client = BulkOperationsClient(
        api_key="test-key",
        base_url=BASE,
        open_timeout=2.0,
        read_timeout=5.0,
        write_timeout=7.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        http_client=fake,
    )
    client.post("/envelopes/env-id/bulk_requirements", {"atomic:operations": []})
    assert fake.calls[0]["headers"]["User-Agent"].startswith(f"clicksign-python/{__version__}")


def test_get_app_info_after_set():
    clear_app_info()
    clicksign.set_app_info("Plugin", "0.1.0", "https://plugin.example")
    info = clicksign.get_app_info()
    assert info is not None
    assert info.name == "Plugin"
    assert info.version == "0.1.0"
    assert info.url == "https://plugin.example"
