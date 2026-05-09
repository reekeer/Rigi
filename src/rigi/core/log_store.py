"""Global log interception store — captures Python logging + loguru records."""

from __future__ import annotations

import logging
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class CapturedRecord:
    timestamp: datetime
    logger_name: str
    level: str
    message: str
    source: str = "logging"  # "logging" | "loguru"


_records: deque[CapturedRecord] = deque(maxlen=10_000)
_logger_names: set[str] = {"root"}
_lock = threading.Lock()
_loguru_installed: bool = False


def get_records(
    logger_filter: str | None = None,
    level_filter: str | None = None,
) -> list[CapturedRecord]:
    """Return a snapshot of records, optionally filtered."""
    with _lock:
        items = list(_records)
    if logger_filter and logger_filter != "all":
        items = [r for r in items if r.logger_name == logger_filter]
    if level_filter and level_filter != "all":
        items = [r for r in items if r.level == level_filter.upper()]
    return items


def known_loggers() -> list[str]:
    """Return sorted unique logger names seen so far."""
    with _lock:
        return sorted(_logger_names)


def clear() -> None:
    with _lock:
        _records.clear()


# ── Python standard logging handler ──────────────────────────────────────────


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            rec = CapturedRecord(
                timestamp=datetime.fromtimestamp(record.created),
                logger_name=record.name,
                level=record.levelname,
                message=msg,
            )
            with _lock:
                _records.append(rec)
                _logger_names.add(record.name)
        except Exception:
            pass


_intercept_handler = _InterceptHandler()
_intercept_handler.setFormatter(logging.Formatter("%(message)s"))
_intercept_handler.setLevel(logging.DEBUG)

_installed_logging = False


def install() -> None:
    """Attach interceptors to both standard logging and loguru (if present)."""
    global _installed_logging, _loguru_installed

    if not _installed_logging:
        root = logging.getLogger()
        root.addHandler(_intercept_handler)
        _installed_logging = True

    if not _loguru_installed:
        try:
            from loguru import logger as _loguru  # type: ignore[import-untyped]

            def _loguru_sink(msg: Any) -> None:
                record = msg.record
                rec = CapturedRecord(
                    timestamp=record["time"].replace(tzinfo=None),
                    logger_name=record["name"] or "loguru",
                    level=record["level"].name,
                    message=record["message"],
                    source="loguru",
                )
                with _lock:
                    _records.append(rec)
                    _logger_names.add(rec.logger_name)

            _loguru.add(_loguru_sink, format="{message}", level="DEBUG")
            _loguru_installed = True
        except ImportError:
            pass
