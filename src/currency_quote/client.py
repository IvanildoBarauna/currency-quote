"""Public typed client and composition root for provider-independent use cases."""

from datetime import date
from typing import List, Union

import requests

from currency_quote.adapters.outbound.currency_api import CurrencyAPI
from currency_quote.adapters.outbound.currency_validator_api import CurrencyValidatorAPI
from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.application.ports.outbound.currency_validator_repository import (
    ICurrencyValidator,
)
from currency_quote.application.use_cases.get_history_currency_quote import (
    get_history_quotes,
)
from currency_quote.application.use_cases.get_last_currency_quote import get_last_quotes
from currency_quote.domain.entities.currency import CurrencyObject, CurrencyQuote
from currency_quote.utils.dates import DateInput, parse_date
from currency_quote.utils.http import HTTPClient, HTTPConfig


class QuoteList(List[CurrencyQuote]):
    """Typed results with explicit, JSON-ready export methods."""

    def to_dict(self) -> List[dict]:
        return [quote.to_dict() for quote in self]

    def to_dataframe(self):
        """Load pandas only when exporting (install currency-quote[pandas])."""
        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel
        except ImportError as exc:
            raise ImportError(
                "Install currency-quote[pandas] for DataFrame export"
            ) from exc
        return pd.DataFrame(self.to_dict())


class CurrencyQuoteClient:
    """Get exact-decimal quotes; optionally inject provider and validator fakes."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        currency_list: Union[List[str], str],
        *,
        validate: bool = True,
        timeout: float = 10,
        retries: int = 2,
        cache_ttl: float = 3600,
        repository: ICurrencyRepository = None,
        validator: ICurrencyValidator = None,
        session: requests.Session = None,
    ):
        self.currency_obj = CurrencyObject(currency_list)
        self.http = HTTPClient(HTTPConfig(timeout, retries), session=session)
        self.repository = (
            repository if repository is not None else CurrencyAPI(self.http)
        )
        self.validator = (
            (
                validator
                if validator is not None
                else CurrencyValidatorAPI(self.http, cache_ttl)
            )
            if validate
            else None
        )

    def get_last_quote(self) -> QuoteList:
        return QuoteList(
            get_last_quotes(
                self.currency_obj.get_currency_list(), self.repository, self.validator
            )
        )

    def get_history_quote(self, reference_date: DateInput) -> QuoteList:
        day = parse_date(reference_date)  # invalid dates never touch the network
        return self._history(day, day)

    def get_history_range(
        self, start_date: DateInput, end_date: DateInput
    ) -> QuoteList:
        start, end = parse_date(start_date), parse_date(end_date)
        return self._history(start, end)

    def _history(self, start: date, end: date) -> QuoteList:
        return QuoteList(
            get_history_quotes(
                self.currency_obj.get_currency_list(),
                start,
                end,
                self.repository,
                self.validator,
            )
        )

    def close(self) -> None:
        """Close the owned HTTP connection pool (not a caller-injected session)."""
        self.http.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
