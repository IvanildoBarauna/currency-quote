# src/currency_quote/application/ports/outbound/currency_validator_repository.py
from abc import ABC, abstractmethod
from currency_quote.domain.entities.currency import CurrencyObject


class ICurrencyValidator(ABC):
    """Port for online currency pair validation."""

    @abstractmethod
    def __init__(self, currency_quote: CurrencyObject):
        pass

    @abstractmethod
    def validate_currency_code(self) -> list:
        """Return the subset of the input pairs supported by the Gateway."""
