# src/currency_quote/application/use_cases/get_last_currency_quote.py
from typing import Optional, Type

from currency_quote.adapters.outbound.currency_api import CurrencyAPI
from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.config.settings import DEFAULT_REQUEST_CONFIG, RequestConfig
from currency_quote.domain.entities.currency import CurrencyObject, QuoteList
from currency_quote.domain.services.get_currency_quote import GetCurrencyQuoteService


class GetLastCurrencyQuoteUseCase:
    @staticmethod
    def execute(
        currency_obj: CurrencyObject,
        config: RequestConfig = DEFAULT_REQUEST_CONFIG,
        validate: bool = True,
        repository: Optional[Type[ICurrencyRepository]] = None,
    ) -> QuoteList:
        quote_service = GetCurrencyQuoteService(
            currency=currency_obj,
            currency_repository=repository or CurrencyAPI,
            config=config,
            validate=validate,
        )
        return quote_service.last()
