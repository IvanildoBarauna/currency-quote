"""Pair validation policy independent of the AwesomeAPI adapter."""

from typing import Sequence

from currency_quote.application.ports.outbound.currency_validator_repository import (
    ICurrencyValidator,
)
from currency_quote.exceptions import InvalidCurrencyError


def validate_pairs(pairs: Sequence[str], validator: ICurrencyValidator) -> None:
    available = validator.available_pairs()
    invalid = [pair for pair in pairs if pair not in available]
    if invalid:
        raise InvalidCurrencyError(f"Unsupported currency pairs: {invalid}")
