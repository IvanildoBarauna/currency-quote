# src/currency_quote/application/ports/outbound/currency_validator_repository.py
from abc import ABC, abstractmethod
from typing import List

from currency_quote.config.settings import DEFAULT_REQUEST_CONFIG, RequestConfig
from currency_quote.domain.entities.currency import CurrencyObject


class ICurrencyValidator(ABC):
    """Outbound port for checking which currency pairs a source supports."""

    @abstractmethod
    def __init__(
        self,
        currency_quote: CurrencyObject,
        config: RequestConfig = DEFAULT_REQUEST_CONFIG,
    ):
        pass

    @abstractmethod
    def validate_currency_code(self) -> List[str]:
        """Return the subset of requested pairs that the source supports."""
