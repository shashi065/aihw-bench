"""Logging setup with secret redaction."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable

SENSITIVE_PATTERNS = (re.compile(r"(?i)(token|password|secret|api[_-]?key)=([^,\s]+)"),)


def redact_secrets(message: str) -> str:
    """Redact common secret assignments from a log message."""
    redacted = message
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}=<redacted>", redacted)
    return redacted


class SecretRedactionFilter(logging.Filter):
    """Filter that redacts common secret values from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_secrets(str(record.getMessage()))
        record.args = ()
        return True


def configure_logging(
    *,
    level: int = logging.INFO,
    logger_name: str = "aihw_bench",
    extra_filters: Iterable[logging.Filter] = (),
) -> logging.Logger:
    """Configure and return the AIHW-Bench logger."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)

    for configured_handler in list(logger.handlers):
        configured_handler.addFilter(SecretRedactionFilter())
        for log_filter in extra_filters:
            configured_handler.addFilter(log_filter)

    return logger
