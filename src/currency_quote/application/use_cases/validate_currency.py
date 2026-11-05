# src/currency_quote/application/use_cases/validate_currency.py
from currency_quote.adapters.outbound.currency_validator_api import CurrencyValidatorAPI
from currency_quote.config.settings import DEFAULT_REQUEST_CONFIG, RequestConfig
from currency_quote.domain.entities.currency import CurrencyObject
from currency_quote.domain.services.validate_currency import CurrencyValidatorService


class ValidateCurrencyUseCase:
    @staticmethod
    def execute(
        currency_quote: CurrencyObject,
        config: RequestConfig = DEFAULT_REQUEST_CONFIG,
    ) -> CurrencyObject:
        validator_service = CurrencyValidatorService(
            currency=currency_quote,
            currency_validator=CurrencyValidatorAPI,
            config=config,
        )
        return validator_service.validate_currency_code()
