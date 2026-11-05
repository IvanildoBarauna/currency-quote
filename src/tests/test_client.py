# src/tests/test_client.py
"""Tests for the recommended high-level client (typed results & flexible dates)."""
from unittest.mock import patch
from datetime import date, datetime

import pytest

from currency_quote.client import CurrencyQuoteClient
from currency_quote.domain.entities.currency import CurrencyQuote, QuoteList
from currency_quote.exceptions import InvalidDateError


def make_quote(pair="USD-BRL", bid=5.0876, ask=5.0891, timestamp=1614024000):
    return CurrencyQuote(
        currency_pair=pair,
        currency_pair_name="Dólar Americano/Real Brasileiro",
        base_currency_code=pair.split("-")[0],
        quote_currency_code=pair.split("-")[1],
        quote_timestamp=timestamp,
        bid_price=bid,
        ask_price=ask,
    )


@patch("currency_quote.client.GetLastCurrencyQuoteUseCase.execute")
def test_get_last_accepts_single_pair(mock_execute):
    mock_execute.return_value = [make_quote()]
    quotes = CurrencyQuoteClient().get_last("USD-BRL")

    assert isinstance(quotes, QuoteList)
    assert len(quotes) == 1
    assert quotes[0].currency_pair == "USD-BRL"
    currency_obj = mock_execute.call_args.args[0]
    assert currency_obj.get_currency_list() == ["USD-BRL"]


@patch("currency_quote.client.GetLastCurrencyQuoteUseCase.execute")
def test_get_last_accepts_varargs_and_lists(mock_execute):
    mock_execute.return_value = []
    CurrencyQuoteClient().get_last("USD-BRL", "EUR-BRL")
    assert mock_execute.call_args.args[0].get_currency_list() == ["USD-BRL", "EUR-BRL"]

    mock_execute.reset_mock()
    CurrencyQuoteClient().get_last(["USD-BRL", ["EUR-BRL", "GBP-BRL"]])
    assert mock_execute.call_args.args[0].get_currency_list() == [
        "USD-BRL",
        "EUR-BRL",
        "GBP-BRL",
    ]


@patch("currency_quote.client.GetLastCurrencyQuoteUseCase.execute")
def test_get_last_validates_by_default_and_passes_http_config(mock_execute):
    mock_execute.return_value = []
    client = CurrencyQuoteClient(timeout_seconds=5, retry_attempts=7)
    client.get_last("USD-BRL")

    kwargs = mock_execute.call_args.kwargs
    assert kwargs["validate"] is True
    assert kwargs["http_config"].timeout_seconds == 5
    assert kwargs["http_config"].retry_attempts == 7


@patch("currency_quote.client.GetLastCurrencyQuoteUseCase.execute")
def test_get_last_can_skip_validation(mock_execute):
    mock_execute.return_value = []
    CurrencyQuoteClient(validate=False).get_last("USD-BRL")
    assert mock_execute.call_args.kwargs["validate"] is False


@patch("currency_quote.client.GetHistCurrencyQuoteUseCase.execute")
def test_get_history_accepts_flexible_single_dates(mock_execute):
    mock_execute.return_value = [make_quote()]
    quotes = CurrencyQuoteClient().get_history("USD-BRL", reference_date="2022-01-01")

    assert quotes[0].quote_timestamp == 1614024000
    assert mock_execute.call_args.args[0].get_currency_list() == ["USD-BRL"]
    assert mock_execute.call_args.args[1] == 20220101


@patch("currency_quote.client.GetHistCurrencyQuoteUseCase.execute")
def test_get_history_accepts_date_objects(mock_execute):
    mock_execute.return_value = []
    CurrencyQuoteClient().get_history("USD-BRL", reference_date=date(2022, 1, 1))
    assert mock_execute.call_args.args[1] == 20220101
    mock_execute.reset_mock()
    CurrencyQuoteClient().get_history("USD-BRL", reference_date=datetime(2022, 1, 1))
    assert mock_execute.call_args.args[1] == 20220101


@patch("currency_quote.client.GetHistCurrencyQuoteRangeUseCase.execute")
def test_get_history_range_defaults_end_to_start(mock_execute):
    mock_execute.return_value = [make_quote()]
    quotes = CurrencyQuoteClient().get_history("USD-BRL", start_date="2022-01-01")

    assert mock_execute.call_args.args[1] == 20220101
    assert mock_execute.call_args.args[2] == 20220101
    assert isinstance(quotes, QuoteList)


@patch("currency_quote.client.GetHistCurrencyQuoteRangeUseCase.execute")
def test_get_history_explicit_range(mock_execute):
    mock_execute.return_value = []
    client = CurrencyQuoteClient(validate=False)
    client.get_history("USD-BRL", start_date=20220101, end_date="2022-01-10")

    assert mock_execute.call_args.args[0].get_currency_list() == ["USD-BRL"]
    assert mock_execute.call_args.args[1] == 20220101
    assert mock_execute.call_args.args[2] == 20220110
    assert mock_execute.call_args.kwargs["validate"] is False


def test_get_history_rejects_conflicting_inputs():
    client = CurrencyQuoteClient()
    with pytest.raises(InvalidDateError, match="not both"):
        client.get_history("USD-BRL", reference_date=20220101, start_date=20220101)


def test_get_history_requires_a_date():
    client = CurrencyQuoteClient()
    with pytest.raises(InvalidDateError, match="reference_date or start_date"):
        client.get_history("USD-BRL")


def test_quote_list_dataframe_export():
    quotes = QuoteList([make_quote(), make_quote("EUR-BRL")])
    pandas = pytest.importorskip("pandas")
    frame = quotes.to_dataframe()
    assert isinstance(frame, pandas.DataFrame)
    assert len(frame) == 2
    assert frame["currency_pair"].tolist() == ["USD-BRL", "EUR-BRL"]
    assert frame["bid_price"].dtype == float


def test_single_quote_dataframe_export():
    pandas = pytest.importorskip("pandas")
    frame = make_quote().to_dataframe()
    assert isinstance(frame, pandas.DataFrame)
    assert len(frame) == 1
