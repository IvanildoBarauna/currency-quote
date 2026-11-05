"""User-facing configuration for outbound HTTP behaviour."""

from dataclasses import dataclass
from enum import Enum

from api_to_dataframe import RetryStrategies


class RetryStrategy(str, Enum):
    """Retry strategies supported when talking to the data source."""

    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"

    def to_api_strategy(self) -> RetryStrategies:
        """Translate the public enum into the underlying transport enum."""
        return _STRATEGY_MAP[self]


_STRATEGY_MAP = {
    RetryStrategy.NONE: RetryStrategies.NO_RETRY_STRATEGY,
    RetryStrategy.LINEAR: RetryStrategies.LINEAR_RETRY_STRATEGY,
    RetryStrategy.EXPONENTIAL: RetryStrategies.EXPONENTIAL_RETRY_STRATEGY,
}


@dataclass(frozen=True)
class RequestConfig:
    """Transport settings applied to every request made by the library.

    Args:
        retry_strategy: Backoff policy used when a request fails.
        retries: Maximum number of retry attempts.
        initial_delay: Seconds to wait before the first retry.
        timeout: Connection timeout, in seconds.
        max_workers: Maximum number of parallel requests when several currency
            pairs must be fetched individually.
    """

    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    retries: int = 3
    initial_delay: int = 1
    timeout: int = 10
    max_workers: int = 8

    def __post_init__(self) -> None:
        if self.retries < 0:
            raise ValueError("retries must be >= 0")
        if self.initial_delay < 0:
            raise ValueError("initial_delay must be >= 0")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")
        if self.max_workers < 1:
            raise ValueError("max_workers must be >= 1")

    def as_client_kwargs(self) -> dict:
        """Build the keyword arguments accepted by the HTTP client."""
        return {
            "retry_strategy": self.retry_strategy.to_api_strategy(),
            "retries": self.retries,
            "initial_delay": self.initial_delay,
            "connection_timeout": self.timeout,
        }


DEFAULT_REQUEST_CONFIG = RequestConfig()
