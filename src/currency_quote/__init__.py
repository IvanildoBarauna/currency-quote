"""Currency quotes from AwesomeAPI without heavy runtime dependencies."""

import logging

from currency_quote.adapters.inbound.lib_controller import ClientBuilder
from currency_quote.client import CurrencyQuoteClient, QuoteList
from currency_quote.domain.entities.currency import CurrencyQuote
from currency_quote.exceptions import (
    CurrencyAPIError,
    CurrencyQuoteError,
    InvalidConfigError,
    InvalidCurrencyError,
    InvalidCurrencyTypeError,
    InvalidDateError,
    NoDataForDateError,
)

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "ClientBuilder",
    "CurrencyQuoteClient",
    "CurrencyQuote",
    "QuoteList",
    "CurrencyQuoteError",
    "InvalidCurrencyError",
    "InvalidConfigError",
    "InvalidCurrencyTypeError",
    "InvalidDateError",
    "NoDataForDateError",
    "CurrencyAPIError",
]
