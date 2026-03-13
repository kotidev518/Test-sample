"""
Centralized logging configuration for the Smart-Learn backend.

Usage:
    from app.core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Something happened")
"""
import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """
    Configure the root logger with a standard formatter that writes to stdout.
    Should be called once at application startup (e.g. in main.py).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    # Avoid duplicate handlers on repeated calls
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    Args:
        name: Typically ``__name__`` of the calling module.
    """
    return logging.getLogger(name)
