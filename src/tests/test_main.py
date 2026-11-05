# src/tests/test_main.py
"""Tests for the command line interface."""
import json
from unittest.mock import patch

from currency_quote.__main__ import build_parser, main
from currency_quote.domain.entities.currency import CurrencyQuote, QuoteList
from currency_quote.exceptions import CurrencyAPIError


QUOTE = CurrencyQuote(
    currency_pair="USD-BRL",
    currency_pair_name="Dólar Americano/Real Brasileiro",
    base_currency_code="USD",
    quote_currency_code="BRL",
    quote_timestamp=1614024000,
    bid_price=5.0876,
    ask_price=5.0891,
)


def test_parser_defaults():
    args = build_parser().parse_args(["USD-BRL"])
    assert args.currencies == ["USD-BRL"]
    assert args.history is None
    assert args.start is None
    assert args.end is None
    assert args.no_validate is False


def test_parser_flags():
    args = build_parser().parse_args(
        [
            "USD-BRL",
            "EUR-BRL",
            "--start",
            "2022-01-01",
            "--end",
            "2022-02-01",
            "--no-validate",
        ]
    )
    assert args.currencies == ["USD-BRL", "EUR-BRL"]
    assert args.start == "2022-01-01"
    assert args.end == "2022-02-01"
    assert args.no_validate is True


@patch("currency_quote.__main__.CurrencyQuoteClient")
def test_main_last_quote_prints_json(mock_client_cls, capsys):
    mock_client_cls.return_value.get_last.return_value = QuoteList([QUOTE])
    exit_code = main(["USD-BRL"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["currency_pair"] == "USD-BRL"
    assert payload[0]["bid_price"] == 5.0876
    assert payload[0]["var_bid"] is None


@patch("currency_quote.__main__.CurrencyQuoteClient")
def test_main_history_flags(mock_client_cls):
    mock_client = mock_client_cls.return_value
    mock_client.get_history.return_value = QuoteList([QUOTE])

    assert main(["USD-BRL", "--history", "2022-01-01"]) == 0
    kwargs = mock_client.get_history.call_args.kwargs
    assert kwargs == {"reference_date": "2022-01-01"}

    assert main(["USD-BRL", "--start", "2022-01-01", "--end", "2022-02-01"]) == 0
    kwargs = mock_client.get_history.call_args.kwargs
    assert kwargs == {"start_date": "2022-01-01", "end_date": "2022-02-01"}


@patch("currency_quote.__main__.CurrencyQuoteClient")
def test_main_no_validate_flag(mock_client_cls):
    mock_client_cls.return_value.get_last.return_value = QuoteList([QUOTE])
    main(["USD-BRL", "--no-validate"])
    assert mock_client_cls.call_args.kwargs["validate"] is False


@patch("currency_quote.__main__.CurrencyQuoteClient")
def test_main_api_error_returns_exit_code_1(mock_client_cls, capsys):
    mock_client_cls.return_value.get_last.side_effect = CurrencyAPIError("offline")
    exit_code = main(["USD-BRL"])

    assert exit_code == 1
    assert "error: offline" in capsys.readouterr().err
