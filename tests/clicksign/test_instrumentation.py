import logging

from clicksign.instrumentation import Instrumentation


def test_on_request_callback_called():
    inst = Instrumentation()
    events = []
    inst.on_request(lambda e: events.append(e))
    inst.publish("request", {"status": 200})
    assert len(events) == 1
    assert events[0]["status"] == 200


def test_on_retry_callback_called():
    inst = Instrumentation()
    events = []
    inst.on_retry(lambda e: events.append(e))
    inst.publish("retry", {"attempt": 1})
    assert events[0]["attempt"] == 1


def test_on_error_callback_called():
    inst = Instrumentation()
    events = []
    inst.on_error(lambda e: events.append(e))
    inst.publish("error", {"status": 500})
    assert events[0]["status"] == 500


def test_callback_exception_does_not_propagate():
    inst = Instrumentation()
    results = []
    inst.on_request(lambda e: (_ for _ in ()).throw(RuntimeError("boom")))
    inst.on_request(lambda e: results.append("ok"))
    inst.publish("request", {})
    assert results == ["ok"]


def test_remaining_callbacks_run_after_one_raises():
    inst = Instrumentation()
    results = []
    inst.on_request(lambda e: (_ for _ in ()).throw(RuntimeError("first fails")))
    inst.on_request(lambda e: results.append("second ran"))
    inst.publish("request", {})
    assert "second ran" in results


def test_logger_warns_on_callback_error(caplog):
    inst = Instrumentation()
    logger = logging.getLogger("test_inst")
    inst.on_request(lambda e: 1 / 0)
    with caplog.at_level(logging.WARNING, logger="test_inst"):
        inst.publish("request", {}, logger=logger)
    assert any("callback error" in r.message for r in caplog.records)


def test_without_logger_callback_errors_silent():
    inst = Instrumentation()
    inst.on_request(lambda e: 1 / 0)
    inst.publish("request", {}, logger=None)  # should not raise


def test_clear_removes_all_callbacks():
    inst = Instrumentation()
    events = []
    inst.on_request(lambda e: events.append(e))
    inst.on_error(lambda e: events.append(e))
    inst.clear()
    inst.publish("request", {})
    inst.publish("error", {})
    assert events == []
