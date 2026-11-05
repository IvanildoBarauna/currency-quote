"""Port implemented by a quote provider."""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Sequence

from currency_quote.domain.entities.currency import CurrencyQuote


class ICurrencyRepository(ABC):
    @abstractmethod
    def get_last_quote(self, pairs: Sequence[str]) -> List[CurrencyQuote]:
        """Fetch one current quote per requested pair."""

    @abstractmethod
    def get_history(self, pair: str, start: date, end: date) -> List[CurrencyQuote]:
        """Fetch all available quotes within an inclusive calendar interval."""
