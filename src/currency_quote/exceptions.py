"""Public exception hierarchy for the currency_quote package.

Every error raised by this library derives from :class:`CurrencyQuoteError`,
so callers can protect an entire integration with a single ``except`` clause::

    from currency_quote import CurrencyQuoteError

    try:
        client.get_last_quote()
    except CurrencyQuoteError as exc:
        ...
"""

from typing import Iterable, Optional


class CurrencyQuoteError(Exception):
    """Base class for every error raised by currency_quote."""


class InvalidCurrencyFormatError(CurrencyQuoteError, ValueError):
    """Raised when a currency pair does not follow the ``BASE-QUOTE`` format."""


class InvalidCurrencyTypeError(CurrencyQuoteError, TypeError):
    """Raised when the currency argument is neither a string nor a sequence."""


class CurrencyNotFoundError(CurrencyQuoteError, ValueError):
    """Raised when none of the requested currency pairs exist in the data source."""

    def __init__(
        self,
        requested: Iterable[str],
        message: Optional[str] = None,
    ) -> None:
        self.requested = list(requested)
        super().__init__(
            message
            or f"None of the requested currency pairs are available: {self.requested}"
        )


class InvalidDateError(CurrencyQuoteError, ValueError):
    """Raised when a reference date is malformed, in the future, or out of range."""


class QuoteFetchError(CurrencyQuoteError, RuntimeError):
    """Raised when the upstream data source fails or returns an unusable payload."""

    def __init__(self, message: str, currency_pair: Optional[str] = None) -> None:
        self.currency_pair = currency_pair
        super().__init__(message)
