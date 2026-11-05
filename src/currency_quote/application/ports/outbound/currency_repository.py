# src/currency_quote/application/ports/outbound/currency_repository.py
from abc import ABC, abstractmethod
from typing import Optional

from currency_quote.config.settings import DEFAULT_REQUEST_CONFIG, RequestConfig
from currency_quote.domain.entities.currency import CurrencyObject, QuoteList
from currency_quote.utils.dates import DateInput


class ICurrencyRepository(ABC):
    """Outbound port for any source of currency quotes."""

    @abstractmethod
    def __init__(
        self,
        currency_obj: CurrencyObject,
        config: RequestConfig = DEFAULT_REQUEST_CONFIG,
    ):
        pass

    @abstractmethod
    def get_last_quote(self) -> QuoteList:
        """Return the most recent quote for each currency pair."""

    @abstractmethod
    def get_history_quote(self, reference_date: DateInput) -> QuoteList:
        """Return the daily closing quote for a single past date."""

    @abstractmethod
    def get_history_quote_range(
        self,
        start_date: DateInput,
        end_date: Optional[DateInput] = None,
    ) -> QuoteList:
        """Return daily closing quotes for an inclusive date range."""
