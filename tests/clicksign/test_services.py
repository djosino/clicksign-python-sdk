import threading

import pytest

import clicksign
from clicksign.services import Services
from tests.support.http_mock import make_response, mock_urlopen

BASE = "http://test.clicksign.com/api/v3"


def test_use_sets_thread_local_client():
    svc = Services(api_key="tenant-key", base_url=BASE)
    with svc.use():
        t = threading.current_thread()
        assert t.__dict__.get("_clicksign_client") is not None
        assert t.__dict__.get("_clicksign_bulk_client") is not None


def test_use_routes_through_service_client():
    svc = Services(api_key="tenant-key", base_url=BASE)
    from clicksign.resources.notarial.envelope import Envelope

    with mock_urlopen(make_response(200, {"data": []})):
        with svc.use():
            Envelope.list()


def test_restores_client_after_block():
    svc = Services(api_key="tenant-key", base_url=BASE)
    with svc.use():
        pass
    t = threading.current_thread()
    assert t.__dict__.get("_clicksign_client") is None
    assert t.__dict__.get("_clicksign_bulk_client") is None


def test_restores_client_on_exception():
    svc = Services(api_key="tenant-key", base_url=BASE)
    try:
        with svc.use():
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    t = threading.current_thread()
    assert t.__dict__.get("_clicksign_client") is None
    assert t.__dict__.get("_clicksign_bulk_client") is None


def test_does_not_use_global_client_inside_block():
    svc = Services(api_key="tenant-key", base_url=BASE)
    with svc.use() as local_client:
        global_client = clicksign._global_client()
        t = threading.current_thread()
        thread_client = t.__dict__.get("_clicksign_client")
        assert thread_client is local_client
        assert thread_client is not global_client


def test_unknown_environment_raises():
    with pytest.raises(ValueError, match="Unknown environment"):
        Services(api_key="key", environment="staging")
