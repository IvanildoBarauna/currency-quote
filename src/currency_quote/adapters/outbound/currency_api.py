"""AwesomeAPI adapter: schema validation and bounded daily history requests."""

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import List, Mapping, Sequence
from urllib.parse import quote

from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.config.endpoints import API
from currency_quote.domain.entities.currency import CurrencyQuote
from currency_quote.exceptions import CurrencyAPIError, NoDataForDateError
from currency_quote.utils.dates import trading_date
from currency_quote.utils.http import HTTPClient

_WINDOW_DAYS = 360


def _as_decimal(value: object, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
        if not result.is_finite():
            raise InvalidOperation
        return result
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CurrencyAPIError(f"Malformed provider field {field}: {value!r}") from exc


def _as_timestamp(value: object) -> int:
    """Normalize provider Unix seconds or 13-digit milliseconds to seconds."""
    if isinstance(value, bool):
        raise CurrencyAPIError("Malformed provider field timestamp: boolean")
    try:
        timestamp = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise CurrencyAPIError(
            f"Malformed provider field timestamp: {value!r}"
        ) from exc
    if 10**12 <= abs(timestamp) < 10**15:
        return timestamp // 1000
    return timestamp


def _quote(pair: str, payload: object) -> CurrencyQuote:
    if not isinstance(payload, Mapping):
        raise CurrencyAPIError(f"Malformed quote for {pair}: expected an object")
    try:
        timestamp = _as_timestamp(payload["timestamp"])
        base, target = pair.split("-")
        name = payload.get("name") or f"{base}/{target}"
        return CurrencyQuote(
            currency_pair=pair,
            currency_pair_name=str(name),
            base_currency_code=str(payload.get("code") or base),
            quote_currency_code=str(payload.get("codein") or target),
            quote_timestamp=timestamp,
            bid_price=_as_decimal(payload["bid"], "bid"),
            ask_price=_as_decimal(payload["ask"], "ask"),
            high_price=(
                _as_decimal(payload["high"], "high")
                if payload.get("high") is not None
                else None
            ),
            low_price=(
                _as_decimal(payload["low"], "low")
                if payload.get("low") is not None
                else None
            ),
            var_bid=(
                _as_decimal(payload["varBid"], "varBid")
                if payload.get("varBid") is not None
                else None
            ),
            pct_change=(
                _as_decimal(payload["pctChange"], "pctChange")
                if payload.get("pctChange") is not None
                else None
            ),
        )
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise CurrencyAPIError(f"Malformed quote for {pair}: {exc}") from exc


class CurrencyAPI(ICurrencyRepository):
    def __init__(self, http: HTTPClient):
        self.http = http

    def get_last_quote(self, pairs: Sequence[str]) -> List[CurrencyQuote]:
        url = API.ENDPOINT_LAST_COTATION + ",".join(
            quote(pair, safe="-") for pair in pairs
        )
        response = self.http.get(url)
        if not isinstance(response, Mapping):
            raise CurrencyAPIError("Current quote response must be a JSON object")
        result = []
        for pair in pairs:
            raw = response.get(pair.replace("-", ""))
            if raw is None:
                raise NoDataForDateError(f"No current quote for {pair}")
            result.append(_quote(pair, raw))
        return result

    def get_history(self, pair: str, start: date, end: date) -> List[CurrencyQuote]:
        result = {}
        cursor = start
        while cursor <= end:
            window_end = min(cursor + timedelta(days=_WINDOW_DAYS - 1), end)
            begin = cursor.strftime("%Y%m%d")
            finish = window_end.strftime("%Y%m%d")
            path = f"{pair}/360" if cursor != window_end else pair
            url = (
                f"{API.ENDPOINT_HISTORY_COTATION}{quote(path, safe='-/')}"
                f"?start_date={begin}&end_date={finish}"
            )
            try:
                response = self.http.get(url)
            except CurrencyAPIError as exc:
                if exc.status_code != 404:
                    raise
                response = []  # the provider has no daily archive in this window
            if not isinstance(response, list):
                raise CurrencyAPIError(
                    f"History response for {pair} must be a JSON list"
                )
            for entry in response:
                parsed = _quote(pair, entry)
                try:
                    day = trading_date(entry, parsed.quote_timestamp)
                except (ValueError, OverflowError, OSError) as exc:
                    raise CurrencyAPIError(
                        f"Malformed trading timestamp for {pair}"
                    ) from exc
                if start <= day <= end:
                    result[parsed.quote_timestamp] = parsed
            cursor = window_end + timedelta(days=1)
        return list(result.values())
