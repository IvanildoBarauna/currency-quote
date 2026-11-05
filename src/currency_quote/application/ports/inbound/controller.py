from abc import ABC, abstractmethod
from typing import Optional

from currency_quote.domain.entities.currency import CurrencyInput, QuoteList
from currency_quote.utils.dates import DateInput


class IController(ABC):
    """Inbound port describing the public surface of the library."""

    @abstractmethod
    def __init__(self, currency_list: CurrencyInput):
        pass

    @abstractmethod
    def get_last_quote(self) -> QuoteList:
        """Return the most recent quote for each configured currency pair."""

    @abstractmethod
    def get_history_quote(self, reference_date: DateInput) -> QuoteList:
        """Return the daily closing quote for a single past date."""

    @abstractmethod
    def get_history_range(
        self,
        start_date: DateInput,
        end_date: Optional[DateInput] = None,
    ) -> QuoteList:
        """Return daily closing quotes for an inclusive date range."""
