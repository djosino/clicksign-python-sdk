import pytest

import clicksign

TEST_BASE_URL = "http://test.clicksign.com/api/v3"
TEST_API_KEY = "test-api-key-aaaaaaaa"


@pytest.fixture(autouse=True)
def reset_clicksign():
    clicksign.configure(
        api_key=TEST_API_KEY,
        base_url=TEST_BASE_URL,
        max_retries=0,
        logger=None,
        http_client=None,
        proxy=None,
        verify_ssl_certs=True,
        enable_telemetry=False,
    )
    clicksign.instrumentation.clear()
    from clicksign.app_info import clear_app_info

    clear_app_info()
    yield
    clicksign.instrumentation.clear()
    clear_app_info()
    # Reset cached clients so next test gets fresh ones
    clicksign._client = None
    clicksign._bulk_client = None
