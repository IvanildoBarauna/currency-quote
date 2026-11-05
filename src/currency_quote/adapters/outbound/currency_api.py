# src/currency_quote/adapters/outbound/currency_api.py
"""AwesomeAPI adapter: translates raw API payloads into CurrencyQuote dataclasses."""
from datetime import date, timedelta
from typing import Any, Iterator, List, Mapping, Optional, Tuple

from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.config.endpoints import API
from currency_quote.domain.entities.currency import (
    CurrencyQuote,
    CurrencyObject,
)
from currency_quote.exceptions import (
    CurrencyAPIError,
    InvalidDateError,
    NoDataForDateError,
)
from currency_quote.utils.dates import (
    assert_valid_range,
    compact_to_date,
    parse_reference_date,
)
from currency_quote.utils.http import HTTPConfig, get_json
from currency_quote.utils.logger import get_logger

logger = get_logger("currency_api")

REQUIRED_QUOTE_KEYS = ("timestamp", "bid", "ask")
PERIOD_CHUNK_CALENDAR_DAYS = 360  # the Gateway caps daily history requests at 360
MAX_PERIOD_PATH_DAYS = 360


class CurrencyAPI(ICurrencyRepository):
    """Repository implementation for fetching currency quotes from external API."""

    def __init__(
        self,
        currency_obj: CurrencyObject,
        http_config: Optional[HTTPConfig] = None,
    ):
        self.currency_list = currency_obj.get_currency_list()
        self.http_config = http_config or HTTPConfig()

    def get_last_quote(self) -> List[CurrencyQuote]:
        url = f"{API.ENDPOINT_LAST_COTATION}{','.join(self.currency_list)}"
        response = self._request_last(url)
        if not isinstance(response, Mapping):
            raise CurrencyAPIError(
                f"Gateway returned an unexpected payload for {url}: expected a JSON object."
            )

        quote_list = []
        for item in self.currency_list:
            pair_key = item.replace("-", "")
            raw_quote = response.get(pair_key)
            if raw_quote is None:
                logger.warning(
                    "The Gateway did not return a quote for %s. Skipping pair.", item
                )
                continue
            quote_list.append(parse_currency_quote(item, raw_quote))

        if not quote_list:
            raise CurrencyAPIError(
                f"The Gateway did not return data for any pair of {self.currency_list}."
            )
        return quote_list

    def get_history_quote(self, reference_date: int) -> List[CurrencyQuote]:
        parsed_date = parse_reference_date(reference_date)
        if parsed_date >= int(date.today().strftime("%Y%m%d")):
            # today's daily entry is partial/unreliable; use get_last_quote instead
            raise InvalidDateError(
                f"Reference date {reference_date} must be earlier than today for a "
                "single-day query; use get_last_quote for current intraday data."
            )

        quote_list = []
        for item in self.currency_list:
            url = (
                f"{API.ENDPOINT_HISTORY_COTATION}{item}"
                f"?start_date={parsed_date}&end_date={parsed_date}"
            )
            raw_entries = self._request_history(item, url)
            quote_list.extend(parse_history_entries(item, raw_entries))
        return quote_list

    def get_history_range(self, start_date: int, end_date: int) -> List[CurrencyQuote]:
        start = parse_reference_date(start_date)
        end = parse_reference_date(end_date)
        assert_valid_range(start, end)

        quote_list = []
        for item in self.currency_list:
            for window_start, window_end in iter_period_windows(start, end):
                url = (
                    f"{API.ENDPOINT_HISTORY_COTATION}{item}/{MAX_PERIOD_PATH_DAYS}"
                    f"?start_date={window_start}&end_date={window_end}"
                )
                raw_entries = self._request_history(item, url)
                quote_list.extend(
                    filter_entries_by_date(
                        parse_history_entries(item, raw_entries),
                        window_start,
                        window_end,
                    )
                )
        return quote_list

    def _request_history(self, currency_pair: str, url: str) -> Any:
        """History request that maps a 404 to a friendly NoDataForDateError."""
        try:
            return self._request(url)
        except CurrencyAPIError as exc:
            if exc.status_code == 404:
                raise NoDataForDateError(
                    f"No daily history available for {currency_pair} on the requested "
                    "date(s); the pair may not keep daily archives (e.g. crypto)."
                ) from exc
            raise

    def _request_last(self, url: str) -> Any:
        """Last-quote request with a clearer message when a pair does not exist."""
        try:
            return self._request(url)
        except CurrencyAPIError as exc:
            if exc.status_code == 404:
                raise CurrencyAPIError(
                    f"The Gateway did not find the pair(s) {self.currency_list} "
                    "(CoinNotExists). Check the pair list at "
                    f"{API.ENDPOINT_AVALIABLE_PARITIES}, or disable validation "
                    "only if you are sure the pair exists.",
                    status_code=404,
                ) from exc
            raise

    def _request(self, url: str) -> Any:
        try:
            return get_json(
                url,
                attempts=self.http_config.retry_attempts,
                timeout_seconds=self.http_config.timeout_seconds,
            )
        except CurrencyAPIError:
            logger.error("Failed to fetch %s after retries.", url)
            raise


