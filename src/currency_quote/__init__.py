"""currency-quote: a typed client for currency pair quotes.

Quick start::

    from currency_quote import CurrencyQuoteClient

    client = CurrencyQuoteClient("USD-BRL")
    for quote in client.get_last_quote():
        print(quote.currency_pair, quote.bid_price)
"""

from currency_quote.adapters.inbound.lib_controller import (
    ClientBuilder,
    CurrencyQuoteClient,
)
from currency_quote.adapters.outbound.currency_validator_api import (
    clear_available_parities_cache,
)
from currency_quote.config.settings import RequestConfig, RetryStrategy
from currency_quote.domain.entities.currency import (
    CurrencyObject,
    CurrencyQuote,
    QuoteList,
)
from currency_quote.exceptions import (
    CurrencyNotFoundError,
    CurrencyQuoteError,
    InvalidCurrencyFormatError,
    InvalidCurrencyTypeError,
    InvalidDateError,
    QuoteFetchError,
)
from currency_quote.utils.logger import setup_logging

try:  # pragma: no cover - depends on install method
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("currency-quote")
except (ImportError, PackageNotFoundError):  # pragma: no cover
    __version__ = "0.0.0"

__all__ = [
    "ClientBuilder",
    "CurrencyQuoteClient",
    "CurrencyObject",
    "CurrencyQuote",
    "QuoteList",
    "RequestConfig",
    "RetryStrategy",
    "CurrencyQuoteError",
    "CurrencyNotFoundError",
    "InvalidCurrencyFormatError",
    "InvalidCurrencyTypeError",
    "InvalidDateError",
    "QuoteFetchError",
    "clear_available_parities_cache",
    "setup_logging",
    "__version__",
]
