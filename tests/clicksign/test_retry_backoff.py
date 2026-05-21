from unittest.mock import patch

from clicksign.retry_backoff import ceiling, delay, parse_retry_after, retry_delay


def test_ceiling_attempt_1():
    assert ceiling(1) == 0.5


def test_ceiling_attempt_2():
    assert ceiling(2) == 1.0


def test_ceiling_attempt_3():
    assert ceiling(3) == 2.0


def test_ceiling_capped_at_30():
    assert ceiling(10) == 30.0
    assert ceiling(100) == 30.0


def test_delay_within_ceiling():
    for attempt in range(1, 8):
        d = delay(attempt)
        assert 0 <= d < ceiling(attempt)


def test_delay_spread_not_constant():
    vals = {delay(1) for _ in range(20)}
    assert len(vals) > 1


def test_delay_zero_when_ceiling_zero():
    # ceiling is always >= 0.5 for attempt >= 1, but guard still works
    from unittest.mock import patch

    with patch("clicksign.retry_backoff.ceiling", return_value=0.0):
        assert delay(1) == 0.0


def test_parse_retry_after_seconds():
    assert parse_retry_after({"Retry-After": "3"}) == 3.0
    assert parse_retry_after({"retry-after": "1.5"}) == 1.5


def test_parse_retry_after_missing():
    assert parse_retry_after({}) is None
    assert parse_retry_after(None) is None


def test_parse_retry_after_http_date():
    from datetime import datetime, timedelta, timezone

    future = datetime.now(timezone.utc) + timedelta(seconds=10)
    http_date = future.strftime("%a, %d %b %Y %H:%M:%S GMT")
    parsed = parse_retry_after({"Retry-After": http_date})
    assert parsed is not None
    assert 5.0 <= parsed <= 15.0


def test_retry_delay_without_retry_after_uses_jitter():
    with patch("clicksign.retry_backoff.delay", return_value=0.42):
        assert retry_delay(1, {}) == 0.42


def test_retry_delay_prefers_max_of_jitter_and_retry_after():
    with patch("clicksign.retry_backoff.delay", return_value=0.5):
        assert retry_delay(1, {"Retry-After": "2"}) == 2.0
    with patch("clicksign.retry_backoff.delay", return_value=5.0):
        assert retry_delay(1, {"Retry-After": "2"}) == 5.0
