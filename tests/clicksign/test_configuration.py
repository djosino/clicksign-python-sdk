import pytest

from clicksign.configuration import Configuration


def test_defaults():
    cfg = Configuration()
    assert cfg.base_url == "https://app.clicksign.com/api/v3"
    assert cfg.open_timeout == 2.0
    assert cfg.read_timeout == 10.0
    assert cfg.write_timeout == 10.0
    assert cfg.max_retries == 3
    assert cfg.api_key is None
    assert cfg.logger is None
    assert cfg.proxy is None
    assert cfg.verify_ssl_certs is True
    assert cfg.http_client is None


def test_environment_sandbox():
    cfg = Configuration()
    cfg.environment = "sandbox"
    assert cfg.base_url == "https://sandbox.clicksign.com/api/v3"


def test_environment_production():
    cfg = Configuration()
    cfg.environment = "production"
    assert cfg.base_url == "https://app.clicksign.com/api/v3"


def test_unknown_environment_raises():
    cfg = Configuration()
    with pytest.raises(ValueError, match="Unknown environment"):
        cfg.environment = "staging"


def test_accepts_logger(caplog):
    import logging

    logger = logging.getLogger("test")
    cfg = Configuration()
    cfg.logger = logger
    assert cfg.logger is logger
