# src/currency_quote/application/use_cases/get_history_currency_quote.py
from typing import List, Optional
from currency_quote.adapters.outbound.currency_api import CurrencyAPI
from currency_quote.domain.services.get_currency_quote import GetCurrencyQuoteService
from currency_quote.domain.entities.currency import CurrencyObject, CurrencyQuote
from currency_quote.utils.http import HTTPConfig


class GetHistCurrencyQuoteUseCase:
    """Fetches the daily quote of one specific past day."""

    @staticmethod
    def execute(
        currency_obj: CurrencyObject,
        reference_date: int,
        validate: bool = True,
        http_config: Optional[HTTPConfig] = None,
    ) -> List[CurrencyQuote]:
        quote_service = GetCurrencyQuoteService(
            currency=currency_obj,
            currency_repository=lambda pending_currency: CurrencyAPI(
                pending_currency, http_config=http_config
            ),
            validate=validate,
        )
        return quote_service.history(reference_date=reference_date)


class GetHistCurrencyQuoteRangeUseCase:
    """Fetches daily quotes for a date range (single Gateway window or paginated)."""

    @staticmethod
    def execute(
        currency_obj: CurrencyObject,
        start_date: int,
        end_date: int,
        validate: bool = True,
        http_config: Optional[HTTPConfig] = None,
    ) -> List[CurrencyQuote]:
        quote_service = GetCurrencyQuoteService(
            currency=currency_obj,
            currency_repository=lambda pending_currency: CurrencyAPI(
                pending_currency, http_config=http_config
            ),
            validate=validate,
        )
        return quote_service.history_range(start_date=start_date, end_date=end_date)
