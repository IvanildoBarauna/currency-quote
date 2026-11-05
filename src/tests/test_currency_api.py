# src/tests/test_currency_api.py
"""Tests for the AwesomeAPI adapter: normalization, ranges and typed errors."""
from unittest.mock import patch

import pytest

from currency_quote.adapters.outbound.currency_api import (
    CurrencyAPI,
    parse_currency_quote,
)
from currency_quote.config.endpoints import API
from currency_quote.domain.entities.currency import CurrencyObject, CurrencyQuote
from currency_quote.exceptions import (
    CurrencyAPIError,
    InvalidDateError,
    NoDataForDateError,
)

SNAPSHOT = {
    "code": "USD",
    "codein": "BRL",
    "name": "Dólar Americano/Real Brasileiro",
    "high": "5.1234",
    "low": "5.0432",
    "varBid": "0.0123",
    "pctChange": "0.24",
    "bid": "5.0876",
    "ask": "5.0891",
    "timestamp": "1614024000",
}


def test_parse_normalizes_numbers():
    quote = parse_currency_quote("USD-BRL", SNAPSHOT)
    assert isinstance(quote, CurrencyQuote)
    assert quote.bid_price == 5.0876
    assert quote.ask_price == 5.0891
    assert isinstance(quote.bid_price, float)
    assert quote.high_price == 5.1234
    assert quote.var_bid == 0.0123
    assert quote.pct_change == 0.24
    assert quote.quote_timestamp == 1614024000


def test_parse_optional_fields_default_to_none():
    payload = {
        key: value
        for key, value in SNAPSHOT.items()
        if key not in ("high", "low", "varBid", "pctChange")
    }
    quote = parse_currency_quote("USD-BRL", payload)
    assert quote.high_price is None
    assert quote.low_price is None
    assert quote.var_bid is None
    assert quote.pct_change is None
    assert quote.bid_price == 5.0876


def test_parse_ignores_non_numeric_optional_fields():
    payload = dict(SNAPSHOT, varBid="junk")
    quote = parse_currency_quote("USD-BRL", payload)
    assert quote.var_bid is None


def test_parse_missing_required_field_raises():
    payload = dict(SNAPSHOT, bid=None)
    with pytest.raises(CurrencyAPIError, match="missing fields"):
        parse_currency_quote("USD-BRL", payload)


