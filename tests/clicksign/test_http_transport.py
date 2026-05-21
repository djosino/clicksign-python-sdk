from unittest.mock import MagicMock, patch

import pytest

from clicksign._http.transport import (
    HTTPConnectionError,
    UrllibHTTPClient,
)


def test_direct_request_applies_separate_timeouts():
    client = UrllibHTTPClient()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b"{}"
    mock_resp.getheaders.return_value = []

    mock_sock = MagicMock()
    mock_conn = MagicMock()
    mock_conn.sock = mock_sock
    mock_conn.getresponse.return_value = mock_resp

    with patch("http.client.HTTPSConnection", return_value=mock_conn):
        client.request(
            "POST",
            "https://app.clicksign.com/api/v3/envelopes",
            headers={},
            body=b"{}",
            open_timeout=1.5,
            read_timeout=2.5,
            write_timeout=3.5,
        )

    mock_conn.connect.assert_called_once()
    mock_sock.settimeout.assert_any_call(3.5)
    mock_sock.settimeout.assert_any_call(2.5)


def test_direct_request_raises_connection_error_on_failure():
    client = UrllibHTTPClient()
    mock_conn = MagicMock()
    mock_conn.connect.side_effect = TimeoutError("connect timed out")

    with patch("http.client.HTTPSConnection", return_value=mock_conn):
        with pytest.raises(HTTPConnectionError, match="connect timed out"):
            client.request(
                "GET",
                "https://app.clicksign.com/api/v3/envelopes",
                headers={},
                body=None,
                open_timeout=1.0,
                read_timeout=2.0,
                write_timeout=3.0,
            )


def test_direct_request_closes_connection():
    client = UrllibHTTPClient()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b"{}"
    mock_resp.getheaders.return_value = []

    mock_conn = MagicMock()
    mock_conn.getresponse.return_value = mock_resp

    with patch("http.client.HTTPConnection", return_value=mock_conn):
        client.request(
            "GET",
            "http://test.clicksign.com/api/v3/envelopes",
            headers={},
            body=None,
            open_timeout=1.0,
            read_timeout=2.0,
            write_timeout=3.0,
        )

    mock_conn.close.assert_called_once()


def test_verify_ssl_false_uses_unverified_context():
    client = UrllibHTTPClient(verify_ssl_certs=False)

    with patch("http.client.HTTPSConnection") as https_cls:
        with patch("ssl._create_unverified_context", return_value="ctx") as unverified:
            mock_conn = MagicMock()
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = b"{}"
            mock_resp.getheaders.return_value = []
            mock_conn.getresponse.return_value = mock_resp
            https_cls.return_value = mock_conn

            client.request(
                "GET",
                "https://app.clicksign.com/api/v3/envelopes",
                headers={},
                body=None,
                open_timeout=1.0,
                read_timeout=2.0,
                write_timeout=3.0,
            )

    unverified.assert_called_once()
    https_cls.assert_called_with(
        "app.clicksign.com",
        443,
        timeout=1.0,
        context="ctx",
    )
