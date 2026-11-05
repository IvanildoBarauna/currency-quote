"""Shared transport for quote and parity requests."""

from dataclasses import dataclass
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from currency_quote.exceptions import CurrencyAPIError, InvalidConfigError


@dataclass(frozen=True)
class HTTPConfig:
    timeout: float = 10.0
    retries: int = 2  # additional retries, beyond the initial request

    def __post_init__(self):
        if (
            isinstance(self.timeout, bool)
            or not isinstance(self.timeout, (int, float))
            or self.timeout <= 0
            or isinstance(self.retries, bool)
            or not isinstance(self.retries, int)
            or self.retries < 0
        ):
            raise InvalidConfigError(
                "timeout must be positive and retries must be nonnegative"
            )


class HTTPClient:
    """Own one pooled Session, including a retry policy shared by both endpoints."""

    def __init__(self, config: HTTPConfig, session: requests.Session = None):
        self.config = config
        self.session = session or requests.Session()
        self._owns_session = session is None
        if self._owns_session:
            retry = Retry(
                total=config.retries,
                backoff_factor=0.5,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=("GET",),
                respect_retry_after_header=True,
            )
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount("https://", adapter)

    def get(self, url: str) -> Any:
        try:
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            raise CurrencyAPIError(
                f"Provider returned HTTP {status}: {url}", status
            ) from exc
        except (requests.RequestException, ValueError) as exc:
            raise CurrencyAPIError(f"Provider request or JSON failed: {url}") from exc

    def close(self):
        if self._owns_session:
            self.session.close()
