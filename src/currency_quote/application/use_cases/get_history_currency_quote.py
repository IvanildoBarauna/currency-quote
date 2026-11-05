# src/currency_quote/application/use_cases/get_history_currency_quote.py
from typing import Optional, Type

from currency_quote.adapters.outbound.currency_api import CurrencyAPI
from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.config.settings import DEFAULT_REQUEST_CONFIG, RequestConfig
from currency_quote.domain.entities.currency import CurrencyObject, QuoteList
from currency_quote.domain.services.get_currency_quote import GetCurrencyQuoteService
from currency_quote.utils.dates import DateInput


class GetHistCurrencyQuoteUseCase:
    @staticmethod
    def execute(
        currency_obj: CurrencyObject,
        reference_date: DateInput,
        config: RequestConfig = DEFAULT_REQUEST_CONFIG,
        validate: bool = True,
        repository: Optional[Type[ICurrencyRepository]] = None,
    ) -> QuoteList:
        return GetHistCurrencyQuoteUseCase._service(
            currency_obj, config, validate, repository
        ).history(reference_date=reference_date)

    @staticmethod
    def execute_range(
        currency_obj: CurrencyObject,
        start_date: DateInput,
        end_date: Optional[DateInput] = None,
        config: RequestConfig = DEFAULT_REQUEST_CONFIG,
        validate: bool = True,
        repository: Optional[Type[ICurrencyRepository]] = None,
    ) -> QuoteList:
        return GetHistCurrencyQuoteUseCase._service(
            currency_obj, config, validate, repository
        ).history_range(start_date=start_date, end_date=end_date)

    @staticmethod
    def _service(
        currency_obj: CurrencyObject,
        config: RequestConfig,
        validate: bool,
        repository: Optional[Type[ICurrencyRepository]],
    ) -> GetCurrencyQuoteService:
        return GetCurrencyQuoteService(
            currency=currency_obj,
            currency_repository=repository or CurrencyAPI,
            config=config,
            validate=validate,
        )
