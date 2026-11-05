# src/currency_quote/application/use_cases/get_last_currency_quote.py
from typing import List, Optional
from currency_quote.adapters.outbound.currency_api import CurrencyAPI
from currency_quote.domain.services.get_currency_quote import GetCurrencyQuoteService
from currency_quote.domain.entities.currency import CurrencyQuote, CurrencyObject
from currency_quote.utils.http import HTTPConfig


class GetLastCurrencyQuoteUseCase:
    """Fetches the latest quotes via the quote service."""

    @staticmethod
    def execute(
        currency_obj: CurrencyObject,
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
        return quote_service.last()
