"""Opt-in package logging; importing the library never configures the app."""

import logging


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"currency_quote.{name}")


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure only the library logger when explicitly requested."""
    logger = logging.getLogger("currency_quote")
    logger.setLevel(level)
    if not any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.NullHandler)
        for handler in logger.handlers
    ):
        logger.addHandler(logging.StreamHandler())
    return logger
