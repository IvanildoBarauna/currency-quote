# src/currency_quote/application/services/currency_validator_service.py
from typing import Type
from currency_quote.domain.entities.currency import CurrencyObject
from currency_quote.application.ports.outbound.currency_validator_repository import (
    ICurrencyValidator,
)
from currency_quote.utils.logger import get_logger

logger = get_logger("validate_currency")


class CurrencyValidatorService:
    """Service for validating currency codes using a currency validator repository."""

    def __init__(
        self, currency: CurrencyObject, currency_validator: Type[ICurrencyValidator]
    ):
        self.currency_validator = currency_validator
        self.currency_quote = currency
        self.currency_list = currency.currency_list

    def validate_currency_code(self) -> CurrencyObject:
        """
        Validate currency codes using the validator repository.

        Returns:
            CurrencyObject: A new CurrencyObject containing only valid currency pairs.

        Raises:
            ValueError: If all provided currency pairs are invalid.
        """
        validated_list = self.currency_validator(
            self.currency_quote
        ).validate_currency_code()

        if len(validated_list) == 0:
            logger.error("All currency params are invalid: %s", self.currency_list)
            raise ValueError(f"All params: {self.currency_list} are invalid.")

        invalid_currencies = [
            currency for currency in self.currency_list if currency not in validated_list
        ]
        if invalid_currencies:
            logger.warning("Invalid currency params: %s", invalid_currencies)
            raise ValueError(f"Invalid currency pairs: {invalid_currencies}")

        return CurrencyObject(validated_list)
