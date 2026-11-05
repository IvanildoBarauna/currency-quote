# src/currency_quote/client.py
"""High-level client: typed results, flexible dates and optional validation."""
from typing import List, Optional, Sequence, Union

from currency_quote.application.use_cases.get_history_currency_quote import (
    GetHistCurrencyQuoteRangeUseCase,
    GetHistCurrencyQuoteUseCase,
)
from currency_quote.application.use_cases.get_last_currency_quote import (
    GetLastCurrencyQuoteUseCase,
)
from currency_quote.config.endpoints import API
from currency_quote.domain.entities.currency import CurrencyObject, QuoteList
from currency_quote.exceptions import InvalidDateError
from currency_quote.utils.dates import parse_reference_date
from currency_quote.utils.http import HTTPConfig

CurrencyInput = Union[str, Sequence[str]]


def normalize_currencies(inputs: Sequence[Union[str, Sequence[str]]]) -> List[str]:
    """Flatten ``*args`` into a plain list of currency pairs."""
    currencies: List[str] = []
    for entry in inputs:
        if isinstance(entry, (list, tuple)):
            currencies.extend(normalize_currencies(entry))
        else:
            currencies.append(entry)  # format errors are raised by CurrencyObject
    return currencies


class CurrencyQuoteClient:
    """Fetch currency quotes with typed, normalized results.

    Args:
        validate: check pairs against the parities list before requesting quotes.
            Disable it to save one HTTP round-trip per call.
        timeout_seconds: per-request timeout override.
        retry_attempts: retry attempts override (exponential backoff).
    """

    def __init__(
        self,
        validate: bool = True,
        timeout_seconds: Optional[float] = None,
        retry_attempts: Optional[int] = None,
    ):
        self.validate = validate
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else API.HTTP_TIMEOUT_SECONDS
        )
        self.retry_attempts = (
            retry_attempts if retry_attempts is not None else API.HTTP_RETRY_ATTEMPTS
        )

    def _http_config(self) -> HTTPConfig:
        return HTTPConfig(
            timeout_seconds=self.timeout_seconds, retry_attempts=self.retry_attempts
        )

    def get_last(self, *currencies: CurrencyInput) -> QuoteList:
        """Fetch the latest quotes. Accepts a pair ('USD-BRL'), varargs or a list."""
        currency_obj = CurrencyObject(normalize_currencies(currencies))
        quotes = GetLastCurrencyQuoteUseCase.execute(
            currency_obj, validate=self.validate, http_config=self._http_config()
        )
        return QuoteList(quotes)

    def get_history(
        self,
        *currencies: CurrencyInput,
        reference_date: Optional[Union[int, str]] = None,
        start_date: Optional[Union[int, str]] = None,
        end_date: Optional[Union[int, str]] = None,
    ) -> QuoteList:
        """Fetch historical quotes for a single day or a date range.

        Accepts ``reference_date`` (single day) or ``start_date``/``end_date``
        (range, ``end_date`` defaults to ``start_date``). Dates may be
        ``20220101``, ``'2022-01-01'``, ``date``/``datetime`` instances.
        """
        currency_obj = CurrencyObject(normalize_currencies(currencies))

        if reference_date is not None:
            if start_date is not None or end_date is not None:
                raise InvalidDateError(
                    "Use either reference_date or start_date/end_date, not both."
                )
            parsed_date = parse_reference_date(reference_date)
            quotes = GetHistCurrencyQuoteUseCase.execute(
                currency_obj,
                parsed_date,
                validate=self.validate,
                http_config=self._http_config(),
            )
            return QuoteList(quotes)

        if start_date is None:
            raise InvalidDateError(
                "Provide either reference_date or start_date (optionally with end_date)."
            )

        range_start = parse_reference_date(start_date)
        range_end = (
            parse_reference_date(end_date) if end_date is not None else range_start
        )
        quotes = GetHistCurrencyQuoteRangeUseCase.execute(
            currency_obj,
            range_start,
            range_end,
            validate=self.validate,
            http_config=self._http_config(),
        )
        return QuoteList(quotes)
