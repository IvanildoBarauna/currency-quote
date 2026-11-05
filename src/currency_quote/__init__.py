"""currency_quote: fetch currency pair quotes from the AwesomeAPI (economia)."""

import logging
from importlib.metadata import PackageNotFoundError, version

from currency_quote.adapters.inbound.lib_controller import ClientBuilder
from currency_quote.client import CurrencyQuoteClient
from currency_quote.domain.entities.currency import CurrencyQuote, QuoteList
from currency_quote.exceptions import (
    CurrencyAPIError,
    CurrencyPairValidationError,
    CurrencyQuoteError,
    InvalidCurrencyPairError,
    InvalidDateError,
    NoDataForDateError,
)

try:
    __version__ = version("currency-quote")
except PackageNotFoundError:  # pragma: no cover - only when running from source
    __version__ = "unknown"

# Library best practice: don't swallow user logs, but avoid "no handler" errors.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "ClientBuilder",
    "CurrencyQuoteClient",
    "CurrencyQuote",
    "QuoteList",
    "CurrencyQuoteError",
    "CurrencyPairValidationError",
    "InvalidCurrencyPairError",
    "InvalidDateError",
    "NoDataForDateError",
    "CurrencyAPIError",
    "__version__",
]
