"""Fetch history without dropping pairs or silently discarding empty windows."""

from datetime import date
from typing import List, Sequence

from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.application.ports.outbound.currency_validator_repository import (
    ICurrencyValidator,
)
from currency_quote.application.use_cases.validate_currency import validate_pairs
from currency_quote.domain.entities.currency import CurrencyQuote
from currency_quote.exceptions import InvalidDateError, NoDataForDateError


def get_history_quotes(
    pairs: Sequence[str],
    start: date,
    end: date,
    repository: ICurrencyRepository,
    validator: ICurrencyValidator = None,
) -> List[CurrencyQuote]:
    if start > end:
        raise InvalidDateError("start_date must not be later than end_date")
    if validator is not None:
        validate_pairs(pairs, validator)

    result = []
    for pair in pairs:
        quotes = repository.get_history(pair, start, end)
        if not quotes:
            raise NoDataForDateError(f"No quotes for {pair} between {start} and {end}")
        # Group by the caller's pair order, newest first within each group.
        result.extend(
            sorted(quotes, key=lambda quote: quote.quote_timestamp, reverse=True)
        )
    return result
