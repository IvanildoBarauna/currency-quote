# src/tests/test_logger.py
import logging

from currency_quote.utils.logger import get_logger, get_package_logger, setup_logging


def test_get_logger_namespaces_under_package():
    assert get_logger("currency_api").name == "currency_quote.currency_api"


def test_get_package_logger_has_null_handler_by_default():
    logger = get_package_logger()
    assert any(isinstance(handler, logging.NullHandler) for handler in logger.handlers)


def test_setup_logging_adds_stream_handler_once():
    logger = setup_logging(level=logging.WARNING)
    stream_handlers = [
        handler
        for handler in logger.handlers
        if not isinstance(handler, logging.NullHandler)
    ]
    assert len(stream_handlers) == 1
    assert logger.level == logging.WARNING

    # calling again must not duplicate handlers
    setup_logging(level=logging.INFO)
    stream_handlers = [
        handler
        for handler in logger.handlers
        if not isinstance(handler, logging.NullHandler)
    ]
    assert len(stream_handlers) == 1