def test_parse_corrupted_required_field_raises():
    payload = dict(SNAPSHOT, bid="not-a-number", timestamp="N/A")
    with pytest.raises(CurrencyAPIError, match="timestamp"):
        parse_currency_quote("USD-BRL", payload)


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_get_last_quote_returns_typed_quotes(mock_get, mock_currency_api_response):
    mock_get.return_value = mock_currency_api_response
    api = CurrencyAPI(CurrencyObject(["USD-BRL", "EUR-BRL"]))
    quotes = api.get_last_quote()

    assert len(quotes) == 2
    assert all(isinstance(quote, CurrencyQuote) for quote in quotes)
    usd = quotes[0]
    assert usd.currency_pair == "USD-BRL"
    assert usd.bid_price == 5.0876
    assert isinstance(usd.quote_extracted_at, int)


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_get_last_quote_skips_missing_pairs(mock_get, mock_currency_api_response):
    partial = {"USDBRL": mock_currency_api_response["USDBRL"]}
    mock_get.return_value = partial
    api = CurrencyAPI(CurrencyObject(["EUR-BRL", "USD-BRL"]))
    quotes = api.get_last_quote()
    assert [quote.currency_pair for quote in quotes] == ["USD-BRL"]


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_get_last_quote_empty_payload_raises(mock_get):
    mock_get.return_value = {}
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))
    with pytest.raises(CurrencyAPIError, match="did not return data"):
        api.get_last_quote()


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_get_history_quote_normalizes_and_returns(
    mock_get, mock_currency_history_api_response
):
    mock_get.return_value = mock_currency_history_api_response
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))
    quotes = api.get_history_quote(reference_date=20220621)

    assert len(quotes) == 1
    assert quotes[0].currency_pair == "USD-BRL"
    assert quotes[0].bid_price == 5.0876
    assert isinstance(quotes[0].bid_price, float)


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_get_history_quote_invalid_date_raises_without_request(mock_get):
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))
    with pytest.raises(InvalidDateError):
        api.get_history_quote(reference_date=99999999)
    mock_get.assert_not_called()


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_get_history_quote_empty_market_raises_helpful_error(mock_get):
    mock_get.return_value = []
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))
    with pytest.raises(NoDataForDateError, match="market was probably closed"):
        api.get_history_quote(reference_date=20220619)


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_history_range_returns_chronological_quotes(mock_get):
    day_before = dict(SNAPSHOT, timestamp="1641229200")  # 2022-01-03 17:00 UTC
    day_a = dict(SNAPSHOT, timestamp="1641315600")  # 2022-01-04 17:00 UTC
    day_b = dict(SNAPSHOT, timestamp="1641402000")  # 2022-01-05 17:00 UTC
    out_of_range = dict(SNAPSHOT, timestamp="1643692800")  # 2022-02-01 06:00 UTC
    mock_get.return_value = [
        out_of_range,
        day_b,
        day_a,
        day_before,
    ]  # API returns newest first

    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))
    quotes = api.get_history_range(20220104, 20220105)

    assert [quote.quote_timestamp for quote in quotes] == [1641315600, 1641402000]
    assert quotes[0].high_price == 5.1234
    called_url = mock_get.call_args.args[0]
    assert (
        called_url.endswith("/json/daily/USD-BRL/")
        or "/json/daily/USD-BRL/" in called_url
    )
    assert called_url.count("/json/daily/USD-BRL/") == 1


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_history_range_inverted_dates_raises_without_request(mock_get):
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))
    with pytest.raises(InvalidDateError, match="earlier than or equal to"):
        api.get_history_range(20220110, 20220101)
    mock_get.assert_not_called()


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_last_quote_404_gets_clear_pair_message(mock_get):
    """With validation skipped, a CoinNotExists 404 must mention the requested pairs."""
    mock_get.side_effect = CurrencyAPIError(
        "Gateway returned HTTP 404 for ...", status_code=404
    )
    api = CurrencyAPI(CurrencyObject(["BTC-JPY"]))
    with pytest.raises(CurrencyAPIError, match=r"\['BTC-JPY'\].*CoinNotExists"):
        api.get_last_quote()


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_history_404_becomes_friendly_no_data_error(mock_get):
    """Crypto pairs (e.g. BTC-JPY) have no daily archive: 404 -> NoDataForDateError."""
    mock_get.side_effect = CurrencyAPIError(
        f"Gateway returned HTTP 404 for {API.ENDPOINT_HISTORY_COTATION}BTC-JPY",
        status_code=404,
    )
    api = CurrencyAPI(CurrencyObject(["BTC-JPY"]))
    with pytest.raises(NoDataForDateError, match="may not keep daily archives"):
        api.get_history_quote(reference_date=20250102)
    with pytest.raises(NoDataForDateError, match="may not keep daily archives"):
        api.get_history_range(20250101, 20250110)


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_history_other_http_errors_still_raise_api_error(mock_get):
    mock_get.side_effect = CurrencyAPIError(
        "Gateway returned HTTP 503 for ...", status_code=503
    )
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))
    with pytest.raises(CurrencyAPIError, match="503"):
        api.get_history_quote(reference_date=20250102)


@patch("currency_quote.adapters.outbound.currency_api.get_json")
def test_history_entries_without_snapshot_fields_are_filled_from_pair(mock_get):
    """Older daily entries omit name/code/codein; they must still parse."""
    mock_get.return_value = [
        {
            "high": "5.1",
            "low": "5.0",
            "bid": "5.05",
            "ask": "5.06",
            "timestamp": "1653000000",
        }
    ]
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))
    quotes = api.get_history_range(20220519, 20220520)
    assert len(quotes) == 1
    assert quotes[0].currency_pair == "USD-BRL"
    assert quotes[0].base_currency_code == "USD"
    assert quotes[0].quote_currency_code == "BRL"
    assert quotes[0].currency_pair_name == "USD/BRL"
