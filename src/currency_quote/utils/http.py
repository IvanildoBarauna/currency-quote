# src/currency_quote/utils/http.py
"""HTTP helpers: GET requests with retries, timeouts and typed errors."""
import json
import time
from dataclasses import dataclass
from typing import Any, Optional

import requests

from currency_quote.config.endpoints import API
from currency_quote.exceptions import CurrencyAPIError
from currency_quote.utils.logger import get_logger

logger = get_logger("http")

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class HTTPConfig:
    """Knobs for the outbound HTTP layer, exposed to `CurrencyQuoteClient`."""

    timeout_seconds: float = API.HTTP_TIMEOUT_SECONDS
    retry_attempts: int = API.HTTP_RETRY_ATTEMPTS

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        if self.retry_attempts < 1:
            raise ValueError("retry_attempts must be at least 1")


def _backoff_delay(attempt: int) -> float:
    return min(API.HTTP_BACKOFF_BASE_SECONDS * (2**attempt), 30.0)


def get_json(
    url: str,
    timeout_seconds: float = API.HTTP_TIMEOUT_SECONDS,
    attempts: int = API.HTTP_RETRY_ATTEMPTS,
) -> Any:
    """GET ``url`` and decode the JSON payload, with exponential-backoff retries.

    Retries on connection errors, timeouts, and 4xx/5xx status codes.
    Raises ``CurrencyAPIError`` once attempts are exhausted or on a
    non-JSON response.
    """
    last_error: Optional[Exception] = None
    for attempt in range(attempts):
        try:
            response = requests.get(
                url, timeout=timeout_seconds, headers={"Accept": "application/json"}
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            last_error = exc
            logger.warning(
                "Request to %s timed out (attempt %d/%d).", url, attempt + 1, attempts
            )
        except requests.ConnectionError as exc:
            last_error = exc
            logger.warning(
                "Connection error on %s (attempt %d/%d).", url, attempt + 1, attempts
            )
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code not in RETRYABLE_STATUS_CODES:
                raise CurrencyAPIError(
                    f"Gateway returned HTTP {status_code} for {url}.",
                    status_code=status_code,
                ) from exc
            last_error = exc
            logger.warning(
                "HTTP %s from %s (attempt %d/%d).",
                status_code,
                url,
                attempt + 1,
                attempts,
            )
        else:
            try:
                return response.json()
            except json.JSONDecodeError as exc:
                raise CurrencyAPIError(
                    f"Gateway did not return valid JSON for {url}."
                ) from exc

        if attempt < attempts - 1:
            delay = _backoff_delay(attempt)
            logger.info("Retrying %s in %.1fs.", url, delay)
            time.sleep(delay)

    raise CurrencyAPIError(
        f"Gateway unreachable after {attempts} attempt(s): {url}."
    ) from last_error