def iter_period_windows(start_date: int, end_date: int) -> Iterator[Tuple[int, int]]:
    """Split a compact-date range into Gateway-sized chunks (<= 360 calendar days)."""
    start = compact_to_date(start_date)
    end = compact_to_date(end_date)
    cursor = start
    while cursor <= end:
        window_end = min(cursor + timedelta(days=PERIOD_CHUNK_CALENDAR_DAYS - 1), end)
        yield int(cursor.strftime("%Y%m%d")), int(window_end.strftime("%Y%m%d"))
        cursor = window_end + timedelta(days=1)


def filter_entries_by_date(
    quotes: List[CurrencyQuote], start_date: int, end_date: int
) -> List[CurrencyQuote]:
    """Keep only quotes whose trading date (UTC) is inside the requested window."""
    start = compact_to_date(start_date)
    end = compact_to_date(end_date)
    return [quote for quote in quotes if start <= quote.trading_date() <= end]


def parse_currency_quote(
    currency_pair: str, payload: Mapping[str, Any]
) -> CurrencyQuote:
    """Convert a raw awesomeapi payload into a normalized ``CurrencyQuote``.

    Numeric fields coming as strings are converted to ``float``; daily-history
    entries omit ``name``/``code``/``codein``, so those are derived from the
    requested pair when missing. ``timestamp``, ``bid`` and ``ask`` are required.
    """
    base_currency, quote_currency = currency_pair.split("-")

    missing = [key for key in REQUIRED_QUOTE_KEYS if payload.get(key) is None]
    if missing:
        raise CurrencyAPIError(
            f"Malformed quote for {currency_pair}: missing fields {missing}."
        )

    return CurrencyQuote(
        currency_pair=currency_pair,
        currency_pair_name=str(
            payload.get("name") or f"{base_currency}/{quote_currency}"
        ),
        base_currency_code=str(payload.get("code") or base_currency),
        quote_currency_code=str(payload.get("codein") or quote_currency),
        quote_timestamp=to_int(payload["timestamp"], "timestamp", currency_pair),
        bid_price=to_float(payload["bid"], "bid", currency_pair),
        ask_price=to_float(payload["ask"], "ask", currency_pair),
        high_price=to_optional_float(payload.get("high")),
        low_price=to_optional_float(payload.get("low")),
        var_bid=to_optional_float(payload.get("varBid")),
        pct_change=to_optional_float(payload.get("pctChange")),
    )


def parse_history_entries(currency_pair: str, entries: Any) -> List[CurrencyQuote]:
    """Parse the daily endpoint list payload, raising a helpful error when empty."""
    if not isinstance(entries, list):
        raise CurrencyAPIError(
            f"Gateway returned an unexpected payload for {currency_pair} history: expected a list."
        )
    if len(entries) == 0:
        raise NoDataForDateError(
            f"No quotes found for {currency_pair} on the requested date(s). "
            "The market was probably closed (weekend/holiday) or the dates are "
            "older than the available history."
        )

    pair_quotes = [parse_currency_quote(currency_pair, entry) for entry in entries]
    pair_quotes.sort(key=lambda quote: quote.quote_timestamp)
    return pair_quotes


def to_float(value: Any, field_name: str, currency_pair: str) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise CurrencyAPIError(
            f"Malformed quote for {currency_pair}: field {field_name!r} "
            f"got unexpected value {value!r}."
        ) from exc


def to_int(value: Any, field_name: str, currency_pair: str) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise CurrencyAPIError(
            f"Malformed quote for {currency_pair}: field {field_name!r} "
            f"got unexpected value {value!r}."
        ) from exc


def to_optional_float(value: Any) -> Optional[float]:
    """Convert optional numeric statistics, tolerating missing/unparseable values."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        logger.warning("Ignoring non-numeric optional field with value %r.", value)
        return None
