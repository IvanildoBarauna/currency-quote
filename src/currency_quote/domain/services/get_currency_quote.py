# src/currency_quote/domain/services/get_currency_quote.py
from typing import Callable, List
from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.application.use_cases.validate_currency import (
    ValidateCurrencyUseCase,
)
from currency_quote.domain.entities.currency import CurrencyQuote, CurrencyObject


class GetCurrencyQuoteService:
    """Orchestrates online validation + quote fetching.

    ``currency_repository`` receives a factory so it is built with the
    validated pairs only.
    """

    def __init__(
        self,
        currency: CurrencyObject,
        currency_repository: Callable[[CurrencyObject], ICurrencyRepository],
        validate: bool = True,
    ):
        self.currency = currency
        self.currency_repository = currency_repository
        self.validate = validate

    def last(self) -> List[CurrencyQuote]:
        currency_obj = self.prevalidated_currency()
        return self.currency_repository(currency_obj).get_last_quote()

    def history(self, reference_date: int) -> List[CurrencyQuote]:
        currency_obj = self.prevalidated_currency()
        return self.currency_repository(currency_obj).get_history_quote(
            reference_date=reference_date
        )

    def history_range(self, start_date: int, end_date: int) -> List[CurrencyQuote]:
        currency_obj = self.prevalidated_currency()
        return self.currency_repository(currency_obj).get_history_range(
            start_date=start_date, end_date=end_date
        )

    def prevalidated_currency(self) -> CurrencyObject:
        if not self.validate:
            return self.currency
        return ValidateCurrencyUseCase.execute(self.currency)
