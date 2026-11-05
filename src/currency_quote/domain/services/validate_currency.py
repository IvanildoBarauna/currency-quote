# src/currency_quote/domain/services/validate_currency.py
from typing import Type

from currency_quote.application.ports.outbound.currency_validator_repository import (
    ICurrencyValidator,
)
from currency_quote.config.settings import DEFAULT_REQUEST_CONFIG, RequestConfig
from currency_quote.domain.entities.currency import CurrencyObject
from currency_quote.exceptions import CurrencyNotFoundError
from currency_quote.utils.logger import get_logger

logger = get_logger("validate_currency")


class CurrencyValidatorService:
    """Service for validating currency codes using a currency validator repository."""

    def __init__(
        self,
        currency: CurrencyObject,
        currency_validator: Type[ICurrencyValidator],
        config: RequestConfig = DEFAULT_REQUEST_CONFIG,
    ):
        self.currency_validator = currency_validator
        self.currency_quote = currency
        self.currency_list = currency.currency_list
        self.config = config

    def validate_currency_code(self) -> CurrencyObject:
        """
        Validate currency codes using the validator repository.

        Returns:
            CurrencyObject: A new CurrencyObject containing only valid currency pairs.

        Raises:
            CurrencyNotFoundError: If all provided currency pairs are invalid.
        """
        validated_list = self.currency_validator(
            self.currency_quote, self.config
        ).validate_currency_code()

        if len(validated_list) == 0:
            logger.error("All currency params are invalid: %s", self.currency_list)
            raise CurrencyNotFoundError(
                self.currency_list,
                message=f"All params: {self.currency_list} are invalid.",
            )

        if len(validated_list) < len(self.currency_list):
            invalid_currencies = set(self.currency_list) - set(validated_list)
            logger.warning("Invalid currency params: %s", invalid_currencies)

        return CurrencyObject(validated_list)
