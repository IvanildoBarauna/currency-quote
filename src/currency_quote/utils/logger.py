import logging

_PACKAGE_LOGGER_NAME = "currency_quote"


def get_package_logger() -> logging.Logger:
    """Package root logger. Handlers are intentionally NOT configured here.

    Libraries should not configure logging; configure your app's logging and
    set at least WARNING level to see warnings (e.g. invalid currency pairs).
    """
    return logging.getLogger(_PACKAGE_LOGGER_NAME)


def setup_logging(level=logging.INFO):
    """Optional helper for standalone scripts (not called automatically).

    Args:
        level: The logging level. Default is INFO.
    """
    logger = logging.getLogger(_PACKAGE_LOGGER_NAME)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if not logger.handlers or not any(
        not isinstance(handler, logging.NullHandler) for handler in logger.handlers
    ):
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Get a named logger
def get_logger(name):
    """Get a child logger under the ``currency_quote`` namespace."""
    return logging.getLogger(f"{_PACKAGE_LOGGER_NAME}.{name}")
