# src/currency_quote/adapters/outbound/currency_validator_api.py
"""Validates currency pairs against the data source's available parities."""

import threading
import time
from typing import List, Optional, Set

from api_to_dataframe import ClientBuilder

from currency_quote.application.ports.outbound.currency_validator_repository import (
    ICurrencyValidator,
)
from currency_quote.config.endpoints import API
from currency_quote.config.settings import (
    DEFAULT_REQUEST_CONFIG,
    RequestConfig,
    RetryStrategy,
)
from currency_quote.domain.entities.currency import CurrencyObject
from currency_quote.exceptions import QuoteFetchError
from currency_quote.utils.logger import get_logger

logger = get_logger("currency_validator_api")


class _AvailableParitiesCache:
    """Process-wide, thread-safe TTL cache for the available parities list.

    The list of supported currency pairs changes very rarely, so refetching it
    on every quote request doubles latency for no benefit.
    """

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._value: Optional[Set[str]] = None
        self._fetched_at: float = 0.0

    def get(self, config: RequestConfig) -> Set[str]:
        with self._lock:
            if (
                self._value is not None
                and (time.monotonic() - self._fetched_at) < self._ttl
            ):
                return self._value

        value = self._fetch(config)

        with self._lock:
            self._value = value
            self._fetched_at = time.monotonic()

        return value

    def clear(self) -> None:
        """Drop the cached value, forcing the next lookup to refetch."""
        with self._lock:
            self._value = None
            self._fetched_at = 0.0

    @staticmethod
    def _fetch(config: RequestConfig) -> Set[str]:
        client = ClientBuilder(
            endpoint=API.ENDPOINT_AVALIABLE_PARITIES,
            **{
                **config.as_client_kwargs(),
                "retry_strategy": RetryStrategy.LINEAR.to_api_strategy(),
            },
        )

        try:
            response = client.get_api_data()
        except Exception as exc:  # pylint: disable=broad-except
            raise QuoteFetchError(
                f"Could not fetch the list of available currency pairs: {exc}"
            ) from exc

        return set(response)


_cache = _AvailableParitiesCache(API.AVAILABLE_PARITIES_TTL_SECONDS)


def clear_available_parities_cache() -> None:
    """Clear the cached list of available currency pairs."""
    _cache.clear()


class CurrencyValidatorAPI(ICurrencyValidator):
    """Filters currency pairs down to the ones the data source supports."""

    def __init__(
        self,
        currency_quote: CurrencyObject,
        config: RequestConfig = DEFAULT_REQUEST_CONFIG,
    ) -> None:
        self.currency_quote = currency_quote
        self.config = config

    def validate_currency_code(self) -> List[str]:
        available = _cache.get(self.config)

        return [
            currency_code
            for currency_code in self.currency_quote.get_currency_list()
            if currency_code in available
        ]
