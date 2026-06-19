"""
Structured logging configuration for Speakly.
Uses Python's built-in logging with JSON-like formatting for production.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure structured logging for the application.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured root logger for the 'speakly' namespace.
    """
    logger = logging.getLogger("speakly")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers on reload
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Module-level logger instance
logger = setup_logging()
