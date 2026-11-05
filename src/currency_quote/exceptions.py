"""Public errors: callers can catch CurrencyQuoteError for every library error."""


class CurrencyQuoteError(Exception):
    """Base class for library failures."""


class InvalidCurrencyError(CurrencyQuoteError, ValueError):
    """Malformed, unsupported or unavailable currency pair."""


class InvalidCurrencyTypeError(CurrencyQuoteError, TypeError):
    """Currency input has the wrong type."""


class InvalidDateError(CurrencyQuoteError, ValueError):
    """Invalid or unclosed historical date."""


class InvalidConfigError(CurrencyQuoteError, ValueError):
    """Invalid timeout, retry or cache configuration."""


class NoDataForDateError(CurrencyQuoteError, LookupError):
    """No quote for a pair on the requested day or in the requested interval."""


class CurrencyAPIError(CurrencyQuoteError):
    """HTTP or malformed provider response."""

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code
