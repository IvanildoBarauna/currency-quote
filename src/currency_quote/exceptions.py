# src/currency_quote/exceptions.py
"""Exceptions raised by the currency_quote library.

Every exception inherits from ``CurrencyQuoteError`` so callers can catch a
single base class. Compatibility exceptions also extend the built-in error
they replaced (``TypeError``/``ValueError``) so existing ``except`` blocks
keep working.
"""
from typing import Optional


class CurrencyQuoteError(Exception):
    """Base class for all errors raised by currency_quote."""


class InvalidCurrencyPairError(CurrencyQuoteError, TypeError):
    """Currency pair input has the wrong type.

    Also subclasses ``TypeError`` for backwards compatibility with v5.
    """


class CurrencyPairValidationError(CurrencyQuoteError, ValueError):
    """Currency pair has an invalid format or was rejected by validation.

    Also subclasses ``ValueError`` for backwards compatibility with v5.
    """


class InvalidDateError(CurrencyQuoteError, ValueError):
    """Reference date is malformed, in the future, or out of range.

    Also subclasses ``ValueError`` for backwards compatibility with v5.
    """


class NoDataForDateError(CurrencyQuoteError):
    """The API returned no quotes for the requested date(s).

    Typically means the market was closed (weekend/holiday) for the pair.
    """


class CurrencyAPIError(CurrencyQuoteError):
    """The AwesomeAPI returned an unexpected response or is unreachable."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
