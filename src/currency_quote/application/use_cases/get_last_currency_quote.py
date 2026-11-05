"""Fetch current quotes after optional parity validation."""

from typing import List, Sequence

from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.application.ports.outbound.currency_validator_repository import (
    ICurrencyValidator,
)
from currency_quote.application.use_cases.validate_currency import validate_pairs
from currency_quote.domain.entities.currency import CurrencyQuote


def get_last_quotes(
    pairs: Sequence[str],
    repository: ICurrencyRepository,
    validator: ICurrencyValidator = None,
) -> List[CurrencyQuote]:
    if validator is not None:
        validate_pairs(pairs, validator)
    return repository.get_last_quote(pairs)
