from unittest.mock import MagicMock, patch

import pytest

from currency_quote.adapters.outbound.currency_api import CurrencyAPI
from currency_quote.config.settings import RequestConfig
from currency_quote.domain.entities.currency import CurrencyObject, QuoteList
from currency_quote.exceptions import InvalidDateError, QuoteFetchError

TARGET = "currency_quote.adapters.outbound.currency_api.ClientBuilder"


def test_get_last_quote_parses_payload(mock_currency_api_response):
    api = CurrencyAPI(CurrencyObject(["USD-BRL", "EUR-BRL"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = mock_currency_api_response
        quotes = api.get_last_quote()

    assert isinstance(quotes, QuoteList)
    assert quotes.pairs == ["USD-BRL", "EUR-BRL"]
    # Prices are coerced to float, not left as strings
    assert quotes[0].bid_price == pytest.approx(5.0876)
    assert isinstance(quotes[0].ask_price, float)


def test_get_last_quote_requests_all_pairs_in_one_call(mock_currency_api_response):
    api = CurrencyAPI(CurrencyObject(["USD-BRL", "EUR-BRL"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = mock_currency_api_response
        api.get_last_quote()

    assert client.call_count == 1
    assert "USD-BRL,EUR-BRL" in client.call_args.kwargs["endpoint"]


def test_get_last_quote_raises_when_pair_missing_from_payload():
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = {}
        with pytest.raises(QuoteFetchError, match="no quote for USD-BRL"):
            api.get_last_quote()


def test_transport_failure_is_wrapped():
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.side_effect = RuntimeError("boom")
        with pytest.raises(QuoteFetchError, match="Failed to fetch data"):
            api.get_last_quote()


def test_request_config_is_forwarded_to_transport(mock_currency_api_response):
    config = RequestConfig(retries=7, timeout=42)
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]), config)

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = mock_currency_api_response
        api.get_last_quote()

    assert client.call_args.kwargs["retries"] == 7
    assert client.call_args.kwargs["connection_timeout"] == 42


def test_history_range_fetches_each_pair(mock_currency_history_api_response):
    api = CurrencyAPI(CurrencyObject(["USD-BRL", "EUR-BRL"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = (
            mock_currency_history_api_response
        )
        quotes = api.get_history_quote_range(20240601, 20240630)

    assert client.call_count == 2
    assert len(quotes) == 2
    endpoints = [c.kwargs["endpoint"] for c in client.call_args_list]
    assert any("start_date=20240601&end_date=20240630" in e for e in endpoints)


def test_history_range_swaps_inverted_dates(mock_currency_history_api_response):
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = (
            mock_currency_history_api_response
        )
        api.get_history_quote_range(20240630, 20240601)

    assert (
        "start_date=20240601&end_date=20240630" in client.call_args.kwargs["endpoint"]
    )


def test_history_range_accepts_string_dates(mock_currency_history_api_response):
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = (
            mock_currency_history_api_response
        )
        api.get_history_quote_range("2024-06-01", "2024-06-30")

    assert "start_date=20240601" in client.call_args.kwargs["endpoint"]


def test_history_url_includes_record_limit(mock_currency_history_api_response):
    """The daily endpoint only returns a range when a limit segment is present."""
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = (
            mock_currency_history_api_response
        )
        api.get_history_quote_range("2024-06-01", "2024-06-30")

    endpoint = client.call_args.kwargs["endpoint"]
    assert "/daily/USD-BRL/30?" in endpoint


def test_long_range_is_split_into_windows(mock_currency_history_api_response):
    """Ranges beyond the source limit must be chunked, not silently truncated."""
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = (
            mock_currency_history_api_response
        )
        api.get_history_quote_range("2021-01-01", "2024-01-01")

    # ~1096 calendar days / 360-day windows
    assert client.call_count == 4


def test_duplicate_timestamps_are_removed(mock_currency_history_api_response):
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = (
            mock_currency_history_api_response * 3
        )
        quotes = api.get_history_quote_range("2024-06-01", "2024-06-30")

    assert len(quotes) == 1


def test_history_entries_inherit_metadata_from_first_entry(
    mock_currency_history_api_response,
):
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))
    first = mock_currency_history_api_response[0]
    second = {"bid": "5.2", "ask": "5.3", "timestamp": "1717710765"}

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = [first, second]
        quotes = api.get_history_quote_range("2024-06-01", "2024-06-30")

    assert len(quotes) == 2
    assert quotes[1].currency_pair_name == first["name"]
    assert quotes[1].base_currency_code == "USD"


def test_history_rejects_non_list_payload():
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))
    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = {"error": "unavailable"}
        with pytest.raises(QuoteFetchError, match="expected a list"):
            api.get_history_quote_range("2024-06-01", "2024-06-30")


def test_history_rejects_future_date():
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))
    with pytest.raises(InvalidDateError):
        api.get_history_quote(20991231)


def test_history_raises_when_source_returns_nothing():
    api = CurrencyAPI(CurrencyObject(["USD-BRL"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = []
        with pytest.raises(QuoteFetchError, match="No historical data"):
            api.get_history_quote(20240601)
