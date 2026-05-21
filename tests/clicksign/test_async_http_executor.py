from unittest.mock import AsyncMock, patch

import pytest

from clicksign._async.http_executor import execute_async_http_request
from clicksign.errors import ValidationError
from clicksign.instrumentation import Instrumentation
from clicksign.request_instrumentation import RequestInstrumentation
from tests.support.fake_async_http_client import FakeAsyncHTTPClient
from tests.support.fake_http_client import http_error, http_response


class _Publisher(RequestInstrumentation):
    pass


@pytest.mark.asyncio
async def test_execute_async_success():
    fake = FakeAsyncHTTPClient(http_response(200, {"ok": True}))
    result = await execute_async_http_request(
        http_client=fake,
        method="GET",
        url="http://test/api/v3/envelopes",
        path="/envelopes",
        headers={},
        body=None,
        open_timeout=1.0,
        read_timeout=2.0,
        write_timeout=3.0,
        max_retries=0,
        instrumentation=Instrumentation(),
        logger=None,
        publish=_Publisher(),
    )
    assert result.data == {"ok": True}


@pytest.mark.asyncio
async def test_execute_async_retries_on_429():
    fake = FakeAsyncHTTPClient(
        http_error(429, ""),
        http_response(200, {"data": []}),
    )
    with patch("clicksign._async.http_executor.asyncio.sleep", new_callable=AsyncMock):
        with patch("clicksign.retry_backoff.delay", return_value=0):
            result = await execute_async_http_request(
                http_client=fake,
                method="GET",
                url="http://test/api/v3/envelopes",
                path="/envelopes",
                headers={},
                body=None,
                open_timeout=1.0,
                read_timeout=2.0,
                write_timeout=3.0,
                max_retries=1,
                instrumentation=Instrumentation(),
                logger=None,
                publish=_Publisher(),
            )
    assert result.data == {"data": []}
    assert len(fake.calls) == 2


@pytest.mark.asyncio
async def test_execute_async_does_not_retry_on_422():
    fake = FakeAsyncHTTPClient(http_error(422, {"errors": [{"detail": "bad"}]}))
    with pytest.raises(ValidationError):
        await execute_async_http_request(
            http_client=fake,
            method="POST",
            url="http://test/api/v3/envelopes",
            path="/envelopes",
            headers={},
            body=b"{}",
            open_timeout=1.0,
            read_timeout=2.0,
            write_timeout=3.0,
            max_retries=2,
            instrumentation=Instrumentation(),
            logger=None,
            publish=_Publisher(),
        )
    assert len(fake.calls) == 1


@pytest.mark.asyncio
async def test_execute_async_retries_on_timeout():
    fake = FakeAsyncHTTPClient(
        TimeoutError("timed out"),
        http_response(200, {"data": []}),
    )
    with patch("clicksign._async.http_executor.asyncio.sleep", new_callable=AsyncMock):
        with patch("clicksign.retry_backoff.delay", return_value=0):
            await execute_async_http_request(
                http_client=fake,
                method="GET",
                url="http://test/api/v3/envelopes",
                path="/envelopes",
                headers={},
                body=None,
                open_timeout=1.0,
                read_timeout=2.0,
                write_timeout=3.0,
                max_retries=1,
                instrumentation=Instrumentation(),
                logger=None,
                publish=_Publisher(),
            )
    assert len(fake.calls) == 2
