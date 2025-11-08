"""
Centralized logging utilities with lightweight trace-id support.
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Optional
from uuid import uuid4


_TRACE_ID_VAR: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_LOGGER_INITIALIZED = False


class TraceIdFilter(logging.Filter):
    """Injects a trace_id attribute into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - thin wrapper
        trace_id = _TRACE_ID_VAR.get()
        if trace_id is None:
            trace_id = uuid4().hex
            _TRACE_ID_VAR.set(trace_id)
        record.trace_id = trace_id
        return True


def _initialize_root_logger() -> None:
    global _LOGGER_INITIALIZED
    if _LOGGER_INITIALIZED:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(trace_id)s | %(name)s | %(message)s"
        )
    )
    handler.addFilter(TraceIdFilter())

    root = logging.getLogger("momento")
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    root.propagate = False

    _LOGGER_INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger scoped under the 'momento' namespace ensuring consistent formatting.
    """
    _initialize_root_logger()
    return logging.getLogger(f"momento.{name}")


def set_trace_id(trace_id: Optional[str]) -> None:
    """
    Manually override the current trace id (useful in request middleware).
    """
    _TRACE_ID_VAR.set(trace_id)
