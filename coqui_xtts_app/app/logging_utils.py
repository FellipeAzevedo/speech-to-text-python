"""Logging helpers for the application."""
from __future__ import annotations

import logging
from typing import Optional

_LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(debug: bool = False, logger: Optional[logging.Logger] = None) -> None:
    """Configure basic logging for the application.

    Args:
        debug: Whether to enable debug logging level.
        logger: Optional logger to configure. When ``None`` configures root logger.
    """

    level = logging.DEBUG if debug else logging.INFO
    target_logger = logger or logging.getLogger()
    if not target_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(_LOGGING_FORMAT)
        handler.setFormatter(formatter)
        target_logger.addHandler(handler)
    target_logger.setLevel(level)

