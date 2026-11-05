"""Logging helpers.

Libraries must not configure logging on behalf of the application, so the
package logger only gets a :class:`~logging.NullHandler`. Applications that
want to see these logs can either configure logging themselves or call
:func:`setup_logging` explicitly.
"""

import logging

PACKAGE_LOGGER_NAME = "currency_quote"

logging.getLogger(PACKAGE_LOGGER_NAME).addHandler(logging.NullHandler())


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``currency_quote`` namespace."""
    return logging.getLogger(f"{PACKAGE_LOGGER_NAME}.{name}")


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Attach a stream handler to the package logger.

    This is opt-in and intended for scripts, notebooks and the CLI. Importing
    the package no longer configures handlers automatically.

    Args:
        level: The logging level. Defaults to ``logging.INFO``.

    Returns:
        The configured package logger.
    """
    logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    logger.setLevel(level)

    has_stream_handler = any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.NullHandler)
        for handler in logger.handlers
    )

    if not has_stream_handler:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s - %(message)s")
        )
        logger.addHandler(handler)

    return logger
