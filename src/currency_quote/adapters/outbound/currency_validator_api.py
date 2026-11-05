# src/currency_quote/adapters/outbound/currency_validator_api.py
"""Validator adapter: checks pairs against the available-parities endpoint.

The parity list rarely changes, so it is cached with a TTL to save one
HTTP request on every quote call.
"""
from currency_quote.application.ports.outbound.currency_validator_repository import (
    ICurrencyValidator,
)
from currency_quote.config.endpoints import API
from currency_quote.domain.entities.currency import CurrencyObject
from currency_quote.exceptions import CurrencyAPIError
from currency_quote.utils.cache import TTLCache
from currency_quote.utils.http import get_json

PARITIES_CACHE: TTLCache = TTLCache(ttl_seconds=API.PARITIES_CACHE_TTL_SECONDS)


def fetch_available_parities() -> list:
    """Fetch the list of supported currency pairs (e.g. 'USD-BRL')."""
    response = get_json(API.ENDPOINT_AVALIABLE_PARITIES)
    if not isinstance(response, dict):
        raise CurrencyAPIError(
            "Gateway returned an unexpected payload for the parities endpoint: "
            "expected a JSON object."
        )
    return list(response.keys())


class CurrencyValidatorAPI(ICurrencyValidator):
    """Validates pairs against the available-parities endpoint (cached)."""

    def __init__(self, currency_quote: CurrencyObject) -> None:
        self.currency_quote = currency_quote

    def validate_currency_code(self) -> list:
        valid_list = PARITIES_CACHE.get_or_fetch(fetch_available_parities)

        validated_list = []
        for currency_code in self.currency_quote.get_currency_list():
            if currency_code in valid_list:
                validated_list.append(currency_code)

        return validated_list
