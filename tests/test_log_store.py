"""Tests for log store."""

from datetime import datetime

from rigi.core import log_store


def test_log_store_install():
    """Test that log store can be installed."""
    log_store.install()
    assert log_store._installed_logging is True


def test_log_store_clear():
    """Test clearing log store."""
    log_store.clear()
    records = log_store.get_records()
    assert len(records) == 0


def test_log_store_known_loggers():
    """Test getting known logger names."""
    loggers = log_store.known_loggers()
    assert isinstance(loggers, list)
    assert "root" in loggers


def test_log_store_get_records():
    """Test getting records."""
    records = log_store.get_records()
    assert isinstance(records, list)


def test_log_store_filter_by_logger():
    """Test filtering by logger name."""
    records = log_store.get_records(logger_filter="test")
    assert isinstance(records, list)


def test_log_store_filter_by_level():
    """Test filtering by log level."""
    records = log_store.get_records(level_filter="ERROR")
    assert isinstance(records, list)


def test_captured_record_structure():
    """Test CapturedRecord structure."""
    from rigi.core.log_store import CapturedRecord

    record = CapturedRecord(
        timestamp=datetime.now(), logger_name="test", level="INFO", message="test message"
    )
    assert record.timestamp is not None
    assert record.logger_name == "test"
    assert record.level == "INFO"
    assert record.message == "test message"
    assert record.source == "logging"
