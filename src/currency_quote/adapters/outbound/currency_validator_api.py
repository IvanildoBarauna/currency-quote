"""Provider-supported pairs, cached per client for a bounded time."""

from threading import Lock
from time import monotonic
from typing import Set

from currency_quote.application.ports.outbound.currency_validator_repository import (
    ICurrencyValidator,
)
from currency_quote.config.endpoints import API
from currency_quote.exceptions import CurrencyAPIError, InvalidConfigError
from currency_quote.utils.http import HTTPClient


class CurrencyValidatorAPI(ICurrencyValidator):
    def __init__(self, http: HTTPClient, ttl_seconds: float = 3600):
        if ttl_seconds <= 0:
            raise InvalidConfigError("ttl_seconds must be positive")
        self.http = http
        self.ttl_seconds = ttl_seconds
        self._lock = Lock()
        self._value = None
        self._expires_at = 0.0

    def available_pairs(self) -> Set[str]:
        with self._lock:
            if self._value is None or monotonic() >= self._expires_at:
                response = self.http.get(API.ENDPOINT_AVALIABLE_PARITIES)
                if not isinstance(response, dict):
                    raise CurrencyAPIError(
                        "Available-pairs response must be a JSON object"
                    )
                self._value = set(response)
                self._expires_at = monotonic() + self.ttl_seconds
            return set(self._value)
