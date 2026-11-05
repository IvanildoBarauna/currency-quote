# src/currency_quote/application/ports/outbound/currency_repository.py
from abc import ABC, abstractmethod
from typing import List
from currency_quote.domain.entities.currency import CurrencyQuote, CurrencyObject


class ICurrencyRepository(ABC):
    """Port for currency quote data sources (AwesomeAPI adapter implements it)."""

    @abstractmethod
    def __init__(self, currency_obj: CurrencyObject):
        pass

    @abstractmethod
    def get_last_quote(self) -> List[CurrencyQuote]:
        pass

    @abstractmethod
    def get_history_quote(self, reference_date: int) -> List[CurrencyQuote]:
        pass

    @abstractmethod
    def get_history_range(self, start_date: int, end_date: int) -> List[CurrencyQuote]:
        pass
