# src/currency_quote/utils/cache.py
"""A tiny thread-safe TTL cache used to avoid redundant API calls."""
import threading
import time
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Caches the result of ``fetch`` for ``ttl_seconds`` (per instance)."""

    def __init__(self, ttl_seconds: float) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._value = None
        self._stored_at = float("-inf")

    def get_or_fetch(self, fetch: Callable[[], T]) -> T:
        with self._lock:
            now = time.monotonic()
            if self._stored_at + self._ttl_seconds > now:
                return self._value  # type: ignore[return-value]
            self._value = fetch()
            self._stored_at = time.monotonic()
            return self._value  # type: ignore[return-value]

    def clear(self) -> None:
        with self._lock:
            self._value = None
            self._stored_at = float("-inf")
