# src/currency_quote/application/use_cases/validate_currency.py
from currency_quote.domain.services.validate_currency import CurrencyValidatorService
from currency_quote.adapters.outbound.currency_validator_api import CurrencyValidatorAPI
from currency_quote.domain.entities.currency import CurrencyObject


class ValidateCurrencyUseCase:
    """Filters pairs through the online validator service."""

    @staticmethod
    def execute(currency_quote: CurrencyObject) -> CurrencyObject:
        validator_service = CurrencyValidatorService(
            currency=currency_quote, currency_validator=CurrencyValidatorAPI
        )
        return validator_service.validate_currency_code()
