"""AwesomeAPI-backed implementation of the currency repository port."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from typing import Any, List, Optional, Tuple

from api_to_dataframe import ClientBuilder

from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.config.endpoints import API
from currency_quote.config.settings import DEFAULT_REQUEST_CONFIG, RequestConfig
from currency_quote.domain.entities.currency import (
    CurrencyObject,
    CurrencyQuote,
    QuoteList,
)
from currency_quote.exceptions import QuoteFetchError
from currency_quote.utils.dates import DateInput, to_date, validate_past_date
from currency_quote.utils.logger import get_logger

logger = get_logger("currency_api")


def _compact(value: date) -> int:
    """Render a date as the YYYYMMDD integer the API expects."""
    return int(value.strftime("%Y%m%d"))


def _date_windows(start: date, end: date) -> List[Tuple[date, date]]:
    """Split an inclusive range into windows the data source can serve."""
    step = timedelta(days=API.HISTORY_CHUNK_DAYS - 1)
    windows = []
    cursor = start
    while cursor <= end:
        window_end = min(cursor + step, end)
        windows.append((cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return windows


class CurrencyAPI(ICurrencyRepository):
    """Repository implementation for fetching currency quotes from external API."""

    def __init__(
        self,
        currency_obj: CurrencyObject,
        config: RequestConfig = DEFAULT_REQUEST_CONFIG,
    ):
        self.currency_list = currency_obj.get_currency_list()
        self.config = config

    def get_last_quote(self) -> QuoteList:
        url = f"{API.ENDPOINT_LAST_COTATION}{','.join(self.currency_list)}"
        response = self._request(url)

        quote_list = QuoteList()

        for item in self.currency_list:
            payload = response.get(item.replace("-", ""))
            if payload is None:
                raise QuoteFetchError(
                    f"Data source returned no quote for {item}", currency_pair=item
                )
            quote_list.append(self._build_quote(item, payload))

        return quote_list

    def get_history_quote(self, reference_date: DateInput) -> QuoteList:
        normalized = validate_past_date(reference_date)
        return self.get_history_quote_range(normalized, normalized)

    def get_history_quote_range(
        self,
        start_date: DateInput,
        end_date: Optional[DateInput] = None,
    ) -> QuoteList:
        """Fetch daily closing quotes for an inclusive date range.

        Ranges longer than the data source's per-request limit are split into
        several windows transparently and fetched in parallel.
        """
        start = to_date(start_date)
        end = to_date(end_date) if end_date is not None else start

        if start > end:
            start, end = end, start

        tasks = [
            (pair, window_start, window_end)
            for pair in self.currency_list
            for window_start, window_end in _date_windows(start, end)
        ]

        results = self._fetch_concurrently(tasks)

        quote_list = QuoteList()
        seen = set()
        for pair, payload in results:
            if not isinstance(payload, list):
                raise QuoteFetchError(
                    f"Unexpected historical payload for {pair}: expected a list",
                    currency_pair=pair,
                )
            metadata = payload[0] if payload else {}
            for entry in payload:
                # AwesomeAPI omits name/code/codein after the first entry.
                quote = self._build_quote(pair, {**metadata, **entry})
                key = (quote.currency_pair, quote.quote_timestamp)
                if key not in seen:
                    seen.add(key)
                    quote_list.append(quote)

        if not quote_list:
            raise QuoteFetchError(
                "No historical data for "
                f"{', '.join(self.currency_list)} between "
                f"{_compact(start)} and {_compact(end)}"
            )

        return quote_list

    def _fetch_concurrently(self, tasks: List[tuple]) -> List[tuple]:
        """Fetch every (pair, window) task, preserving input order."""

        def fetch(task: tuple) -> tuple:
            pair, window_start, window_end = task
            span = (window_end - window_start).days + 1
            limit = min(span, API.HISTORY_MAX_RECORDS)
            url = (
                f"{API.ENDPOINT_HISTORY_COTATION}{pair}/{limit}"
                f"?start_date={_compact(window_start)}"
                f"&end_date={_compact(window_end)}"
            )
            return pair, self._request(url, currency_pair=pair) or []

        if len(tasks) == 1:
            return [fetch(tasks[0])]

        workers = min(self.config.max_workers, len(tasks))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            return list(executor.map(fetch, tasks))

    def _request(self, url: str, currency_pair: Optional[str] = None) -> Any:
        client = ClientBuilder(endpoint=url, **self.config.as_client_kwargs())
        try:
            return client.get_api_data()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Request to the data source failed: %s", exc)
            raise QuoteFetchError(
                f"Failed to fetch data from the currency data source: {exc}",
                currency_pair=currency_pair,
            ) from exc

    @staticmethod
    def _build_quote(currency_pair: str, payload: dict) -> CurrencyQuote:
        try:
            return CurrencyQuote(
                currency_pair=currency_pair,
                currency_pair_name=payload["name"],
                base_currency_code=payload["code"],
                quote_currency_code=payload["codein"],
                quote_timestamp=int(payload["timestamp"]),
                bid_price=float(payload["bid"]),
                ask_price=float(payload["ask"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise QuoteFetchError(
                f"Unexpected payload for {currency_pair}: {exc}",
                currency_pair=currency_pair,
            ) from exc
